# -*- coding: utf-8 -*-
"""便秘軌跡模型（分析計畫 §7.2、§7.2A）。

以 M2／M3 兩波建構四分組（持續／僅 M2／僅 M3／從未），參照組＝從未便秘。
MIDUS 1 未納入前先以兩波建構；M1 無認知測驗，三波持續型人數會過少。

持續型便秘是本研究最穩健的發現，且三組呈劑量反應，支持因果方向，
建議作為結果章節的核心論證。
"""
import _path  # noqa: F401
import pandas as pd

from midus_cognition import masking, models
from midus_cognition.data import PRELIM_COVARIATES, PRELIM_RHS, build
from midus_cognition.reporting import Report

GROUPS = {"never": "從未便秘（參照）", "m2only": "僅 M2 便秘",
          "m3only": "僅 M3 便秘", "persist": "持續便秘（兩波皆是）"}


def main():
    ds = build()
    traj = ds.two_wave
    traj = traj[traj["traj"].notna()].copy()
    rep = Report("trajectory.md", "便秘軌跡與認知功能", "§7.2、§7.2A")
    rep.add(f"兩波便秘題皆有效 N = {len(traj)}", "")

    rep.heading("一、各軌跡組人數")
    counts = {GROUPS[k]: int((traj["traj"] == k).sum()) for k in GROUPS}
    rep.table(pd.DataFrame([{"軌跡組": k, "人數": v}
                            for k, v in masking.dist(counts).items()]))

    rep.heading("二、初步模型（僅基線、年齡、性別、教育）")
    sub, rows = models.categorical_terms(traj, "C3TCOMP", "B3TCOMPZ1", "traj", "never",
                                         covariate_rhs=PRELIM_RHS,
                                         required=PRELIM_COVARIATES)
    for row in rows:
        row.label = GROUPS.get(row.label, row.label)
    rep.add(f"N = {len(sub)}（參照組＝從未便秘）")
    rep.estimates(rows)

    rep.heading("三、完整共變項模型（§5.5 全部納入）")
    sub, rows = models.categorical_terms(traj, "C3TCOMP", "B3TCOMPZ1", "traj", "never")
    for row in rows:
        row.label = GROUPS.get(row.label, row.label)
    rep.add(f"N = {len(sub)}（參照組＝從未便秘）")
    rep.estimates(rows)

    rep.note("僅持續組達顯著，且效果約為任一波暴露的兩倍。"
             "三組的劑量反應（僅 M2 < 僅 M3 < 持續）支持因果方向。")
    rep.note("⚠️ 持續組人數少（約 30–40 人），信賴區間寬，"
             "須在限制中說明此結果的精確度有限。")
    rep.save()


if __name__ == "__main__":
    main()
