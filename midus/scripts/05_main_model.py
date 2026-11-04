# -*- coding: utf-8 -*-
"""主模型：基線校正 ANCOVA（分析計畫 §7.1、§7.1A、§7.1B）。

模型：`C3TCOMP ~ 便秘(定義B) + B3TCOMPZ1 + §5.5 全部共變項`
      家庭叢集（M2FAMNUM）穩健標準誤。

⚠️ 三個不可更動的設定：
  1. 不可用變化量當結果（均值回歸會反轉結論）。
  2. C3TCOMP／C3TEM／C3TEF 已以 M2 常模標準化，不可再重新標準化；
     基線必須配 B3TCOMPZ1／B3TEMZ1／B3TEFZ1。
  3. 完整案例僅供敏感度分析，**主要報告值見 06_multiple_imputation.py**。
"""
import _path  # noqa: F401
import pandas as pd

from midus_cognition import models
from midus_cognition.data import (COVARIATES, OUTCOMES, PRELIM_COVARIATES,
                                  PRELIM_RHS, build)
from midus_cognition.reporting import Report

OUTCOME_LABELS = {"C3TCOMP": "BTACT 綜合分數", "C3TEM": "情節記憶", "C3TEF": "執行功能"}

STEPS = [
    ("僅控制基線認知", None),
    ("＋ 年齡、性別、教育", "age + female + edu"),
    ("＋ BMI、慢性病數、憂鬱", "age + female + edu + bmi + chron27 + depre"),
    ("＋ 吸菸、飲酒、用藥（完整）",
     "C(smoke) + age + female + edu + bmi + chron27 + depre "
     "+ drinks + binge + alcprob + rxmed"),
]


def main():
    ds = build()
    sample = ds.analysis_sample("expo_b")
    rep = Report("main_model.md", "主模型：便秘與認知功能", "§7.1、§7.1A、§7.1B")
    rep.add(f"定義 B 可分析樣本 N = {len(sample)}，暴露 = {int(sample['expo_b'].sum())}", "")

    rep.heading("一、共變項缺失率（修正編碼後，§5.5A）")
    rep.table(pd.DataFrame([
        {"共變項": c, "缺失": int(sample[c].isna().sum()),
         "缺失率": f"{100 * sample[c].isna().mean():.1f}%"}
        for c in COVARIATES + ["smoke", "ampli"]
    ]))
    rep.add("", "吸菸三分類分布（0 = 從未規律、1 = 已戒、2 = 目前）："
            f"{sample['smoke'].value_counts(dropna=False).sort_index().to_dict()}")

    rep.heading("二、初步模型（僅基線、年齡、性別、教育）—— §7.1A")
    rep.estimates([
        models.ancova(sample, out, base, covariate_rhs=PRELIM_RHS,
                      required=PRELIM_COVARIATES, label=OUTCOME_LABELS[out])
        for out, base in OUTCOMES.items()
    ])
    rep.note("⚠️ 這是初步模型。納入 §5.5 全部共變項後效果約減半，"
             "引用時一律使用下節數值。")

    rep.heading("三、完整共變項模型（§5.5 全部納入）—— §7.1B")
    rep.estimates([
        models.ancova(sample, out, base, label=OUTCOME_LABELS[out])
        for out, base in OUTCOMES.items()
    ])

    rep.heading("四、逐步調整（固定同一完整案例樣本）")
    fixed = models.complete_cases(sample, "C3TCOMP", "B3TCOMPZ1", "expo_b")
    rep.estimates([
        models.ancova(fixed, "C3TCOMP", "B3TCOMPZ1", covariate_rhs=rhs, label=label)
        for label, rhs in STEPS
    ])
    rep.note(f"以上固定為同一完整案例樣本 N = {len(fixed)}，"
             "故差異純為共變項調整所致。衰減主要來自人口學與整體健康，"
             "吸菸／飲酒／用藥幾乎無額外貢獻。")
    rep.note("完整調整後效果量約為初步模型的六成，屬小且邊緣的效果；"
             "討論章節不可寫成強關聯。")
    rep.save()


if __name__ == "__main__":
    main()
