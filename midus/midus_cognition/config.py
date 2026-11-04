# -*- coding: utf-8 -*-
"""路徑與資料集設定。

資料路徑一律由環境變數決定，程式內不寫死任何本機或共享資料夾路徑：

    MIDUS_DATA_ROOT    ICPSR 原始資料根目錄（內含 ICPSR_xxxxx/ 子目錄）
                       預設 ~/Documents/MIDUS/data/raw
    MIDUS_OUTPUT_DIR   分析輸出目錄（彙總結果，不含個人層級資料）
                       預設 ~/Documents/MIDUS/output
"""
from __future__ import annotations

import os
from pathlib import Path

DATA_ROOT = Path(os.environ.get("MIDUS_DATA_ROOT") or Path.home() / "Documents" / "MIDUS" / "data" / "raw")
OUTPUT_DIR = Path(os.environ.get("MIDUS_OUTPUT_DIR") or Path.home() / "Documents" / "MIDUS" / "output")

#: 分析用的四個核心資料檔（相對於 DATA_ROOT）
FILES = {
    "M2P1": "ICPSR_04652/DS0001/04652-0001-Data.sav",  # MIDUS 2 Project 1 主調查
    "M2P3": "ICPSR_25281/DS0001/25281-0001-Data.sav",  # MIDUS 2 Project 3 BTACT
    "M3P1": "ICPSR_36346/DS0001/36346-0001-Data.sav",  # MIDUS 3 Project 1 主調查
    "M3P3": "ICPSR_37095/DS0001/37095-0001-Data.sav",  # MIDUS 3 Project 3 BTACT
}

#: 個案層級資料的最小可呈現格數；低於此值一律遮蔽
MIN_CELL = 10

#: 多重插補設定（§6）
MI_M = 20
MI_SEED = 20261104


def path(key: str) -> Path:
    """回傳資料檔完整路徑；檔案不存在時給出可操作的錯誤訊息。"""
    p = DATA_ROOT / FILES[key]
    if not p.exists():
        raise FileNotFoundError(
            f"找不到 {key} 資料檔：{p}\n"
            f"請確認 MIDUS_DATA_ROOT 指向 ICPSR 原始資料根目錄"
            f"（目前為 {DATA_ROOT}），且該目錄下有 {FILES[key]}。"
        )
    return p


def output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR
