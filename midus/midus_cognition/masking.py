# -*- coding: utf-8 -*-
"""小格遮蔽（n < 10）。

分析在本機執行，只輸出彙總結果；受試者層級資料不離開本機（§9）。
任何人數格子低於 :data:`config.MIN_CELL` 一律遮蔽，並處理「由合計反推」
的風險：若一維分布只有一格被遮，再遮次小的一格。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import MIN_CELL

MASK = "遮蔽"


def small(n) -> bool:
    return 0 < n < MIN_CELL


def fmt(n) -> str:
    """單一人數：1–9 顯示 `<10`。"""
    return f"<{MIN_CELL}" if small(n) else str(int(n))


def pct(a, b) -> str:
    return "—" if not b else f"{100 * a / b:.1f}%"


def dist(counts: dict) -> dict:
    """一維分布遮蔽；只有一格被遮時，另遮次小的一格以免被反推。"""
    hide = {k for k, n in counts.items() if small(n)}
    if len(hide) == 1:
        rest = {k: n for k, n in counts.items() if k not in hide and n > 0}
        if rest:
            hide.add(min(rest, key=rest.get))
    return {k: (MASK if k in hide else str(int(n))) for k, n in counts.items()}


def crosstab_2x2(df: pd.DataFrame, a: str, b: str, label_a: str, label_b: str,
                 title: str) -> list:
    """2×2 交叉表（兩欄皆為 1/0）。任一格 n < 10 則整張表遮蔽。"""
    d = df[[a, b]].dropna()
    n = len(d)
    lines = [f"### {title}", ""]
    n11 = int(((d[a] == 1) & (d[b] == 1)).sum())
    n10 = int(((d[a] == 1) & (d[b] == 0)).sum())
    n01 = int(((d[a] == 0) & (d[b] == 1)).sum())
    n00 = int(((d[a] == 0) & (d[b] == 0)).sum())
    if n < MIN_CELL or any(small(c) for c in (n11, n10, n01, n00)):
        lines.append(f"兩者皆有效：{fmt(n)} 人。有細格 n < {MIN_CELL}，"
                     "整張表（人數、百分比、phi、邊際）已遮蔽。")
        return lines + [""]
    r1, r0, c1, c0 = n11 + n10, n01 + n00, n11 + n01, n10 + n00
    denominator = np.sqrt(float(r1) * r0 * c1 * c0)
    phi = (n11 * n00 - n10 * n01) / denominator if denominator > 0 else float("nan")
    lines += [
        f"兩者皆有效：{n} 人", "",
        f"| | {label_b}：是 | {label_b}：否 | 合計 |", "|---|---|---|---|",
        f"| {label_a}：是 | {n11} | {n10} | {r1} |",
        f"| {label_a}：否 | {n01} | {n00} | {r0} |",
        f"| 合計 | {c1} | {c0} | {n} |", "",
        f"- 「{label_a}者中有{label_b}」（列百分比）：{pct(n11, r1)}",
        f"- 「{label_b}者中有{label_a}」（欄百分比）：{pct(n11, c1)}",
        f"- phi 係數：{phi:.3f}",
    ]
    return lines + [""]


def count_distribution(df: pd.DataFrame, cols: list, labels: list, title: str) -> list:
    """症狀計數分布（各欄 1/0，三者皆有效者才計入）。"""
    d = df[cols].dropna()
    totals = d.sum(axis=1).astype(int)
    counts = {k: int((totals == k).sum()) for k in range(len(cols) + 1)}
    shown = dist(counts)
    lines = [f"### {title}", "",
             f"皆有效：{fmt(len(d))} 人（計入項目：{'、'.join(labels)}）", "",
             "| 症狀數 | 人數 |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in shown.items()]
    return lines + [""]
