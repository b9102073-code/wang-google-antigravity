# -*- coding: utf-8 -*-
"""敏感度分析（分析計畫 §8、§8A）。

三個必須據實呈現、不可隱藏的結果：
  1. 控制症狀放大傾向 B1SAMPLI 後 p 剛好跨過 .05 門檻。自陳便秘與認知
     可能共享「症狀回報傾向」的共同方法變異，審稿人極可能要求此調整。
     可平衡之處：該量表 α 僅 .53，過度調整也可能造成低估。
  2. 僅用 RDD 主樣本時不顯著（效果量幾乎相同，是檢定力問題），
     意味著結論有相當部分倚賴雙胞胎與手足樣本。
  3. 定義 F（持續型便秘）是最穩健的結果。
"""
import _path  # noqa: F401
from midus_cognition import models
from midus_cognition.data import build
from midus_cognition.reporting import Report


def main():
    ds = build()
    sample = ds.analysis_sample("expo_b")
    rep = Report("sensitivity.md", "敏感度分析", "§8、§8A")
    rep.add("結果變項 C3TCOMP，完整共變項模型，家庭叢集穩健標準誤。", "")

    rows = [models.ancova(sample, "C3TCOMP", "B3TCOMPZ1", label="主模型（完整案例）")]
    mi, _ = models.multiple_imputation(sample, "C3TCOMP", "B3TCOMPZ1")
    rows.append(mi)

    rep.heading("一、模型設定與樣本限制")
    rows += [
        models.ancova(sample, "C3TCOMP", "B3TCOMPZ1", extra_rhs="ampli",
                      label="＋ 控制症狀放大 B1SAMPLI"),
        models.ancova(sample[sample["neuro"] == 0], "C3TCOMP", "B3TCOMPZ1",
                      label="排除神經疾病者"),
        models.ancova(sample[(sample["neuro"] == 0) & (sample["anyfp"] == 0)],
                      "C3TCOMP", "B3TCOMPZ1", label="再排除 BTACT 問題旗標"),
        models.ancova(sample[sample["SAMPLMAJ"] != 4], "C3TCOMP", "B3TCOMPZ1",
                      label="排除都市加抽樣本"),
        models.ancova(sample[sample["SAMPLMAJ"] == 1], "C3TCOMP", "B3TCOMPZ1",
                      label="僅 RDD 主樣本"),
    ]

    rep.heading("二、替代暴露定義")
    two_wave = ds.two_wave
    rows += [
        models.ancova(two_wave[two_wave["expo_a"].notna()], "C3TCOMP", "B3TCOMPZ1",
                      exposure="expo_a", label="定義 A（僅 M2 單波）"),
        models.ancova(two_wave[two_wave["expo_f"].notna()], "C3TCOMP", "B3TCOMPZ1",
                      exposure="expo_f", label="定義 F（兩波皆便秘）"),
    ]
    rep.estimates(rows)

    rep.note("控制 B1SAMPLI 後 p 跨越 .05 門檻，必須主動呈現，不可隱藏；"
             "可在討論中說明該量表 α 僅 .53，過度調整亦可能低估效果。")
    rep.note("僅 RDD 主樣本時不顯著，但效果量與全樣本幾乎相同，"
             "主因是樣本與暴露人數縮減造成的檢定力不足。"
             "須在限制中說明結論有相當部分倚賴雙胞胎與手足樣本。")
    rep.note("定義 F（持續型）效果約為任一波暴露的兩倍，是最穩健的結果，"
             "建議作為結果章節的核心論證。")
    rep.save()


if __name__ == "__main__":
    main()
