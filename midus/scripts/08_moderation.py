# -*- coding: utf-8 -*-
"""調節分析（分析計畫 §7.3、§7.3A）—— 結果為陰性，據實報告。

便秘 × 年齡、便秘 × 性別交互作用。實測兩者皆完全無效果且趨近於零，
並非檢定力不足所致的邊緣結果。

⚠️ 這對論文架構有實質影響：§5.3 與研究問題中「以年齡調節檢驗老化角色」
的設定未獲資料支持。建議（a）改列為陰性發現；（b）老化改以 M2→M3 認知
變化速度操作；（c）優先與指導教授討論（§11 第 4 項）。

與同資料庫既有觀察一致：Karlamangla 2014（Neurobiol Aging,
doi:10.1016/j.neurobiolaging.2013.07.028）以 MIDUS 證明發炎與情節記憶的
負相關亦不隨年齡而異。
"""
import _path  # noqa: F401
from midus_cognition import models
from midus_cognition.data import build
from midus_cognition.reporting import Report


def main():
    ds = build()
    sample = ds.analysis_sample("expo_b")
    rep = Report("moderation.md", "調節分析（年齡、性別）", "§7.3、§7.3A")

    rep.heading("交互作用項（完整共變項模型）")
    rep.estimates([
        models.interaction(sample, "C3TCOMP", "B3TCOMPZ1", "age", label="便秘 × 年齡"),
        models.interaction(sample, "C3TCOMP", "B3TCOMPZ1", "female", label="便秘 × 性別"),
    ])
    rep.note("兩者皆無顯著交互作用，效果量趨近於零。"
             "便秘與認知的關聯在中年與老年族群間並無差異。")
    rep.note("建議作為陰性發現據實報告，並把「老化」的操作方式"
             "改以認知變化速度為主（§5.3 次要路徑）。")
    rep.save()


if __name__ == "__main__":
    main()
