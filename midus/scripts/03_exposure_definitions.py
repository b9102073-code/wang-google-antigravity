# -*- coding: utf-8 -*-
"""暴露定義比較（分析計畫 §5.1、§5.1B）。

比較定義 A–F 的可分析人數、病例數與初步模型效果，說明為何採定義 B。

⚠️ 定義 B 是**先驗選定**（Rome 準則下便秘為間斷復發症狀，單次橫斷問卷
會錯分），不是依 p 值挑選。本表的作用是呈現複合暴露（C／D）為何失敗
——病例變多但效果被稀釋，因為痔瘡與胃部不適不等於便秘。
"""
import _path  # noqa: F401
import pandas as pd

from midus_cognition import models
from midus_cognition.data import PRELIM_COVARIATES, PRELIM_RHS, build
from midus_cognition.reporting import Report

DEFINITIONS = [
    ("A. 僅 M2 便秘（單波）", "expo_a"),
    ("B. 任一波便秘（主要暴露）", "expo_b"),
    ("C. 便秘或痔瘡", "expo_c"),
    ("D. M2 三症狀任一", "expo_d"),
    ("F. 兩波皆便秘（持續型）", "expo_f"),
]


def main():
    ds = build()
    two_wave = ds.two_wave
    rep = Report("exposure_definitions.md", "暴露定義比較", "§5.1、§5.1B、§8 敏感度 4")

    rep.heading("一、各定義的可分析人數與盛行率")
    rows = []
    for label, col in DEFINITIONS:
        sub = two_wave[two_wave[col].notna()]
        n, cases = len(sub), int(sub[col].sum())
        rows.append({"定義": label, "可分析 N": n, "病例": cases,
                     "盛行率": f"{100 * cases / n:.1f}%"})
    rep.table(pd.DataFrame(rows))

    rep.heading("二、初步模型效果（僅控制基線、年齡、性別、教育）")
    estimates = [
        models.ancova(two_wave, "C3TCOMP", "B3TCOMPZ1", exposure=col,
                      covariate_rhs=PRELIM_RHS, required=PRELIM_COVARIATES, label=label)
        for label, col in DEFINITIONS
    ]
    rep.estimates(estimates)

    rep.heading("三、檢定力：各定義的最小可偵測效果量")
    rep.table(pd.DataFrame([
        {"定義": e.label, "N": e.n, "病例": e.n_exposed,
         "最小可偵測 β (SD)": round(models.mde(e.n, e.n_exposed), 3)}
        for e in estimates
    ]))
    rep.note("α = .05 雙尾、power = .80、殘差 SD ≈ 0.60 的常態近似。")

    rep.heading("四、序數暴露：M2 腸胃症狀個數")
    sub = two_wave[two_wave["nsym"].notna()]
    rep.add(f"症狀個數有效者 N = {len(sub)}")
    rep.estimates([models.ancova(sub, "C3TCOMP", "B3TCOMPZ1", exposure="nsym",
                                 covariate_rhs=PRELIM_RHS, required=PRELIM_COVARIATES,
                                 label="症狀個數（0–3，每增一項）")])
    rep.note("⚠️ 不可改以變化量 C3TCOMP − B3TCOMPZ1 作為結果：均值回歸會讓"
             "症狀愈多者「衰退愈少」，方向與基線校正模型完全相反（§7.1）。")
    rep.save()


if __name__ == "__main__":
    main()
