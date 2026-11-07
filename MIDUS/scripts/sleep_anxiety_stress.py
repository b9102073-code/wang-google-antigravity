# -*- coding: utf-8 -*-
"""睡眠／焦慮／憂鬱／長期壓力 在便祕→認知關聯中的三種角色（混淆／中介／調節）

主模型沿用 full_model.py：暴露=定義B（任一波便祕）、結果 C3TCOMP 校正 B3TCOMPZ1、
§5.5 全共變項、M2FAMNUM 叢集 SE。
"""
import pyreadstat, pandas as pd, numpy as np, re, itertools
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor

R='/mnt/project-files/MIDUS/data/raw/'
NA=lambda s,codes: s.where(~s.isin(codes))
Z =lambda s: (s-s.mean())/s.std()

m2,mm=pyreadstat.read_sav(R+'ICPSR_04652/DS0001/04652-0001-Data.sav',user_missing=True)
sa11=[c for c in mm.column_names if re.match(r'^B1SA11[A-Z]{1,2}$',c)]
keep27=[c for c in sa11 if c not in ('B1SA11I','B1SA11K','B1SA11CC')]
keep24=[c for c in keep27 if c not in ('B1SA11T','B1SA11W')]   # 再扣掉焦憂與睡眠

M3V=['M2ID','C1SA11K','C1SA57A','C1SA57B','C1SA57C','C1SA57D','C1SA10G','C1SA11W','C1SA11T',
     'C1SA53A','C1SA53B','C1SNEURO','C1SNEGAF','C1SKINNE','C1SFDSNE','C1SSPCRI','C1SDAYDI',
     'C1SG9','C1SG7','C1PANXIE','C1PANXTD','C1PDEPRE','C1SA24F','C1SA24G','C1SA24H','C1SA24I','C1SA24J']
m3,_=pyreadstat.read_sav(R+'ICPSR_36346/DS0001/36346-0001-Data.sav',usecols=M3V,user_missing=True)
b2,_=pyreadstat.read_sav(R+'ICPSR_25281/DS0001/25281-0001-Data.sav',
  usecols=['M2ID','B3TCOMPZ1','B3TEMZ1','B3TEFZ1'])
b3,_=pyreadstat.read_sav(R+'ICPSR_37095/DS0001/37095-0001-Data.sav',usecols=['M2ID','C3TCOMP','C3TEM','C3TEF'])
d=m2.merge(b2,on='M2ID').merge(b3,on='M2ID').merge(m3,on='M2ID',how='left')

# ---------------- 暴露 ----------------
for c in ['B1SA11K','C1SA11K']: d[c]=NA(d[c],[-1,7,8,9])
d['expo']=np.where(d.B1SA11K.isna()&d.C1SA11K.isna(),np.nan,((d.B1SA11K==1)|(d.C1SA11K==1)).astype(float))

# ---------------- 既有共變項（與 full_model.py 完全相同） ----------------
d['age']=NA(d.B1PRAGE_2019,[97,98]); d['female']=(d.B1PRSEX==2).astype(float)
d['edu']=NA(d.B1PB1,[97,98]); d['bmi']=NA(d.B1SBMI,[-1,98])
k27=d[keep27].apply(lambda s: NA(s,[-1,7,8,9]))
d['chron27']=(k27==1).sum(axis=1).where(~k27.isna().all(axis=1))
k24=d[keep24].apply(lambda s: NA(s,[-1,7,8,9]))
d['chron24']=(k24==1).sum(axis=1).where(~k24.isna().all(axis=1))
d['depre']=NA(d.B1PDEPRE,[97,98])
d['smoke']=np.nan
d.loc[(d.B1PA37==96)|(d.B1PA38A==2),'smoke']=0
d.loc[(d.B1PA38A==1)&(d.B1PA39==2),'smoke']=1
d.loc[d.B1PA39==1,'smoke']=2
nondrink=d.B1PA50.isin([2,9])
d['drinks']=np.where(nondrink,0.0,NA(d.B1PA52,[97,98,99]))
d['binge'] =np.where(nondrink,0.0,NA(d.B1PA53,[97,98,99]))
d.loc[d.B1PA50==8,['drinks','binge']]=np.nan
d['alcprob']=NA(d.B1SALCOH,[-1,8]); d['rxmed']=NA(d.B1SRXMED,[-1,98])
d['ampli']=NA(d.B1SAMPLI,[-1,8])

# ---------------- 新增四類：M2 ----------------
# 睡眠：A61 四題失眠症狀（1 Never – 5 Almost always）
ins2=['B1SA61A','B1SA61B','B1SA61C','B1SA61D']
tmp=d[ins2].apply(lambda s: NA(s,[-1,7,8,9]))
d['sleep_ins']=tmp.mean(axis=1).where(tmp.notna().sum(axis=1)>=3)
# A10g 過去 30 天入睡／維持睡眠困難頻率（原碼 1=幾乎每天 … 6=完全沒有），反轉為越高越差
d['sleep_freq']=(7-NA(d.B1SA10G,[-1,7,8,9]))
d['sleep_chron']=(NA(d.B1SA11W,[-1,7,8,9])==1).astype(float).where(NA(d.B1SA11W,[-1,7,8,9]).notna())
# 睡眠時數（工作日）：98=Refused；分鐘欄 98 多為「只填小時」，故有效小時時以 0 分補
h=NA(d.B1SA57A,[-1,98]); mi=NA(d.B1SA57B,[-1,98])
d['sleep_hr']=h+mi.fillna(0)/60.0
d['sleep_short']=(d.sleep_hr<6).astype(float).where(d.sleep_hr.notna())
# 焦慮
d['anx_cidi']=NA(d.B1PANXIE,[97,98]); d['anx_dx']=NA(d.B1PANXTD,[7,8,9])
d['panic']=NA(d.B1PPANIC,[97,98])
d['neuro']=NA(d.B1SNEURO,[-1,8])
d['anxdep_sr']=(NA(d.B1SA11T,[-1,7,8,9])==1).astype(float).where(NA(d.B1SA11T,[-1,7,8,9]).notna())
# 憂鬱（既有 depre）＋負向情緒
d['negaf']=NA(d.B1SNEGAF,[-1,8])
# 長期壓力：家庭／朋友張力、付帳困難、日常歧視 → z 平均
d['str_kin']=NA(d.B1SKINNE,[-1,8]); d['str_fri']=NA(d.B1SFDSNE,[-1,8])
d['str_bill']=(5-NA(d.B1SG7,[-1,7,8,9]))          # 反轉：越高越難付
d['str_disc']=NA(d.B1SDAYDI,[-1,98])
d['str_spo']=NA(d.B1SSPCRI,[-1,8,9]); d['str_job']=NA(d.B1SJCDS,[-1,98,99])
S4=['str_kin','str_fri','str_bill','str_disc']
zs=d[S4].apply(Z); d['stress_idx']=zs.mean(axis=1).where(zs.notna().sum(axis=1)>=3)

# ---------------- 新增四類：M3（供中介用） ----------------
ins3=['C1SA57A','C1SA57B','C1SA57C','C1SA57D']
t3=d[ins3].apply(lambda s: NA(s,[-1,7,8,9]))
d['sleep_ins3']=t3.mean(axis=1).where(t3.notna().sum(axis=1)>=3)
d['neuro3']=NA(d.C1SNEURO,[-1,8]); d['negaf3']=NA(d.C1SNEGAF,[-1,8])
d['depre3']=NA(d.C1PDEPRE,[97,98]); d['anx_dx3']=NA(d.C1PANXTD,[7,8,9])
d['str_kin3']=NA(d.C1SKINNE,[-1,8]); d['str_fri3']=NA(d.C1SFDSNE,[-1,8])
d['str_bill3']=(5-NA(d.C1SG9,[-1,7,8,9])); d['str_disc3']=NA(d.C1SDAYDI,[-1,98])
z3=d[['str_kin3','str_fri3','str_bill3','str_disc3']].apply(Z)
d['stress_idx3']=z3.mean(axis=1).where(z3.notna().sum(axis=1)>=3)

core=d[d.B3TCOMPZ1.notna()&d.C3TCOMP.notna()&d.expo.notna()].copy()
COV=['age','female','edu','bmi','chron27','depre','smoke','drinks','binge','alcprob','rxmed']
F='C(smoke) + age + female + edu + bmi + chron27 + depre + drinks + binge + alcprob + rxmed'
BASE=core.dropna(subset=COV+['expo','C3TCOMP','B3TCOMPZ1']).copy()

FACTORS=[('sleep_ins','睡眠：A61 失眠症狀均分(1-5)'),
         ('sleep_freq','睡眠：A10g 30天入睡困難頻率(反轉1-6)'),
         ('sleep_chron','睡眠：A11w 自陳慢性睡眠問題(0/1)'),
         ('sleep_hr','睡眠：工作日睡眠時數'),
         ('sleep_short','睡眠：短睡 <6 小時(0/1)'),
         ('anx_cidi','焦慮：CIDI-SF GAD 連續(0-10)'),
         ('anx_dx','焦慮：CIDI-SF GAD 診斷(0/1)'),
         ('panic','焦慮：恐慌症狀(0-6)'),
         ('neuro','焦慮/特質：神經質(1-4)'),
         ('anxdep_sr','焦慮：A11t 自陳焦慮或憂鬱(0/1)'),
         ('depre','憂鬱：CIDI-SF 憂鬱連續(0-7)【已在既有模型】'),
         ('negaf','憂鬱：負向情緒(1-5)'),
         ('stress_idx','壓力：長期壓力指數(4項z平均)'),
         ('str_kin','壓力：家庭張力(1-4)'),
         ('str_fri','壓力：朋友張力(1-4)'),
         ('str_bill','壓力：付帳困難(反轉1-4)'),
         ('str_disc','壓力：日常歧視(9-45)'),
         ('str_spo','壓力：配偶張力(1-4，僅有伴侶者)'),
         ('str_job','壓力：工作要求(僅在職者)')]

def ols(df,fml,sub=None):
    t=df.dropna(subset=sub) if sub else df
    return smf.ols(fml,data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM}),t

print('='*100)
print('樣本：完整案例 N=%d／暴露=%d（與 full_model.py 的 2,028／188 基準一致）'%(len(BASE),int(BASE.expo.sum())))
m0,_=ols(BASE,f'C3TCOMP ~ expo + B3TCOMPZ1 + {F}')
B0=m0.params['expo']
print('基準主效果 β=%.4f SE=%.4f p=%.4f'%(B0,m0.bse['expo'],m0.pvalues['expo']))

print('\n'+'='*100)
print('步驟 0：四類因素的缺失與分布（決定哪些根本沒有檢定力）')
print('-'*100)
for v,lab in FACTORS:
    s=BASE[v]
    print('%-12s %-38s 可用 %4d (%5.1f%%)  mean=%7.3f sd=%6.3f'%(
        v,lab,s.notna().sum(),100*s.notna().mean(),s.mean(),s.std()))

print('\n'+'='*100)
print('步驟 1：混淆的兩個必要條件（a 路徑：便祕→因素；b 路徑：因素→認知）')
print('  a 路徑 = 因素在便祕組 vs 非便祕組的差（已校正年齡性別教育）')
print('  b 路徑 = 因素對 M3 認知的效果（已校正基線認知＋全共變項，未含便祕）')
print('-'*100)
rows=[]
for v,lab in FACTORS:
    sub=['expo',v,'age','female','edu']
    ma,ta=ols(BASE,f'{v} ~ expo + age + female + edu',sub)
    sd=ta[v].std()
    aстd=ma.params['expo']/sd if sd>0 else np.nan
    sub2=COV+['C3TCOMP','B3TCOMPZ1',v]
    mb,tb=ols(BASE,f'C3TCOMP ~ {v} + B3TCOMPZ1 + {F}',sub2)
    bstd=mb.params[v]*tb[v].std()
    rows.append(dict(v=v,lab=lab,a=ma.params['expo'],a_sd=aстd,ap=ma.pvalues['expo'],
                     b=mb.params[v],b_sd=bstd,bp=mb.pvalues[v],n=len(tb)))
    print('%-12s a=%7.3f (%+.3f SD, p=%.4f) | b=%7.4f (%+.3f SD/SD, p=%.4f) N=%d'%(
        v,ma.params['expo'],aстd,ma.pvalues['expo'],mb.params[v],bstd,mb.pvalues[v],len(tb)))
pa=multipletests([r['ap'] for r in rows],method='fdr_bh')[1]
pb=multipletests([r['bp'] for r in rows],method='fdr_bh')[1]
print('\nFDR(BH) 校正後：')
for r,qa,qb in zip(rows,pa,pb):
    print('  %-12s a 路徑 q=%.4f %s | b 路徑 q=%.4f %s'%(r['v'],qa,'✔' if qa<.05 else '',qb,'✔' if qb<.05 else ''))

print('\n'+'='*100)
print('步驟 2：作為共變項加入後主效果的衰減（固定每個模型自己的完整案例樣本）')
print('-'*100)
def addcov(extra,label,dropv):
    sub=COV+['expo','C3TCOMP','B3TCOMPZ1']+dropv
    t=BASE.dropna(subset=sub)
    mb=smf.ols(f'C3TCOMP ~ expo + B3TCOMPZ1 + {F}',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    ma=smf.ols(f'C3TCOMP ~ expo + B3TCOMPZ1 + {F}{extra}',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    att=100*(1-ma.params['expo']/mb.params['expo'])
    print('%-40s N=%4d  未加 β=%7.4f → 加入後 β=%7.4f (p=%.4f)  衰減 %+5.1f%%'%(
        label,len(t),mb.params['expo'],ma.params['expo'],ma.pvalues['expo'],att))
    return ma.params['expo'],att
addcov(' + sleep_ins',' ＋睡眠（失眠症狀均分）',['sleep_ins'])
addcov(' + sleep_ins + sleep_hr + sleep_chron',' ＋睡眠（整組三項）',['sleep_ins','sleep_hr','sleep_chron'])
addcov(' + anx_cidi',' ＋焦慮（CIDI-SF 連續）',['anx_cidi'])
addcov(' + anx_cidi + panic + neuro',' ＋焦慮（整組：GAD＋恐慌＋神經質）',['anx_cidi','panic','neuro'])
addcov(' + negaf',' ＋憂鬱（負向情緒；depre 已在模型內）',['negaf'])
addcov(' + stress_idx',' ＋長期壓力（指數）',['stress_idx'])
addcov(' + str_kin + str_fri + str_bill + str_disc',' ＋長期壓力（四分項）',S4)
addcov(' + sleep_ins + anx_cidi + negaf + stress_idx',' ＋四類整組同時加入',['sleep_ins','anx_cidi','negaf','stress_idx'])
print('\n  對照：憂鬱在既有模型中的貢獻（把 depre 從完整模型移除）')
t=BASE
mwith=smf.ols(f'C3TCOMP ~ expo + B3TCOMPZ1 + {F}',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
F_nodep=F.replace(' + depre','')
mno=smf.ols(f'C3TCOMP ~ expo + B3TCOMPZ1 + {F_nodep}',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
print('    無 depre β=%.4f → 含 depre β=%.4f（憂鬱造成的衰減 %+.1f%%）'%(
    mno.params['expo'],mwith.params['expo'],100*(1-mwith.params['expo']/mno.params['expo'])))
print('  對照：A11 慢性病計數中本來就含「焦慮憂鬱(T)」與「慢性睡眠問題(W)」→ 改用 24 題重算')
t2=BASE.dropna(subset=['chron24'])
F24=F.replace('chron27','chron24')
m24=smf.ols(f'C3TCOMP ~ expo + B3TCOMPZ1 + {F24}',data=t2).fit(cov_type='cluster',cov_kwds={'groups':t2.M2FAMNUM})
print('    chron27 β=%.4f → chron24（扣掉 T 與 W）β=%.4f'%(mwith.params['expo'],m24.params['expo']))

print('\n'+'='*100)
print('步驟 3：中介檢定（便祕 M2 → 因素 → 認知 M3），差異法＋Bootstrap 1000 次')
print('-'*100)
rng=np.random.default_rng(20261107)
import patsy
def _fit(y,X):
    return np.linalg.lstsq(X,y,rcond=None)[0]
def mediate(med,label):
    sub=COV+['expo','C3TCOMP','B3TCOMPZ1',med]
    t=BASE.dropna(subset=sub).copy()
    y,X0=patsy.dmatrices(f'C3TCOMP ~ expo + B3TCOMPZ1 + {F}',data=t,return_type='matrix')
    _,X1=patsy.dmatrices(f'C3TCOMP ~ expo + {med} + B3TCOMPZ1 + {F}',data=t,return_type='matrix')
    y=np.asarray(y).ravel(); X0=np.asarray(X0); X1=np.asarray(X1)
    i0=list(X0.design_info.column_names).index('expo') if hasattr(X0,'design_info') else None
    n0=patsy.dmatrix(f'expo + B3TCOMPZ1 + {F}',data=t).design_info.column_names
    n1=patsy.dmatrix(f'expo + {med} + B3TCOMPZ1 + {F}',data=t).design_info.column_names
    j0=n0.index('expo'); j1=n1.index('expo')
    tot=_fit(y,X0)[j0]; dir_=_fit(y,X1)[j1]; ind=tot-dir_
    # 以家庭為單位的叢集 bootstrap（索引層級，避免 DataFrame 複製）
    codes,uniq=pd.factorize(t.M2FAMNUM.values)
    idx_by_fam=[np.where(codes==k)[0] for k in range(len(uniq))]
    nf=len(uniq); bs=[]
    for _ in range(1000):
        pick=rng.integers(0,nf,nf)
        ii=np.concatenate([idx_by_fam[k] for k in pick])
        try:
            a=_fit(y[ii],X0[ii])[j0]; b=_fit(y[ii],X1[ii])[j1]; bs.append(a-b)
        except Exception: pass
    lo,hi=np.percentile(bs,[2.5,97.5])
    pm=100*ind/tot if tot!=0 else np.nan
    print('%-34s N=%4d 總效果=%7.4f 直接=%7.4f 間接=%+7.4f CI[%+.4f,%+.4f] 中介比例 %+5.1f%%'%(
        label,len(t),tot,dir_,ind,lo,hi,pm))
print('  (a) 同波中介（M2 因素；只能說是共變，不能說是中介）')
for v,lab in [('sleep_ins','M2 失眠症狀'),('anx_cidi','M2 焦慮 CIDI'),('negaf','M2 負向情緒'),('stress_idx','M2 長期壓力指數')]:
    mediate(v,lab)
print('  (b) 後續波中介（M3 因素，時序正確：便祕 M2 → 因素 M3 → 認知 M3）')
for v,lab in [('sleep_ins3','M3 失眠症狀'),('depre3','M3 憂鬱'),('negaf3','M3 負向情緒'),('stress_idx3','M3 長期壓力指數')]:
    mediate(v,lab)

print('\n'+'='*100)
print('步驟 3b：中介的第一環（便祕 M2 → M3 因素，已校正該因素的 M2 基線）')
print('-'*100)
pairs=[('sleep_ins3','sleep_ins','失眠症狀'),('depre3','depre','憂鬱'),
       ('negaf3','negaf','負向情緒'),('stress_idx3','stress_idx','長期壓力指數'),
       ('neuro3','neuro','神經質')]
ps=[]
for y,x0,lab in pairs:
    sub=['B1SA11K','age','female','edu',y,x0]
    t=BASE.dropna(subset=sub).copy()
    t['e2']=(t.B1SA11K==1).astype(float)
    m=smf.ols(f'{y} ~ e2 + {x0} + age + female + edu',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    sd=t[y].std(); ps.append(m.pvalues['e2'])
    print('  M2便祕 → %-10s(M3)  β=%+7.4f (%+.3f SD) p=%.4f N=%d'%(lab,m.params['e2'],m.params['e2']/sd,m.pvalues['e2'],len(t)))
print('  FDR q:',np.round(multipletests(ps,method='fdr_bh')[1],4))

print('\n'+'='*100)
print('步驟 4：調節（交互作用）＋最小可偵測效果量（80% power, α=.05）')
print('-'*100)
res=[]
for v,lab in FACTORS:
    sub=COV+['expo','C3TCOMP','B3TCOMPZ1',v]
    t=BASE.dropna(subset=sub)
    if t[v].nunique()<2: continue
    m=smf.ols(f'C3TCOMP ~ expo*{v} + B3TCOMPZ1 + {F}',data=t).fit(cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    k=[x for x in m.params.index if ':' in x][0]
    sd=t[v].std()
    beta_sd=m.params[k]*sd      # 每 1 SD 因素變化造成的主效果變化
    mde=2.802*m.bse[k]*sd       # 80% power 最小可偵測（標準化後）
    res.append((v,lab,m.params[k],beta_sd,m.bse[k],m.pvalues[k],mde,len(t)))
qs=multipletests([r[5] for r in res],method='fdr_bh')[1]
for r,q in zip(res,qs):
    print('%-12s 交互 β=%+8.4f (每1SD %+.4f SD) p=%.4f q=%.3f  最小可偵測 %.3f SD  N=%d %s'%(
        r[0],r[2],r[3],r[5],q,r[6],r[7],'✔' if q<.05 else ''))
print('\n  提醒：主效果本身僅 %.3f SD；上列最小可偵測交互作用若大於此值，陰性只能解讀為「偵測不到大的調節」。'%abs(B0))

print('\n'+'='*100)
print('步驟 5：這四類是否能解釋「反向路徑」（認知 M2 → 便祕 M3）')
print('-'*100)
rv=d[d.B3TCOMPZ1.notna()&d.C1SA11K.notna()].copy()
rv['newcon']=(rv.C1SA11K==1).astype(float)
RCOV=['age','female','edu','bmi','chron27','depre','rxmed']
def rev(extra,label,dropv=[]):
    sub=RCOV+['B3TCOMPZ1','newcon','B1SA11K']+dropv
    t=rv.dropna(subset=sub).copy()
    t=t[t.B1SA11K==2]     # 限定 M2 時無便祕者 → 新發
    f0='newcon ~ B3TCOMPZ1 + age + female + edu + bmi + chron27 + depre + rxmed'
    m=smf.probit(f0+extra,data=t).fit(disp=0,cov_type='cluster',cov_kwds={'groups':t.M2FAMNUM})
    print('%-34s N=%4d 新發=%3d  認知 β=%+7.4f p=%.4f'%(
        label,len(t),int(t.newcon.sum()),m.params['B3TCOMPZ1'],m.pvalues['B3TCOMPZ1']))
    return m.params['B3TCOMPZ1']
b_ref=rev('','基準（既有共變項）')
rev(' + sleep_ins','＋M2 失眠症狀',['sleep_ins'])
rev(' + anx_cidi + panic + neuro','＋M2 焦慮整組',['anx_cidi','panic','neuro'])
rev(' + negaf','＋M2 負向情緒',['negaf'])
rev(' + stress_idx','＋M2 長期壓力指數',S4)
rev(' + sleep_ins + anx_cidi + negaf + stress_idx','＋四類整組',['sleep_ins','anx_cidi','negaf','stress_idx'])

print('\n'+'='*100)
print('步驟 6：共線性（VIF）')
print('-'*100)
vv=['age','edu','bmi','chron27','depre','rxmed','sleep_ins','sleep_hr','anx_cidi','panic','neuro','negaf','stress_idx','str_kin','str_fri','str_bill','str_disc']
t=BASE.dropna(subset=vv)
X=sm.add_constant(t[vv])
for i,c in enumerate(X.columns):
    if c=='const': continue
    print('  %-12s VIF=%.2f'%(c,variance_inflation_factor(X.values,i)))
print('\n  因素間相關矩陣（Pearson）')
print(BASE[['sleep_ins','anx_cidi','panic','neuro','depre','negaf','stress_idx']].corr().round(3).to_string())
