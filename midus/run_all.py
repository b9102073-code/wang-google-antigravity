# -*- coding: utf-8 -*-
"""依序執行全部分析，輸出到 MIDUS_OUTPUT_DIR。

用法：
    python run_all.py              # 全部
    python run_all.py --fast       # 跳過多重插補（最慢的兩支）
    python run_all.py 05 07        # 只跑指定編號
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS = [
    ("01", "01_sample_flow.py", "樣本流程 §4.4"),
    ("03", "03_exposure_definitions.py", "暴露定義比較 §5.1B"),
    ("04", "04_hemorrhoid_crosstab.py", "痔瘡交叉表 §5.1A"),
    ("05", "05_main_model.py", "主模型 §7.1A/B"),
    ("06", "06_multiple_imputation.py", "多重插補（主要報告值）§7.1C"),
    ("07", "07_trajectory.py", "軌跡模型 §7.2A"),
    ("08", "08_moderation.py", "調節分析 §7.3A"),
    ("09", "09_sensitivity.py", "敏感度分析 §8A"),
    ("10", "10_weighted.py", "加權敏感度分析 §8B"),
]
SLOW = {"06", "09", "10"}   # 含多重插補


def main(argv):
    fast = "--fast" in argv
    wanted = [a for a in argv if a.isdigit()]
    here = Path(__file__).resolve().parent / "scripts"
    failures = []
    for number, filename, label in SCRIPTS:
        if wanted and number not in wanted:
            continue
        if fast and number in SLOW:
            print(f"\n[跳過] {number} {label}（--fast）")
            continue
        print(f"\n{'=' * 70}\n[{number}] {label} — {filename}\n{'=' * 70}")
        result = subprocess.run([sys.executable, str(here / filename)], cwd=here)
        if result.returncode:
            failures.append(filename)
            print(f"!! {filename} 失敗（returncode {result.returncode}）")
    if failures:
        print("\n失敗的腳本：" + "、".join(failures))
        return 1
    print("\n全部完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
