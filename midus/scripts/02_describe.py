# -*- coding: utf-8 -*-
"""任意變項的描述統計（n < 10 自動遮蔽）。

用法：
    python scripts/02_describe.py M2P1 B1PAGE_M2 B1PRSEX
資料集：M2P1、M2P3、M3P1、M3P3

輸出存到 MIDUS_OUTPUT_DIR/describe_<資料集>.md，可直接貼回對話討論。
注意：有值標籤的類別也可能是缺失碼（如 98、99），請對照 codebook。
"""
import sys

import _path  # noqa: F401
import pyreadstat

from midus_cognition import config
from midus_cognition.masking import MASK, MIN_CELL, fmt

MAX_CATEGORIES = 15  # 類別數超過此值視為連續變項


def describe(df, meta, var):
    lines = [f"## {var}：{meta.column_names_to_labels.get(var) or ''}"]
    s = df[var]
    labels = meta.variable_value_labels.get(var, {})
    valid = s.dropna()
    n_missing = int(s.isna().sum())
    if 0 < n_missing < MIN_CELL:        # 避免用總 N 減有效 N 反推遺漏數
        lines.append(f"有效 N = {len(s) - MIN_CELL + 1}–{len(s)}，遺漏 = <{MIN_CELL}")
    elif 0 < len(valid) < MIN_CELL:
        lines.append(f"有效 N = <{MIN_CELL}，遺漏 = {len(s) - MIN_CELL + 1}–{len(s)}")
    else:
        lines.append(f"有效 N = {len(valid)}，遺漏 = {n_missing}")
    if len(valid) < MIN_CELL:
        return lines + [f"（有效樣本 < {MIN_CELL}，不輸出統計量）"]
    if labels or valid.nunique() <= MAX_CATEGORIES:
        lines += ["", "| 值 | 標籤 | n | % |", "|---|---|---|---|"]
        counts = valid.value_counts().sort_index()
        hide = set(counts[counts < MIN_CELL].index)
        if len(hide) == 1 and len(counts) > 1:   # 只遮一格可被反推，再遮次小的一格
            hide.add(counts.drop(list(hide)).idxmin())
        for value, n in counts.items():
            if value in hide:
                lines.append(f"| {value:g} | {labels.get(value, '')} | {MASK} | — |")
            else:
                share = "—" if 0 < n_missing < MIN_CELL else f"{100 * n / len(valid):.1f}"
                lines.append(f"| {value:g} | {labels.get(value, '')} | {n} | {share} |")
    if not labels and valid.nunique() > 2:
        lines.append(f"M = {valid.mean():.2f}，SD = {valid.std():.2f}，"
                     f"中位數 = {valid.median():.2f}")
    return lines


def main(argv):
    if len(argv) < 2 or argv[0] not in config.FILES:
        print(__doc__)
        return 1
    name, variables = argv[0], argv[1:]
    df, meta = pyreadstat.read_sav(str(config.path(name)), usecols=variables,
                                   user_missing=True)
    out = [f"# {name} 描述統計（n < {MIN_CELL} 已遮蔽）", f"總樣本 N = {fmt(len(df))}", ""]
    for var in variables:
        out += describe(df, meta, var) + [""]
    text = "\n".join(out)
    path = config.output_dir() / f"describe_{name}.md"
    path.write_text(text, encoding="utf-8")
    print(text)
    print(f"\n已存到 {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
