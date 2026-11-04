# -*- coding: utf-8 -*-
"""讓 scripts/ 下的腳本不必安裝套件即可 import midus_cognition。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
