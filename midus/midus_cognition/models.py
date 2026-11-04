# -*- coding: utf-8 -*-
"""估計模型（對應分析計畫 §7）。

核心設定（三者不可更動，否則結論會反轉或失真）：

1. **基線校正 ANCOVA**：`C3TCOMP ~ 暴露 + B3TCOMPZ1 + 共變項`。
   ⚠️ 不可用變化量 `C3TCOMP − B3TCOMPZ1` 當結果變項：均值回歸會得出
   「便秘保護認知」的相反結論（§7.1）。
2. **家庭叢集穩健標準誤**，叢集單位 `M2FAMNUM`（樣本含雙胞胎與手足）。
3. **多重插補為主要報告值**，完整案例為敏感度分析（§6、§7.1C）。
"""
from __future__ import annotations

import re
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from . import config
from .data import COVARIATE_RHS, MODEL_COVARIATES

CLUSTER = "M2FAMNUM"


@dataclass
class Estimate:
    """單一係數的估計結果。"""

    label: str
    n: int
    n_exposed: int
    beta: float
    se: float
    p: float
    ci_low: float
    ci_high: float
    ess: float | None = None  # 加權分析的有效樣本數

    def row(self) -> str:
        ess = "" if self.ess is None else "  有效樣本數 %.0f (%.0f%%)" % (self.ess, 100 * self.ess / self.n)
        return ("  %-30s N=%5d 暴露=%4d  β=%7.3f SE=%.3f p=%.4f CI[%7.3f, %7.3f]%s"
                % (self.label, self.n, self.n_exposed, self.beta, self.se,
                   self.p, self.ci_low, self.ci_high, ess))

    def as_dict(self) -> dict:
        return {"分析": self.label, "N": self.n, "暴露": self.n_exposed,
                "β": round(self.beta, 3), "SE": round(self.se, 3),
                "p": round(self.p, 4),
                "95% CI": "[%.3f, %.3f]" % (self.ci_low, self.ci_high)}


def complete_cases(df: pd.DataFrame, outcome: str, baseline: str,
                   exposure: str = "expo_b", extra=(), required=None) -> pd.DataFrame:
    """完整案例子集。``required`` 預設為 §5.5 全部共變項。"""
    need = list(MODEL_COVARIATES if required is None else required)
    need += [outcome, baseline, CLUSTER] + list(extra)
    if exposure:
        need.append(exposure)
    return df.dropna(subset=need)


def _formula_columns(df: pd.DataFrame, *formula_parts) -> list:
    """取出公式中實際存在於資料的欄名。

    模型公式裡出現的變項若未納入 dropna，patsy 會自行丟掉含遺漏的列，
    使叢集變項的長度與設計矩陣不一致（statsmodels 會直接報錯）。
    """
    names = set()
    for part in formula_parts:
        if part:
            names.update(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", part))
    return [c for c in names if c in df.columns]


def ancova(df: pd.DataFrame, outcome: str, baseline: str, exposure: str = "expo_b",
           covariate_rhs: str | None = COVARIATE_RHS, extra_rhs: str = "",
           weights: str | None = None, label: str = "", term: str | None = None,
           required=None) -> Estimate:
    """基線校正 ANCOVA，家庭叢集穩健標準誤。

    ``covariate_rhs=None`` 表示僅控制基線（用於逐步調整的第一步）。
    ``weights`` 給權重欄名時改用 WLS（§8B 加權敏感度分析）。
    """
    extra_cols = [weights] if weights else []
    extra_cols += _formula_columns(df, covariate_rhs, extra_rhs)
    t = complete_cases(df, outcome, baseline, exposure, extra=extra_cols, required=required)
    rhs = baseline
    if covariate_rhs:
        rhs += " + " + covariate_rhs
    if extra_rhs:
        rhs += " + " + extra_rhs
    formula = f"{outcome} ~ {exposure} + {rhs}"
    kwargs = {"weights": t[weights]} if weights else {}
    model = smf.wls(formula, data=t, **kwargs) if weights else smf.ols(formula, data=t)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": t[CLUSTER]})
    key = term or exposure
    ci = fit.conf_int().loc[key]
    ess = None
    if weights:
        w = t[weights].to_numpy(dtype=float)
        ess = w.sum() ** 2 / (w ** 2).sum()
    return Estimate(label or outcome, len(t), int(t[exposure].sum()),
                    fit.params[key], fit.bse[key], fit.pvalues[key],
                    ci.iloc[0], ci.iloc[1], ess)


def categorical_terms(df: pd.DataFrame, outcome: str, baseline: str, variable: str,
                      reference: str, covariate_rhs: str | None = COVARIATE_RHS,
                      required=None) -> tuple[pd.DataFrame, list]:
    """類別預測變項（如便秘軌跡）的各組對照，參照組為 ``reference``。"""
    need = list(MODEL_COVARIATES if required is None else required)
    need += [outcome, baseline, CLUSTER, variable]
    need += _formula_columns(df, covariate_rhs)
    t = df.dropna(subset=need)
    rhs = baseline + (" + " + covariate_rhs if covariate_rhs else "")
    formula = f"{outcome} ~ C({variable}, Treatment('{reference}')) + {rhs}"
    fit = smf.ols(formula, data=t).fit(cov_type="cluster", cov_kwds={"groups": t[CLUSTER]})
    out = []
    for key in fit.params.index:
        if variable not in key or "T." not in key:
            continue
        group = key.split("T.")[1].rstrip("]")
        ci = fit.conf_int().loc[key]
        out.append(Estimate(group, len(t), int((t[variable] == group).sum()),
                            fit.params[key], fit.bse[key], fit.pvalues[key],
                            ci.iloc[0], ci.iloc[1]))
    return t, out


def interaction(df: pd.DataFrame, outcome: str, baseline: str, modifier: str,
                exposure: str = "expo_b", label: str = "") -> Estimate:
    """調節分析：暴露 × 調節變項（§7.3）。"""
    return ancova(df, outcome, baseline, exposure=exposure,
                  extra_rhs=f"{exposure}:{modifier}",
                  label=label or f"{exposure} × {modifier}",
                  term=f"{exposure}:{modifier}")


def _rubin(betas: np.ndarray, ses: np.ndarray) -> tuple:
    """Rubin 法則彙總多重插補結果。"""
    m = len(betas)
    qbar = betas.mean()
    ubar = (ses ** 2).mean()          # 插補內變異
    b = betas.var(ddof=1)             # 插補間變異
    total = ubar + (1 + 1 / m) * b
    se = np.sqrt(total)
    df = (m - 1) * (1 + ubar / ((1 + 1 / m) * b)) ** 2
    tcrit = stats.t.ppf(0.975, df)
    p = 2 * (1 - stats.t.cdf(abs(qbar / se), df))
    return qbar, se, p, qbar - tcrit * se, qbar + tcrit * se, df


def multiple_imputation(df: pd.DataFrame, outcome: str, baseline: str,
                        exposure: str = "expo_b", weights: str | None = None,
                        m: int = config.MI_M, seed: int = config.MI_SEED,
                        label: str = "多重插補 (M=%d)") -> tuple[Estimate, float]:
    """MICE（predictive mean matching）＋ Rubin 彙總（§6、§7.1C）。

    插補模型納入結果、基線認知、暴露與全部共變項。吸菸三分類改以兩個
    虛擬變項進入（MICEData 不支援 formula 內的 ``C()``）。
    回傳 (估計結果, Rubin 自由度)。
    """
    cols = [outcome, baseline, exposure, "smoke"] + [c for c in MODEL_COVARIATES if c != "smoke"]
    keep = [CLUSTER] + ([weights] if weights else [])
    x = df[cols + keep].copy()
    # 結果、基線與暴露本身不插補：缺其中任一者不屬於可分析樣本
    x = x.dropna(subset=[outcome, baseline, exposure])
    if weights:
        x = x[x[weights].notna()]
    x["sm1"] = (x["smoke"] == 1).astype(float)
    x["sm2"] = (x["smoke"] == 2).astype(float)
    x = x.drop(columns=["smoke"])
    cluster = x.pop(CLUSTER)
    weight_values = x.pop(weights) if weights else None

    rhs = " + ".join([baseline] + [c for c in MODEL_COVARIATES if c != "smoke"] + ["sm1", "sm2"])
    formula = f"{outcome} ~ {exposure} + {rhs}"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from statsmodels.imputation import mice
        np.random.seed(seed)
        imputer = mice.MICEData(x, k_pmm=5)
        betas, ses = [], []
        for _ in range(m):
            imputer.update_all(1)
            data = imputer.data
            if weights is None:
                fit = sm.OLS.from_formula(formula, data=data).fit(
                    cov_type="cluster", cov_kwds={"groups": cluster.to_numpy()})
            else:
                fit = sm.WLS.from_formula(formula, data=data,
                                          weights=weight_values.to_numpy()).fit(
                    cov_type="cluster", cov_kwds={"groups": cluster.to_numpy()})
            betas.append(fit.params[exposure])
            ses.append(fit.bse[exposure])

    beta, se, p, lo, hi, df_rubin = _rubin(np.array(betas), np.array(ses))
    name = label % m if "%d" in label else label
    return Estimate(name, len(x), int(x[exposure].sum()), beta, se, p, lo, hi), df_rubin


def mde(n: int, n_cases: int, residual_sd: float = 0.60,
        alpha: float = 0.05, power: float = 0.80) -> float:
    """最小可偵測效果量（常態近似），用於檢定力說明。"""
    if n_cases <= 0 or n_cases >= n:
        return float("nan")
    z = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    prop = n_cases / n
    return z * residual_sd * np.sqrt(1 / (n * prop * (1 - prop)))
