"""반접기 시연 비교: 원래 50개(80_v4 ep0~49) vs 추가 20개(ep50~69). 하드웨어 구동 없음.

80_v4의 ep0~49는 50_v3와 같은 녹화다(앞 400프레임 state 일치 확인).
반접기 구간은 검토 경계(outputs/datasets/towel_tape_70_stage_half_fold/reviewed_stage_source.json)를 쓴다.
팔마다 집기(그리퍼 닫힘)~놓기(열림) 구간을 찾아 시간·자세·경로를 비교한다.

Usage:
    uv run python custom_scripts/compare_half_fold_groups.py
    → outputs/half_fold_compare/{carry_paths.png, summary.json} 와 표 출력
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from towel_mirror import JOINTS, _resample, carry_segment, load_actions

SOURCE_ROOT = Path.home() / ".cache/huggingface/lerobot/Woohi123/towel_tape_halffold_gatefold_80_v4"
BOUNDARIES = Path("outputs/datasets/towel_tape_70_stage_half_fold/reviewed_stage_source.json")
OUTPUT_DIR = Path("outputs/half_fold_compare")
FPS = 30
FIRST_NEW_EPISODE = 50
ARMS = {"left": 0, "right": 6}


def episode_metrics(half: np.ndarray) -> dict | None:
    """반접기 구간 하나의 팔별 집기/놓기 시각, 집기·놓기 자세, 이동 경로(시간 정규화)."""
    out = {"duration_s": len(half) / FPS}
    for arm, o in ARMS.items():
        carry = carry_segment(half[:, o + 5])
        if carry is None:
            return None
        seg = half[carry, o:o + 6]
        out[arm] = {
            "grasp_s": carry.start / FPS,
            "carry_s": (carry.stop - carry.start) / FPS,
            "grasp_pose": half[carry.start, o:o + 5],
            "release_pose": half[min(carry.stop, len(half) - 1), o:o + 5],
            "grip_closed": float(np.median(seg[:, 5])),
            "peak_speed": float(np.abs(np.diff(seg[:, :5], axis=0)).max(initial=0) * FPS),
            "path": _resample(seg[:, :5]),
        }
    out["grasp_gap_s"] = abs(out["left"]["grasp_s"] - out["right"]["grasp_s"])
    out["release_gap_s"] = abs(out["left"]["grasp_s"] + out["left"]["carry_s"]
                               - out["right"]["grasp_s"] - out["right"]["carry_s"])
    return out


def effect(a, b) -> float:
    """Cohen's d (두 묶음 평균 차 / 합친 표준편차). |d|>0.8이면 큰 차이."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return float((b.mean() - a.mean()) / pooled) if pooled > 1e-9 else 0.0


def main() -> None:
    actions = load_actions(SOURCE_ROOT)
    samples = json.loads(BOUNDARIES.read_text())["samples"]
    groups = {"old50": [], "new20": []}
    skipped = []
    for s in samples:
        ep = s["source_episode"]
        m = episode_metrics(actions[ep][s["start"]:s["end"]])
        if m is None:
            skipped.append(ep)
            continue
        m["episode"] = ep
        groups["new20" if ep >= FIRST_NEW_EPISODE else "old50"].append(m)
    old, new = groups["old50"], groups["new20"]
    print(f"비교: 원래 {len(old)}개 vs 추가 {len(new)}개 (집기/놓기 못 찾아 제외: {skipped})")

    rows = []

    def row(name, get):
        a, b = [get(m) for m in old], [get(m) for m in new]
        rows.append({"metric": name, "old50": float(np.mean(a)), "old50_std": float(np.std(a)),
                     "new20": float(np.mean(b)), "new20_std": float(np.std(b)), "d": effect(a, b)})

    row("반접기 길이(s)", lambda m: m["duration_s"])
    row("두 손 집기 시각 차(s)", lambda m: m["grasp_gap_s"])
    row("두 손 놓기 시각 차(s)", lambda m: m["release_gap_s"])
    for arm in ARMS:
        row(f"{arm} 집기 시각(s)", lambda m, a=arm: m[a]["grasp_s"])
        row(f"{arm} 끌기 시간(s)", lambda m, a=arm: m[a]["carry_s"])
        row(f"{arm} 그리퍼 쥔 값", lambda m, a=arm: m[a]["grip_closed"])
        row(f"{arm} 끌기 최고속도(°/s)", lambda m, a=arm: m[a]["peak_speed"])
        for j, joint in enumerate(JOINTS[:5]):
            row(f"{arm} 집기자세 {joint}", lambda m, a=arm, j=j: m[a]["grasp_pose"][j])
            row(f"{arm} 놓기자세 {joint}", lambda m, a=arm, j=j: m[a]["release_pose"][j])

    print(f"{'항목':28s} {'원래50':>14s} {'추가20':>14s} {'d':>6s}")
    for r in sorted(rows, key=lambda r: -abs(r["d"])):
        flag = " ◀ 큰 차이" if abs(r["d"]) > 0.8 else ""
        print(f"{r['metric']:28s} {r['old50']:7.1f}±{r['old50_std']:<5.1f} {r['new20']:7.1f}±{r['new20_std']:<5.1f}"
              f" {r['d']:+6.2f}{flag}")

    plt.rcParams["font.family"] = "Noto Sans CJK TC"  # 이 PC에 있는 한글 글꼴
    fig, axes = plt.subplots(2, 5, figsize=(20, 7), sharex=True)
    x = np.linspace(0, 100, old[0]["left"]["path"].shape[0])
    for i, arm in enumerate(ARMS):
        for j, joint in enumerate(JOINTS[:5]):
            ax = axes[i, j]
            for name, ms, color in (("원래 50", old, "tab:blue"), ("추가 20", new, "tab:red")):
                p = np.stack([m[arm]["path"][:, j] for m in ms])
                ax.plot(x, p.mean(0), color=color, label=name)
                ax.fill_between(x, p.mean(0) - p.std(0), p.mean(0) + p.std(0), color=color, alpha=0.2)
            ax.set_title(f"{arm} {joint}")
            if i == 1:
                ax.set_xlabel("집기→놓기 (%)")
    axes[0, 0].legend()
    fig.suptitle("반접기 끌기 경로 (평균 ± 표준편차)")
    fig.tight_layout()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_DIR / "carry_paths.png", dpi=90)
    (OUTPUT_DIR / "summary.json").write_text(json.dumps(
        {"old50": len(old), "new20": len(new), "skipped": skipped, "rows": rows}, indent=2, ensure_ascii=False))
    print(f"저장: {OUTPUT_DIR / 'carry_paths.png'}, {OUTPUT_DIR / 'summary.json'}")


if __name__ == "__main__":
    main()
