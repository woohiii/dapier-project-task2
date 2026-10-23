"""오른손 그리퍼가 닫힌 순간의 오른팔 관절값(성공/실패 비교).

    cd ~/towel_eval_logs && python right_grasp_pose.py act_half42_1023_lim12 act_half42_1023_lim12_far
"""
import json,sys,glob,numpy as np
for d in sys.argv[1:]:
    res={l.split(',')[0]:l.split(',')[1] for l in open(f"{d}/results.csv").read().split('\n')[1:] if l}
    for t in sorted(glob.glob(f"{d}/trial_??/trace/actions.jsonl")):
        tid=t.split('trial_')[1][:2]
        rows=[json.loads(l) for l in open(t)]
        cur=np.array([r["current_deg"] for r in rows]); tgt=np.array([r["raw_target_deg"] for r in rows])
        g=cur[:,11]; opened=np.flatnonzero(g>20)
        if not opened.size: print(d.split('_')[-1],tid,res.get(tid),"오른손 안 열림"); continue
        cl=np.flatnonzero((g<10)&(np.arange(len(g))>opened[0]))
        k=cl[0] if cl.size else len(g)-1
        lag=np.abs(tgt[:k+1,6:11]-cur[:k+1,6:11]).max(0)
        print(f"{d.split('1023_')[-1]:10s} {tid} {res.get(tid,'-'):14s} close@{k:4d} R pan/lift/elbow/flex/roll={np.round(cur[k,6:11],1)} 목표-현재 최대={np.round(lag,1)}")
