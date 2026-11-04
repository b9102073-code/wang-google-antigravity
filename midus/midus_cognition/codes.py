# -*- coding: utf-8 -*-
"""MIDUS 缺失碼處理（對應分析計畫 §6、§5.5A 第 4 點）。

MIDUS 的缺失碼慣例：
    -1          未完成自填問卷（SAQ）
    7 / 97      不知道
    8 / 98      拒答，或無法計算
    9 / 99      不適用（跳答 Inapp）

⚠️ 一律以 ``user_missing=True`` 讀取原始碼後逐一判斷，不可讓 pyreadstat
自動套用 SPSS 的使用者缺失定義。否則：
  * `B1PA37 = 96`（從未抽過菸）這類**有效資訊**會被當成缺失，
    使 1,270 名從未吸菸者消失（§5.5A 第 2 點）；
  * 權重變項的 `99`（不適用）會被當成數值 99，
    使 2,706 人獲得 99 倍權重而結果完全失真（§8B）。
"""
from __future__ import annotations

import pandas as pd

#: 二元症狀題（1 = 是，2 = 否）的缺失碼
BINARY_MISSING = [-1, 7, 8, 9]


def na(s: pd.Series, codes) -> pd.Series:
    """把 ``codes`` 列出的值設為遺漏。"""
    return s.where(~s.isin(codes))


def yes(s: pd.Series) -> pd.Series:
    """症狀題「是」= 1。回傳布林（遺漏視為 False，呼叫端須自行處理可分析性）。"""
    return s == 1


def binary(s: pd.Series) -> pd.Series:
    """症狀題轉 1/0；-1、7、8、9 轉遺漏。"""
    cleaned = na(s, BINARY_MISSING)
    return cleaned.map({1: 1.0, 2: 0.0})


def drop_weight_inapp(s: pd.Series) -> pd.Series:
    """事後分層權重：99 = 不適用（非 RDD 主樣本），必須先設為缺失。"""
    return s.where(s != 99)
