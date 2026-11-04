# -*- coding: utf-8 -*-
"""建構分析資料集（對應分析計畫 §4、§5）。

本模組是**唯一**的資料建構入口。所有分析腳本都呼叫 :func:`build`，
避免各腳本各自清理資料而產生不一致的設定。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

import numpy as np
import pandas as pd
import pyreadstat

from . import config
from .codes import drop_weight_inapp, na, yes

# ---------------------------------------------------------------- 變項清單

#: §5.2 結果與基線。C3TCOMP／C3TEM／C3TEF 已以 MIDUS 2 全國常模標準化，
#: 故基線必須配 Z1 版本（B3TCOMPZ1／B3TEMZ1／B3TEFZ1），**不可再重新標準化**。
OUTCOMES = {
    "C3TCOMP": "B3TCOMPZ1",  # BTACT 綜合分數
    "C3TEM": "B3TEMZ1",      # 情節記憶（注意：B3TEM 不存在，正確為 B3TEMZ1）
    "C3TEF": "B3TEFZ1",      # 執行功能（注意：B3TEF 不存在，正確為 B3TEFZ1）
}

#: BTACT 分測驗「施測有問題」旗標（§4.3 排除條件、§8A 敏感度分析）
BTACT_FLAGS = ["B3TWLIFP", "B3TDBFP", "B3TCTFFP", "B3TNSFP", "B3TBKFP", "B3TWLDFP"]

#: §7.1A 初步模型的共變項（僅基線、年齡、性別、教育）
PRELIM_COVARIATES = ["age_m2", "female", "edu"]
PRELIM_RHS = "age_m2 + female + edu"

#: §5.5 共變項（吸菸以 C(smoke) 三分類另外進入模型）
COVARIATES = [
    "age", "female", "edu", "bmi", "chron27", "depre",
    "drinks", "binge", "alcprob", "rxmed",
]

#: 模型右側的共變項字串（含吸菸三分類）
COVARIATE_RHS = (
    "C(smoke) + age + female + edu + bmi + chron27 + depre "
    "+ drinks + binge + alcprob + rxmed"
)

#: 建模時必須非遺漏的共變項（完整案例用）
MODEL_COVARIATES = COVARIATES + ["smoke"]

_M2P1_VARS = [
    "M2ID", "M2FAMNUM", "SAMPLMAJ",
    "B1SA11K", "B1SA11CC", "B1SA11I", "B1SCHRON",
    "B1PRAGE_2019", "B1PAGE_M2", "B1PRSEX", "B1PB1",
    "B1SBMI", "B1PDEPRE",
    "B1PA37", "B1PA38A", "B1PA39", "B1PA50", "B1PA52", "B1PA53",
    "B1SALCOH", "B1SRXMED", "B1SAMPLI",
    "B1PA6A", "B1PA6C", "B1PA6D",
    "B1PWGHT1", "B1PWGHT10",
]
_M3P1_VARS = ["M2ID", "C1SA11K", "C1SA11CC", "C1SA11I", "C1PRAGE", "C1PWGHT1", "C1PWGHT10"]
_M2P3_VARS = ["M2ID"] + list(OUTCOMES.values()) + BTACT_FLAGS
_M3P3_VARS = ["M2ID"] + list(OUTCOMES)


@dataclass
class Dataset:
    """建構完成的分析資料集。"""

    frame: pd.DataFrame
    chronic_items: list = field(default_factory=list)
    n_m2p1: int = 0

    # -- 常用子集 ------------------------------------------------------
    @property
    def two_wave(self) -> pd.DataFrame:
        """兩波 BTACT 綜合分數皆有效者（§4.4）。"""
        f = self.frame
        return f[f["B3TCOMPZ1"].notna() & f["C3TCOMP"].notna()]

    def analysis_sample(self, exposure: str = "expo_b") -> pd.DataFrame:
        """主分析樣本：兩波 BTACT 有效，且指定暴露定義可分析。"""
        d = self.two_wave
        return d[d[exposure].notna()].copy()


def _chronic_items(path) -> list:
    """M2 的 30 題慢性病清單 B1SA11A–B1SA11DD（只讀 metadata，不載入資料列）。"""
    _, meta = pyreadstat.read_sav(str(path), metadataonly=True)
    return [c for c in meta.column_names if re.fullmatch(r"B1SA11[A-Z]{1,2}", c)]


def _read(key: str, usecols: list) -> pd.DataFrame:
    df, _ = pyreadstat.read_sav(str(config.path(key)), usecols=usecols, user_missing=True)
    return df


@lru_cache(maxsize=1)
def build() -> Dataset:
    """載入四個核心資料檔，合併並建構暴露、結果與共變項。

    結果會被快取，同一個 Python 行程內重複呼叫不會重讀 `.sav`。
    """
    m2p1_path = config.path("M2P1")
    chronic = _chronic_items(m2p1_path)
    # 慢性病數須扣除便秘、胃部不適、痔瘡三題，避免與暴露共線（§5.5A 第 1 點）
    keep27 = [c for c in chronic if c not in ("B1SA11K", "B1SA11I", "B1SA11CC")]

    m2p1 = _read("M2P1", sorted(set(_M2P1_VARS + chronic)))
    m3p1 = _read("M3P1", _M3P1_VARS)
    m2p3 = _read("M2P3", _M2P3_VARS)
    m3p3 = _read("M3P3", _M3P3_VARS)

    d = (m2p1
         .merge(m2p3, on="M2ID", how="left")
         .merge(m3p3, on="M2ID", how="left")
         .merge(m3p1, on="M2ID", how="left"))

    # ---- 結果與基線：BTACT 的 8／9 為缺失碼 ----
    for col in list(OUTCOMES) + list(OUTCOMES.values()):
        d[col] = na(d[col], [8, 9])

    # ---- 暴露（§5.1、§5.1B）----
    for col in ["B1SA11K", "B1SA11CC", "B1SA11I", "C1SA11K", "C1SA11CC", "C1SA11I"]:
        d[col] = na(d[col], [-1, 7, 8, 9])

    k2, k3 = d["B1SA11K"], d["C1SA11K"]
    # 定義 A：僅 MIDUS 2 單波便秘（暴露完全先於結果）
    d["expo_a"] = np.where(k2.notna(), yes(k2).astype(float), np.nan)
    # 定義 B：任一波便秘 —— **主要暴露**（§5.1B，先驗選定，非依 p 值挑選）
    d["expo_b"] = np.where(k2.isna() & k3.isna(), np.nan,
                           (yes(k2) | yes(k3)).astype(float))
    # 定義 C：便秘或痔瘡
    d["expo_c"] = np.where(k2.isna() & d["B1SA11CC"].isna(), np.nan,
                           (yes(k2) | yes(d["B1SA11CC"])).astype(float))
    # 定義 D：M2 三症狀任一（便秘／痔瘡／胃部不適）
    m2_items = d[["B1SA11K", "B1SA11CC", "B1SA11I"]]
    d["expo_d"] = np.where(m2_items.notna().any(axis=1),
                           (m2_items == 1).any(axis=1).astype(float), np.nan)
    # 定義 F：兩波皆便秘（持續型）
    d["expo_f"] = np.where(k2.isna() | k3.isna(), np.nan,
                           (yes(k2) & yes(k3)).astype(float))
    # 症狀個數（序數暴露）
    d["nsym"] = np.where(m2_items.notna().all(axis=1), (m2_items == 1).sum(axis=1), np.nan)

    # ---- 便秘軌跡四分組（§7.2）----
    both = k2.notna() & k3.notna()
    cond = [yes(k2) & yes(k3), yes(k2) & ~yes(k3), ~yes(k2) & yes(k3)]
    d["traj"] = np.where(both, np.select(cond, ["persist", "m2only", "m3only"], "never"), None)

    # ---- 共變項（§5.5、§5.5A）----
    d["age"] = na(d["B1PRAGE_2019"], [97, 98])      # 修訂版年齡，完整共變項模型用
    d["age_m2"] = na(d["B1PAGE_M2"], [97, 98])      # M2 原始年齡，初步模型（§7.1A）用
    d["female"] = (d["B1PRSEX"] == 2).astype(float)
    d["edu"] = na(d["B1PB1"], [97, 98])
    d["bmi"] = na(d["B1SBMI"], [-1, 98])

    # 慢性病數：27 題版本（已驗證 B1SCHRON 等於 30 題答「是」的題數）
    k27 = d[keep27].apply(lambda s: na(s, [-1, 7, 8, 9]))
    d["chron27"] = (k27 == 1).sum(axis=1).where(~k27.isna().all(axis=1))

    d["depre"] = na(d["B1PDEPRE"], [97, 98])

    # 吸菸三分類：B1PA37 = 96（從未抽過菸）是有效資訊，不可當缺失（§5.5A 第 2 點）
    d["smoke"] = np.nan
    d.loc[(d["B1PA37"] == 96) | (d["B1PA38A"] == 2), "smoke"] = 0.0  # 從未規律吸菸
    d.loc[(d["B1PA38A"] == 1) & (d["B1PA39"] == 2), "smoke"] = 1.0   # 曾吸菸已戒
    d.loc[d["B1PA39"] == 1, "smoke"] = 2.0                           # 目前吸菸

    # 飲酒：未飲酒者（含 B1PA50 = 9 從未飲酒）補 0，否則缺失率達 43%（§5.5A 第 3 點）
    nondrink = d["B1PA50"].isin([2, 9])
    d["drinks"] = np.where(nondrink, 0.0, na(d["B1PA52"], [97, 98, 99]))
    d["binge"] = np.where(nondrink, 0.0, na(d["B1PA53"], [97, 98, 99]))
    d.loc[d["B1PA50"] == 8, ["drinks", "binge"]] = np.nan  # 拒答者仍為缺失

    d["alcprob"] = na(d["B1SALCOH"], [-1, 8])
    d["rxmed"] = na(d["B1SRXMED"], [-1, 98])
    d["ampli"] = na(d["B1SAMPLI"], [-1, 8])  # 症狀放大傾向（α = .53，僅敏感度分析）

    # ---- 排除條件旗標（§4.3）----
    for col in ["B1PA6A", "B1PA6C", "B1PA6D"]:
        d[col] = na(d[col], [7, 8, 9])
    d["neuro"] = ((d["B1PA6A"] == 1) | (d["B1PA6C"] == 1) | (d["B1PA6D"] == 1)).astype(float)
    d["anyfp"] = (d[BTACT_FLAGS] == 1).any(axis=1).astype(float)

    # ---- 事後分層權重：99 = 不適用，必須先設為缺失（§8B）----
    for col in ["B1PWGHT1", "B1PWGHT10", "C1PWGHT1", "C1PWGHT10"]:
        d[col] = drop_weight_inapp(d[col])

    return Dataset(frame=d, chronic_items=chronic, n_m2p1=len(m2p1))
