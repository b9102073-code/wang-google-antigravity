# -*- coding: utf-8 -*-
"""輸出：同時印到終端機並存成 Markdown，方便貼回論文或對話。"""
from __future__ import annotations

from datetime import date

import pandas as pd

from . import config
from .models import Estimate


class Report:
    """累積 Markdown 行，最後寫入 ``MIDUS_OUTPUT_DIR``。"""

    def __init__(self, filename: str, title: str, plan_sections: str = ""):
        self.filename = filename
        self.lines = [f"# {title}", ""]
        if plan_sections:
            self.lines += [f"> 對應分析計畫：{plan_sections}"]
        self.lines += [f"> 產出日期：{date.today().isoformat()}",
                       "> 本檔只含彙總結果，n < 10 已遮蔽。", ""]

    def add(self, *lines) -> "Report":
        for line in lines:
            print(line)
            self.lines.append(str(line))
        return self

    def heading(self, text: str, level: int = 2) -> "Report":
        print(f"\n### {text}")
        self.lines += ["", "#" * level + " " + text, ""]
        return self

    def note(self, text: str) -> "Report":
        print(f"> {text}")
        self.lines += [f"> {text}", ""]
        return self

    def estimates(self, rows, caption: str = "") -> "Report":
        """把 :class:`Estimate` 清單寫成表格，並印出對齊的終端機版本。"""
        rows = list(rows)
        if caption:
            self.lines += [caption, ""]
            print(caption)
        for row in rows:
            print(row.row())
        frame = pd.DataFrame([r.as_dict() for r in rows])
        self.lines += [frame.to_markdown(index=False), ""]
        return self

    def table(self, frame: pd.DataFrame) -> "Report":
        print(frame.to_string(index=False))
        self.lines += [frame.to_markdown(index=False), ""]
        return self

    def save(self) -> "Report":
        path = config.output_dir() / self.filename
        path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        print(f"\n已存到 {path}")
        return self


def estimate_frame(rows) -> pd.DataFrame:
    return pd.DataFrame([r.as_dict() for r in rows])


__all__ = ["Report", "estimate_frame", "Estimate"]
