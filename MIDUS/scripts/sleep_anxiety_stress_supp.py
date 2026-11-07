# -*- coding: utf-8 -*-
"""補充檢定：(1) 正確的 VIF（排除與分項共線的指數）
(2) M3 負向情緒的中介在校正 M2 基線後是否仍成立（唯一通過 bootstrap 的那一條）
(3) 四類整組 vs 主效果的 E-value 式敏感度參考"""
exec(open('/mnt/project-files/MIDUS/scripts/sleep_anxiety_stress.py').read().split("print('='*100)")[0])
import statsmodels.formula.api as smf, statsmodels.api as sm, numpy as np, patsy
from statsmodels.stats.outliers_influence import variance_inflation_factor
BASE=core.dropna(subset=COV+['expo','C3TCOMP','B3TCOMPZ1']).copy()
print('N=%d 暴露=%d'%(len(BASE),int(BASE.expo.sum())))

print('\n### 更正後 VIF（不同時放指數與其四個分項）')
for name,vv in [('含指數、不含分項',['age','edu','bmi','chron27','depre','rxmed','sleep_ins','sleep_hr','anx_cidi','panic','neuro','negaf','stress_idx']),
                ('含四分項、不含指數',['age','edu','bmi','chron27','depre','rxmed','sleep_ins','sleep_hr','anx_cidi','panic','neuro','negaf','str_kin','str_fri','str_bill','str_disc'])]:
    t=BASE.dropna(subset=vv); X=sm.add_constant(t[vv]); print(' --',name,'N=%d'%len(t))
    for i,c in enumerate(X.columns):
        if c!='const': print('    %-11s VIF=%.2f'%(c,variance_inflation_factor(X.values,i)))

print('\n### M3 負向情緒的中介，加上 M2 負向情緒基線（滯後中介的正確規格）')
F2=F
for lab,extra in [('不校正 M2 基線（原結果）',''),('校正 M2 基線 negaf','+ negaf ')]:
    t=BASE.dropna(subset=COV+['expo','C3TCOMP','B3TCOMPZ1','negaf3','negaf']).copy()
    tot=smf.ols(f'C3TCOMP ~ expo + {extra}+ B3TCOMPZ1 + {F2}'.replace('+ +','+'),data=t).fit(
        cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    dr =smf.ols(f'C3TCOMP ~ expo + negaf3 + {extra}+ B3TCOMPZ1 + {F2}'.replace('+ +','+'),data=t).fit(
        cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    print('  %-24s N=%d 總=%.4f 直接=%.4f 間接=%+.4f (%.1f%%)'%(
        lab,len(t),tot.params['expo'],dr.params['expo'],tot.params['expo']-dr.params['expo'],
        100*(tot.params['expo']-dr.params['expo'])/tot.params['expo']))
    # 第一環
    m1=smf.ols(f'negaf3 ~ expo + negaf + age + female + edu',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    print('      第一環 便祕→M3負向情緒（校正M2基線）β=%+.4f p=%.4f'%(m1.params['expo'],m1.pvalues['expo']))
    m2b=smf.ols(f'C3TCOMP ~ negaf3 + B3TCOMPZ1 + {F2}',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    print('      第二環 M3負向情緒→認知 β=%+.4f p=%.4f'%(m2b.params['negaf3'],m2b.pvalues['negaf3']))

print('\n### 持續型便祕（最穩健結果）在加入四類後是否變動')
tr=d[d.B3TCOMPZ1.notna()&d.C3TCOMP.notna()&d.B1SA11K.notna()&d.C1SA11K.notna()].copy()
cond=[(tr.B1SA11K==1)&(tr.C1SA11K==1),(tr.B1SA11K==1)&(tr.C1SA11K==2),(tr.B1SA11K==2)&(tr.C1SA11K==1)]
tr['traj']=np.select(cond,['persist','m2only','m3only'],'never')
for lab,extra in [('基準',''),('＋四類整組',' + sleep_ins + anx_cidi + negaf + stress_idx')]:
    sub=COV+['C3TCOMP','B3TCOMPZ1']+(['sleep_ins','anx_cidi','negaf','stress_idx'] if extra else [])
    t=tr.dropna(subset=sub)
    m=smf.ols(f"C3TCOMP ~ C(traj, Treatment('never')) + B3TCOMPZ1 + {F}{extra}",data=t).fit(
        cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    k=[x for x in m.params.index if 'persist' in x][0]
    print('  %-12s N=%d 持續型 β=%+.4f SE=%.4f p=%.4f'%(lab,len(t),m.params[k],m.bse[k],m.pvalues[k]))

print('\n### 領域結果加入四類後（EM / EF）')
for out,base in [('C3TEM','B3TEMZ1'),('C3TEF','B3TEFZ1')]:
    for lab,extra in [('基準',''),('＋四類',' + sleep_ins + anx_cidi + negaf + stress_idx')]:
        sub=COV+['expo',out,base]+(['sleep_ins','anx_cidi','negaf','stress_idx'] if extra else [])
        t=BASE.dropna(subset=sub)
        m=smf.ols(f'{out} ~ expo + {base} + {F}{extra}',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
        print('  %-6s %-6s N=%d β=%+.4f p=%.4f'%(out,lab,len(t),m.params['expo'],m.pvalues['expo']))
