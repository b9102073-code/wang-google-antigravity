# MIDUS 便秘 → 認知功能縱貫分析

博士論文「腸腦軸：便秘、發炎與認知功能」的分析程式。資料來源為 MIDUS
（Midlife in the United States）第二波與第三波，分析設定對應
`博士研究/分析計畫草稿.md`，每支腳本的 docstring 都註明對應章節。

> **此目錄只放程式碼。** 任何 MIDUS 原始資料（`.sav`）、受試者層級的中間檔
> 與含個人資料的輸出一律不進版本控管（見根目錄 `.gitignore`）。
> 資料路徑由環境變數指定，程式內不寫死任何本機路徑。

---

## 1. 環境

分析環境為 Python。**12/31 前不升級 Python 或套件**：分析中途換環境，
數字可能出現小差異，口試與審稿時難以重現。

```bash
cd ~/Documents/MIDUS                 # 或任何你放這份程式的地方
python3 -m venv .venv
.venv/bin/pip install -r midus/requirements.txt
```

原始分析環境（2026-10-11 核對）：Python 3.9.6、pandas 2.3.3、numpy 2.0.2、
scipy 1.13.1、statsmodels 0.14.4、pyreadstat 1.2.8。

## 2. 資料擺放位置

程式讀兩個環境變數，不設定時用預設值：

| 環境變數 | 用途 | 預設值 |
|---|---|---|
| `MIDUS_DATA_ROOT` | ICPSR 原始資料根目錄 | `~/Documents/MIDUS/data/raw` |
| `MIDUS_OUTPUT_DIR` | 分析輸出目錄 | `~/Documents/MIDUS/output` |

`MIDUS_DATA_ROOT` 下必須有以下四個檔（目錄結構即 ICPSR 下載後的原樣）：

| 鍵 | 內容 | 相對路徑 |
|---|---|---|
| `M2P1` | MIDUS 2 Project 1 主調查（暴露、共變項、權重） | `ICPSR_04652/DS0001/04652-0001-Data.sav` |
| `M2P3` | MIDUS 2 Project 3 BTACT（基線認知） | `ICPSR_25281/DS0001/25281-0001-Data.sav` |
| `M3P1` | MIDUS 3 Project 1 主調查（第二波暴露、權重） | `ICPSR_36346/DS0001/36346-0001-Data.sav` |
| `M3P3` | MIDUS 3 Project 3 BTACT（結果） | `ICPSR_37095/DS0001/37095-0001-Data.sav` |

檔案缺少時程式會直接指出少了哪一個、該放在哪裡。

## 3. 執行

```bash
cd ~/Documents/MIDUS                      # 放這份程式的上層目錄
export MIDUS_DATA_ROOT="$PWD/data/raw"
export MIDUS_OUTPUT_DIR="$PWD/output"

.venv/bin/python midus/run_all.py           # 全部分析
.venv/bin/python midus/run_all.py --fast     # 跳過多重插補（快，約一分鐘）
.venv/bin/python midus/run_all.py 05 07      # 只跑指定編號
```

單獨跑一支：

```bash
.venv/bin/python midus/scripts/05_main_model.py
```

任意變項的描述統計：

```bash
.venv/bin/python midus/scripts/02_describe.py M2P1 B1PAGE_M2 B1PRSEX
```

遮蔽邏輯的單元測試（用假資料，不讀任何 MIDUS 檔案）：

```bash
.venv/bin/python midus/tests/test_masking.py
```

每支腳本都把結果同時印到終端機並存成 Markdown 到 `MIDUS_OUTPUT_DIR`，
可直接貼回論文或對話討論。全部輸出都是彙總結果，**n < 10 一律遮蔽**，
受試者層級資料不會離開本機。

執行時間：除多重插補（`06`、`09`、`10`，各約數分鐘）外，其餘每支數十秒。

## 4. 腳本與分析計畫的對應

| 腳本 | 內容 | 分析計畫章節 | 輸出 |
|---|---|---|---|
| `01_sample_flow.py` | 樣本流程、組成、排除條件影響 | §4.3、§4.4 | `sample_flow.md` |
| `02_describe.py` | 任意變項描述統計（CLI） | §9 | `describe_<資料集>.md` |
| `03_exposure_definitions.py` | 暴露定義 A–F 比較、檢定力 | §5.1、§5.1B、§8-4 | `exposure_definitions.md` |
| `04_hemorrhoid_crosstab.py` | 痔瘡 × 便秘交叉表（描述性） | §5.1A、§8-8 | `hemorrhoid_constipation.md` |
| `05_main_model.py` | 主模型、三個認知領域、逐步調整 | §7.1、§7.1A、§7.1B | `main_model.md` |
| `06_multiple_imputation.py` | **主要報告值**（MICE, M=20） | §6、§7.1C | `multiple_imputation.md` |
| `07_trajectory.py` | 便秘軌跡四分組 | §7.2、§7.2A | `trajectory.md` |
| `08_moderation.py` | 便秘 × 年齡／性別（陰性結果） | §7.3、§7.3A | `moderation.md` |
| `09_sensitivity.py` | 敏感度分析全套 | §8、§8A | `sensitivity.md` |
| `10_weighted.py` | 加權敏感度分析 | §8B | `weighted.md` |

套件模組：

| 模組 | 職責 |
|---|---|
| `midus_cognition/config.py` | 路徑、資料集清單、插補設定 |
| `midus_cognition/codes.py` | MIDUS 缺失碼處理（§6、§5.5A） |
| `midus_cognition/data.py` | **唯一**的資料建構入口：合併四檔、建暴露／共變項／軌跡／權重 |
| `midus_cognition/models.py` | ANCOVA、叢集穩健 SE、類別對照、交互作用、MICE＋Rubin、檢定力 |
| `midus_cognition/masking.py` | n < 10 遮蔽 |
| `midus_cognition/reporting.py` | Markdown 輸出 |

資料建構集中在 `data.py` 一處，避免各腳本各自清理而產生不一致的設定
（這是改寫前的主要問題：原本數支腳本以 `exec(open(...).read())` 互相重用
片段，設定一旦變動難以追蹤）。

## 5. 不可更動的設定（照改會得到錯誤結論）

這些都是實測踩過的坑，已寫進程式與註解，修改前請先讀對應章節：

1. **不可用變化量當結果。** 以 `C3TCOMP − B3TCOMPZ1` 為結果會因均值回歸
   得出「便秘保護認知」的相反結論。一律基線校正 ANCOVA（§7.1）。
2. **`C3TCOMP`／`C3TEM`／`C3TEF` 已以 MIDUS 2 全國常模標準化，不可再重新
   標準化**；基線必須配 `B3TCOMPZ1`／`B3TEMZ1`／`B3TEFZ1`。
   另注意 **`B3TEM`／`B3TEF` 這兩個變項不存在**（§5.2）。
3. **權重變項的 `99` 是「不適用」代碼**，必須先設為缺失，否則 2,706 名
   非 RDD 受訪者會被當成 99 倍權重（§8B）。
4. **一律以 `user_missing=True` 讀取後逐一判斷缺失碼**，不可讓 pyreadstat
   自動套用 SPSS 的使用者缺失定義。否則 `B1PA37 = 96`（從未抽過菸）這類
   有效資訊會被當成缺失，1,270 名從未吸菸者消失（§5.5A）。
5. **慢性病數須用 27 題版本**（`B1SCHRON` 扣除便秘、胃部不適、痔瘡三題），
   否則與暴露共線（§5.5A）。
6. **飲酒須將未飲酒者補 0**，否則缺失率 43%（§5.5A）。
7. **主要暴露為定義 B「任一波便秘」，且是先驗選定**（Rome 準則下便秘為
   間斷復發症狀，單次橫斷問卷會錯分），不是依 p 值挑選（§5.1B）。
8. **主要報告值是多重插補結果**，完整案例為敏感度分析（§6、§7.1C）。
9. **主分析維持全樣本未加權 ＋ `M2FAMNUM` 叢集穩健標準誤**（§8B）。

## 6. 已驗證可重現的結果

以共享資料夾的四個 `.sav` 實際執行，與分析計畫記錄的數值逐項相符
（β 與 SE 皆到小數第三位一致）：

| 分析 | 章節 | β | p | N／暴露 |
|---|---|---|---|---|
| 主要報告值：綜合分數，多重插補 M=20 | §7.1C | −0.097 | 0.0015 | 2,376／213 |
| 完整案例（敏感度） | §7.1B | −0.070 | 0.036 | 2,028／188 |
| 情節記憶，完整案例 | §7.1B | −0.111 | 0.047 | 2,028／188 |
| 執行功能，完整案例 | §7.1B | −0.097 | 0.035 | 2,028／188 |
| 持續型便秘（軌跡模型，完整共變項） | §7.2A | −0.165 | 0.0094 | 1,911／33 |
| 定義 F 兩波皆便秘 | §8A | −0.157 | 0.013 | 1,911／33 |
| ＋ 控制症狀放大 `B1SAMPLI` | §8A | −0.065 | **0.051** | 2,017／186 |
| 僅 RDD 主樣本 | §8A | −0.071 | **0.165** | 870／78 |
| 便秘 × 年齡交互作用 | §7.3A | −0.0005 | 0.868 | 2,028／188 |

多重插補下的認知領域結果（計畫中尚未記錄，本次新增）：
情節記憶 β = −0.144（p = 0.0059）、執行功能 β = −0.114（p = 0.0062）。

> 三個必須據實呈現、不可隱藏的弱點（已寫入對應腳本的 docstring）：
> 控制症狀放大傾向後 p = 0.051 剛好跨門檻；僅 RDD 主樣本時不顯著；
> 年齡與性別完全無調節效果，原研究問題「以年齡調節檢驗老化角色」未獲支持。

## 7. 尚未納入的分析

以下需要先下載對應 ICPSR 資料集，資料到位後再加腳本：

| 分析 | 需要的資料 | 章節 |
|---|---|---|
| Refresher 1＋2 獨立重複驗證（串接鍵 `MRID`，非 `M2ID`） | ICPSR 36532、37081、39670 | §7.5 |
| 發炎中介（橫斷設定：M2 便秘 → M2 發炎 → M3 認知） | ICPSR 29282 | §5.4、§7.4 |
| 流失偏誤（P7 召回樣本的字詞回憶） | ICPSR 38291 | §8-4 |
| MIDUS 1 反向因果檢驗（排除 M1 已便秘者） | ICPSR 2760 | §8 |
