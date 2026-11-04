# -*- coding: utf-8 -*-
"""加權敏感度分析（分析計畫 §8B）。

⚠️ 權重變項的 `99` 是「不適用」代碼（非 RDD 主樣本一律為 99），
讀取時必須先設為缺失，否則 2,706 人會被當成 99 倍權重而結果完全失真。
本套件在 data.build() 已統一處理（codes.drop_weight_inapp）。

結論：主分析維持全樣本未加權 ＋ M2FAMNUM 叢集穩健標準誤。
  - 有利證據：以 **M2** 權重（對應暴露測量的波次）加權後點估計幾乎不變
    → 關聯並非來自樣本在地區、年齡、教育、性別、種族上的組成偏差。
  - 須據實列為限制：以 **M3** 權重加權則衰減且對設定敏感；已確認非極端
    權重所致（截尾後仍相近），推測 M3 權重同時反映追蹤流失的組成差異。
"""
import _path  # noqa: F401
import pandas as pd

from midus_cognition import models
from midus_cognition.data import build
from midus_cognition.reporting import Report

WEIGHTS = [
    ("B1PWGHT1", "加權 B1PWGHT1（M2）"),
    ("B1PWGHT10", "加權 B1PWGHT10（M2，四因子）"),
    ("C1PWGHT1", "加權 C1PWGHT1（M3）"),
    ("C1PWGHT10", "加權 C1PWGHT10（M3，四因子）"),
]


def main():
    ds = build()
    sample = ds.analysis_sample("expo_b")
    rdd = sample[sample["SAMPLMAJ"] == 1].copy()
    rep = Report("weighted.md", "加權敏感度分析", "§8B")

    rep.heading("一、權重的可用範圍（99 已設為缺失）")
    rep.table(pd.DataFrame([
        {"權重": col, "全分析樣本中有效": int(sample[col].notna().sum()),
         "RDD 子樣本中有效": int(rdd[col].notna().sum())}
        for col, _ in WEIGHTS
    ]))
    rep.add("", f"RDD 主樣本（定義 B）N = {len(rdd)}，暴露 = {int(rdd['expo_b'].sum())}",
            f"RDD 家庭叢集數 = {rdd['M2FAMNUM'].nunique()}（RDD 樣本幾乎無親屬配對）")
    rep.note("事後分層權重僅涵蓋 RDD 主樣本，加權會損失全部家族樣本，"
             "故不適合作為主分析。")

    rep.heading("二、未加權 vs 加權（完整共變項）")
    rows = [
        models.ancova(sample, "C3TCOMP", "B3TCOMPZ1", label="全樣本未加權（主模型）"),
        models.ancova(rdd, "C3TCOMP", "B3TCOMPZ1", label="RDD 未加權"),
    ]
    rows += [models.ancova(rdd, "C3TCOMP", "B3TCOMPZ1", weights=col, label=label)
             for col, label in WEIGHTS]
    rep.estimates(rows)

    rep.heading("三、M3 權重的衰減是否由極端權重造成")
    diag = models.complete_cases(rdd, "C3TCOMP", "B3TCOMPZ1", "expo_b", extra=["C1PWGHT1"])
    rep.add(f"C1PWGHT1 分布（N = {len(diag)}）："
            f"{diag['C1PWGHT1'].describe([.5, .9, .95, .99]).round(3).to_dict()}")
    rep.add(f"暴露組權重平均 {diag.loc[diag.expo_b == 1, 'C1PWGHT1'].mean():.3f}"
            f" vs 未暴露 {diag.loc[diag.expo_b == 0, 'C1PWGHT1'].mean():.3f}")
    rows = [models.ancova(diag, "C3TCOMP", "B3TCOMPZ1", weights="C1PWGHT1",
                          label="原始 C1PWGHT1")]
    for q in (0.99, 0.95):
        capped = diag.copy()
        cap = capped["C1PWGHT1"].quantile(q)
        capped["w"] = capped["C1PWGHT1"].clip(upper=cap)
        rows.append(models.ancova(capped, "C3TCOMP", "B3TCOMPZ1", weights="w",
                                  label=f"截尾於 p{int(q * 100)}（上限 {cap:.2f}）"))
    capped = diag.copy()
    capped["w"] = capped["C1PWGHT1"].clip(upper=3.0)
    rows.append(models.ancova(capped, "C3TCOMP", "B3TCOMPZ1", weights="w",
                              label="截尾於 3.0"))
    rep.estimates(rows)
    rep.note("截尾後估計值仍相近，衰減是真實的再加權效果，不是少數離群值。")

    rep.heading("四、加權 ＋ 多重插補（RDD，C1PWGHT1）")
    mi, _ = models.multiple_imputation(rdd, "C3TCOMP", "B3TCOMPZ1", weights="C1PWGHT1",
                                       label="加權 C1PWGHT1 ＋ 插補 (M=%d)")
    rep.estimates([mi])

    rep.note("建議的加權策略：主分析維持全樣本未加權 ＋ 叢集穩健標準誤；"
             "加權分析（M2 與 M3 權重各一）列為敏感度分析，兩者結果都要呈現，"
             "包含 M3 權重下的衰減；並明確說明推論對象為「樣本族群」"
             "而非「美國成人母體」。")
    rep.save()


if __name__ == "__main__":
    main()
