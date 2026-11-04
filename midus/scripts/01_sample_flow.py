# -*- coding: utf-8 -*-
"""樣本流程與組成（分析計畫 §4.4）。

輸出 sample_flow.md：從 M2P1 全部受訪者逐步篩到分析樣本的人數，
以及分析樣本的暴露分布、樣本來源與家庭叢集數。
"""
import _path  # noqa: F401
import pandas as pd

from midus_cognition import masking
from midus_cognition.data import build
from midus_cognition.reporting import Report

SAMPLE_LABELS = {1: "RDD 主樣本", 2: "手足", 3: "雙胞胎", 4: "都市加抽樣本"}


def main():
    ds = build()
    d = ds.frame
    rep = Report("sample_flow.md", "MIDUS 分析樣本流程", "§4.3、§4.4")

    two_wave = ds.two_wave
    steps = [
        ("M2P1 全部受訪者", ds.n_m2p1),
        ("且 M2 BTACT 綜合分數有效", int(d["B3TCOMPZ1"].notna().sum())),
        ("且 M3 BTACT 綜合分數有效", len(two_wave)),
        ("且 M2 便秘題有效（定義 A）", int(two_wave["expo_a"].notna().sum())),
        ("且 M2 或 M3 便秘題有效（定義 B，主分析）", int(two_wave["expo_b"].notna().sum())),
        ("且 兩波便秘題皆有效（定義 F／軌跡分析）", int(two_wave["expo_f"].notna().sum())),
    ]
    rep.heading("一、篩選步驟")
    rep.table(pd.DataFrame([{"步驟": s, "人數": masking.fmt(n)} for s, n in steps]))

    sample = ds.analysis_sample("expo_b")
    rep.heading("二、分析樣本組成（定義 B）")
    counts = {"便秘：是": int((sample["expo_b"] == 1).sum()),
              "便秘：否": int((sample["expo_b"] == 0).sum())}
    counts.update({f"樣本來源：{name}": int((sample["SAMPLMAJ"] == code).sum())
                   for code, name in SAMPLE_LABELS.items()})
    rep.table(pd.DataFrame([{"類別": k, "人數": v} for k, v in masking.dist(counts).items()]))
    rep.add(f"- 家庭叢集數（M2FAMNUM）：{sample['M2FAMNUM'].nunique()}")

    rep.heading("三、排除條件的影響（§4.3，僅呈現人數，主分析不排除）")
    rep.table(pd.DataFrame([
        {"條件": "自陳中風／帕金森氏症／其他神經疾病",
         "人數": masking.fmt(int((sample["neuro"] == 1).sum()))},
        {"條件": "BTACT 任一分測驗被標為施測有問題",
         "人數": masking.fmt(int((sample["anyfp"] == 1).sum()))},
        {"條件": "兩者皆排除後剩餘",
         "人數": masking.fmt(int(((sample["neuro"] == 0) & (sample["anyfp"] == 0)).sum()))},
    ]))
    rep.note("MIDUS 2 問卷無「以上皆無」選項，未勾選視為「否」，"
             "故「否」可能混有漏答者（§8 敏感度分析第 3 項）。")
    rep.save()


if __name__ == "__main__":
    main()
