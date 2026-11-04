# -*- coding: utf-8 -*-
"""痔瘡 × 便秘交叉分析（分析計畫 §5.1A、§8 敏感度 8）—— 描述性，不做因果推論。

目的：檢驗痔瘡能否作為便秘的補充指標。
結論（實測）：有便秘者中約四分之一有痔瘡，但**有痔瘡者中僅約一成有便秘**，
與 Peery 2015 的 12% 吻合 → 痔瘡無代理價值，複合暴露會造成暴露錯分。
"""
import _path  # noqa: F401
import pandas as pd

from midus_cognition import masking
from midus_cognition.codes import binary, na
from midus_cognition.data import build
from midus_cognition.reporting import Report

ITEMS = {"con": ("B1SA11K", "C1SA11K"), "hem": ("B1SA11CC", "C1SA11CC"),
         "gas": ("B1SA11I", "C1SA11I")}


def main():
    ds = build()
    d = ds.frame.copy()
    for stem, (m2_var, m3_var) in ITEMS.items():
        d[f"{stem}_m2"] = binary(d[m2_var])
        d[f"{stem}_m3"] = binary(d[m3_var])
    d["age_m2_raw"] = na(d["B1PAGE_M2"], [98, 99])
    analysis_ids = set(ds.analysis_sample("expo_b")["M2ID"])
    d["in_analysis"] = d["M2ID"].isin(analysis_ids)

    rep = Report("hemorrhoid_constipation.md", "痔瘡 × 便秘交叉分析", "§5.1A")
    rep.note("母體 A＝分析樣本（兩波 BTACT 有效且定義 B 可分析）；"
             "母體 B＝該波問卷中兩項皆有效者。")
    rep.note("MIDUS 2 問卷沒有「以上皆無」選項，未勾選視為「否」，"
             "「否」可能混有漏答者；M3 起有該選項。")

    populations = [("母體 A（分析樣本）", d[d["in_analysis"]]), ("母體 B（全部有效者）", d)]

    rep.heading("一、MIDUS 2：痔瘡 × 便秘")
    for name, frame in populations:
        rep.add(*masking.crosstab_2x2(frame, "hem_m2", "con_m2", "痔瘡", "便秘",
                                      f"M2，{name}"))

    rep.heading("二、MIDUS 3：痔瘡 × 便秘")
    for name, frame in populations:
        rep.add(*masking.crosstab_2x2(frame, "hem_m3", "con_m3", "痔瘡", "便秘",
                                      f"M3，{name}"))

    rep.heading("三、M2 → M3 便秘變化")
    for name, frame in populations:
        pair = frame[["con_m2", "con_m3"]].dropna()
        counts = {
            "持續有": int(((pair.con_m2 == 1) & (pair.con_m3 == 1)).sum()),
            "新發": int(((pair.con_m2 == 0) & (pair.con_m3 == 1)).sum()),
            "緩解": int(((pair.con_m2 == 1) & (pair.con_m3 == 0)).sum()),
            "持續無": int(((pair.con_m2 == 0) & (pair.con_m3 == 0)).sum()),
        }
        rep.add(f"**{name}**（兩波皆有效 {masking.fmt(len(pair))} 人）")
        rep.table(pd.DataFrame([{"類別": k, "人數": v}
                                for k, v in masking.dist(counts).items()]))

    rep.heading("四、腸胃症狀計數")
    for name, frame in populations:
        rep.add(*masking.count_distribution(frame, ["con_m2", "gas_m2", "hem_m2"],
                                            ["便秘", "胃部不適", "痔瘡"],
                                            f"M2 三項計數（0–3），{name}"))

    rep.heading("五、M2 痔瘡盛行率依年齡層")
    for name, frame in populations:
        pair = frame[["hem_m2", "age_m2_raw"]].dropna()
        rows = []
        for low, high, label in [(0, 54, "<55 歲"), (55, 64, "55–64 歲"), (65, 200, "≥65 歲")]:
            group = pair[(pair.age_m2_raw >= low) & (pair.age_m2_raw <= high)]
            n, cases = len(group), int((group.hem_m2 == 1).sum())
            if masking.small(n) or masking.small(cases) or masking.small(n - cases):
                rows.append({"年齡層": label, "有效人數": masking.fmt(n),
                             "痔瘡：是": masking.MASK, "盛行率": masking.MASK})
            else:
                rows.append({"年齡層": label, "有效人數": n, "痔瘡：是": cases,
                             "盛行率": masking.pct(cases, n)})
        rep.add(f"**{name}**")
        rep.table(pd.DataFrame(rows))

    rep.note("痔瘡對便秘的陽性預測值低，不宜作為便秘的補充指標；"
             "複合暴露（定義 C／D）病例雖多但效果被稀釋，即此之故。")
    rep.save()


if __name__ == "__main__":
    main()
