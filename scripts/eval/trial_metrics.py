"""평가 폴더(results.csv + trial_*/trace/actions.jsonl)에서 시행별 지표를 계산한다.

    cd ~/towel_eval_logs && python trial_metrics.py trial_metrics.json
지표: 소요시간(작업자 정지까지), 실제 루프 Hz, 왼/오 집기·놓기 시각, 관절속도 p95/최대, 오른손 집기 순간 자세.
"""
import json,glob,sys,numpy as np,csv
out={}
def closes(g,t):
    """그리퍼 열림(>20) 뒤 처음 닫힘(<10) 시각과 그 뒤 다시 열림(>20) 시각"""
    o=np.flatnonzero(g>20)
    if not o.size: return None,None
    c=np.flatnonzero((g<10)&(np.arange(len(g))>o[0]))
    if not c.size: return None,None
    r=np.flatnonzero((g>20)&(np.arange(len(g))>c[0]))
    return float(t[c[0]]), (float(t[r[0]]) if r.size else None)
for name in ["act_half42_1023_lim15","act_half42_1023_lim12","act_half42_1023_lim12_far","act_wide_full70_1023_lim12","act_wide_full70_1023_lim15"]:
    res=list(csv.DictReader(open(f"{name}/results.csv")))
    trials=[]
    for r in res:
        p=f"{name}/trial_{r['trial']}/trace/actions.jsonl"
        try: rows=[json.loads(l) for l in open(p)]
        except FileNotFoundError: trials.append(dict(r)); continue
        t=np.array([x["elapsed_s"] for x in rows]); cur=np.array([x["current_deg"] for x in rows])
        dt=np.diff(t); hz=1/np.median(dt)
        vel=np.abs(np.diff(cur[:,[0,1,2,3,4,6,7,8,9,10]],axis=0))/dt[:,None]
        lc,lr=closes(cur[:,5],t); rc,rr=closes(cur[:,11],t)
        trials.append(dict(r, dur=round(float(t[-1]),1), steps=len(t), hz=round(float(len(t)/t[-1]),1),
            l_grasp=lc and round(lc,1), r_grasp=rc and round(rc,1), l_rel=lr and round(lr,1), r_rel=rr and round(rr,1),
            vel_p95=round(float(np.percentile(vel,95)),1), vel_max=round(float(vel.max()),1),
            r_pose=[round(float(v),1) for v in cur[np.searchsorted(t,rc) if rc else -1,6:9]]))
    out[name]=trials
json.dump(out,open(sys.argv[1] if len(sys.argv)>1 else "trial_metrics.json","w"),ensure_ascii=False,indent=1)
for k,v in out.items():
    print("==",k)
    for x in v: print({a:x.get(a) for a in ['trial','outcome','dur','hz','l_grasp','r_grasp','l_rel','r_rel','vel_p95','vel_max','r_pose']})
