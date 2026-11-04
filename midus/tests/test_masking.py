# -*- coding: utf-8 -*-
"""遮蔽邏輯的單元測試（用假資料，不讀任何 MIDUS 檔案）。

執行：
    python tests/test_masking.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from midus_cognition import masking  # noqa: E402
from midus_cognition.config import MIN_CELL  # noqa: E402


def test_fmt():
    assert masking.fmt(0) == "0"
    assert masking.fmt(5) == f"<{MIN_CELL}"
    assert masking.fmt(MIN_CELL) == str(MIN_CELL)


def test_dist_hides_second_smallest():
    """只有一格 < 10 時，必須再遮次小的一格，否則可由合計反推。"""
    out = masking.dist({"x": 5, "y": 40, "z": 90})
    assert out["x"] == masking.MASK
    assert out["y"] == masking.MASK
    assert out["z"] == "90"


def test_dist_keeps_large_cells():
    out = masking.dist({"a": 50, "b": 60})
    assert out == {"a": "50", "b": "60"}


def test_crosstab_masks_whole_table():
    """任一細格 < 10 時，整張 2×2 表（含 phi 與邊際）都要遮蔽。"""
    frame = pd.DataFrame({"a": [1] * 5 + [0] * 95 + [1] * 50,
                          "b": [1] * 5 + [1] * 95 + [0] * 50})
    text = "\n".join(masking.crosstab_2x2(frame, "a", "b", "甲", "乙", "測試"))
    assert "已遮蔽" in text
    assert "phi 係數" not in text
    assert "| 甲：是 |" not in text


def test_crosstab_reports_when_all_cells_large():
    frame = pd.DataFrame({"a": [1] * 60 + [0] * 140, "b": [1] * 30 + [0] * 30 + [1] * 70 + [0] * 70})
    text = "\n".join(masking.crosstab_2x2(frame, "a", "b", "甲", "乙", "測試"))
    assert "phi 係數" in text and "已遮蔽" not in text


def test_count_distribution_masks_small():
    frame = pd.DataFrame({"x": [1.0] * 3 + [0.0] * 200, "y": [0.0] * 203})
    text = "\n".join(masking.count_distribution(frame, ["x", "y"], ["甲", "乙"], "測試"))
    assert masking.MASK in text


if __name__ == "__main__":
    failed = 0
    for name, func in sorted(globals().items()):
        if name.startswith("test_") and callable(func):
            try:
                func()
                print(f"  ok   {name}")
            except AssertionError as exc:
                failed += 1
                print(f"  FAIL {name}: {exc}")
    print("全部通過（假資料；未讀取任何 MIDUS 檔案）" if not failed else f"{failed} 項失敗")
    sys.exit(1 if failed else 0)
