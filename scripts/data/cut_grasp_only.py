"""반접기가 별로였던 28개(bad)에서 '두 손 집기'까지만 잘라 B안 데이터셋에 더한다.

집기 시연은 70개 모두 쓰고, 끌기·놓기는 좋은 42개만 배우게 한다.
구간: 반접기 시작 ~ 두 손 모두 그리퍼를 닫은 시점 + MARGIN 프레임 (손이 실제로 다 닫히는 시간 여유).
ACT는 구간 끝 이후 동작을 패딩 마스크로 학습에서 뺀다.

순서:
    1) 자르기:  uv run python custom_scripts/cut_grasp_only.py
    2) 합치기:  uv run python custom_scripts/cut_grasp_only.py --merge   (build_half42_gate_mix.py 완료 후)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from build_half42_gate_mix import FULL, HF, OUT as B_OUT, OUT_REPO as B_REPO, SELECTION
from compare_half_fold_groups import BOUNDARIES, FPS, episode_metrics, load_actions
from duplicate_towel_dataset import DERIVED_FEATURES, frame_for_writer

from lerobot.datasets.dataset_tools import merge_datasets
from lerobot.datasets.lerobot_dataset import LeRobotDataset

GRASP_REPO = "local/towel_tape_70_grasp28"
GRASP_OUT = Path("outputs/datasets/towel_tape_70_grasp28")
FINAL_REPO = "local/towel_tape_70_half42_gate28_grasp28"
FINAL_OUT = Path("outputs/datasets/towel_tape_70_half42_gate28_grasp28")
TASK = "Fold the towel in half, then gate-fold it"  # 원본 전체 에피소드와 같은 태스크
MARGIN = 15
REGRASP_S = 2.0  # 이 안에 다시 열면 첫 집기 실패로 본다
REOPEN_DEG = 20.0
CLOSED_DEG = 6.0


def regrasp_end(half, grasp_end: int) -> int:
    """집기 직후 REGRASP_S 안에 그리퍼를 다시 열면(첫 집기 실패) 다시 닫은 프레임까지 늘린다.

    ep9, 20, 28, 54, 62, 64: 오른손이 닫힌 뒤 0.5~1.4초 만에 다시 열고 4~5초 뒤 다시 잡는다.
    보통의 놓기(끌기 끝, 7초 이상 뒤)와는 시간으로 구분한다.
    """
    end = grasp_end
    for gripper in (5, 11):
        # 집기 시각은 '절반 닫힘' 기준이라 아직 닫히는 중일 수 있다: 완전히 닫힌 뒤부터 다시 여는지 본다
        shut = np.flatnonzero(half[grasp_end:, gripper] < CLOSED_DEG)
        if not shut.size:
            continue
        start = grasp_end + int(shut[0])
        after = half[start:, gripper]
        reopen = np.flatnonzero(after[:round(REGRASP_S * FPS)] > REOPEN_DEG)
        if reopen.size:
            closed = np.flatnonzero(after[reopen[0]:] < CLOSED_DEG)
            if closed.size:
                end = max(end, start + int(reopen[0] + closed[0]))
    return end


def grasp_segments() -> dict[int, tuple[int, int]]:
    """bad 에피소드마다 (시작, 두 손 집기 완료 + MARGIN) 프레임 (원본 에피소드 기준)."""
    selection = json.loads(SELECTION.read_text())
    bad = sorted(int(k) for k, v in selection.items() if v == "bad")
    samples = {s["source_episode"]: s for s in json.loads(BOUNDARIES.read_text())["samples"]}
    actions = load_actions(HF / FULL)
    segments = {}
    for ep in bad:
        s = samples[ep]
        m = episode_metrics(actions[ep][s["start"]:s["end"]])
        if m is None:
            raise ValueError(f"ep{ep}: 집기를 찾지 못함")
        grasp_end = round(max(m["left"]["grasp_s"], m["right"]["grasp_s"]) * FPS)
        grasp_end = regrasp_end(actions[ep][s["start"]:s["end"]], grasp_end)
        segments[ep] = (s["start"], min(s["start"] + grasp_end + MARGIN, s["end"]))
    return segments


def cut() -> None:
    if GRASP_OUT.exists():
        raise FileExistsError(GRASP_OUT)
    segments = grasp_segments()
    source = LeRobotDataset(FULL, root=HF / FULL, return_uint8=True, tolerance_s=1e-3)
    offsets = {int(e["episode_index"]): int(e["dataset_from_index"]) for e in source.meta.episodes}
    features = {k: v for k, v in source.meta.features.items() if k not in DERIVED_FEATURES}
    output = LeRobotDataset.create(repo_id=GRASP_REPO, root=GRASP_OUT, fps=source.fps, features=features,
                                   robot_type=source.meta.robot_type, use_videos=True, batch_encoding_size=1)
    try:
        for ep, (start, end) in segments.items():
            for offset in range(start, end):
                output.add_frame(frame_for_writer(source[offsets[ep] + offset], set(features)) | {"task": TASK})
            output.save_episode()
            print(f"ep{ep} frames {start}:{end} ({end - start})", flush=True)
    finally:
        output.finalize()
    (GRASP_OUT / "source_segments.json").write_text(json.dumps({str(k): v for k, v in segments.items()}, indent=2))
    print(f"저장: {GRASP_OUT} ({len(segments)}개, {sum(e - s for s, e in segments.values())}프레임)")


def merge() -> None:
    if FINAL_OUT.exists():
        raise FileExistsError(FINAL_OUT)
    b = LeRobotDataset(B_REPO, root=B_OUT)
    g = LeRobotDataset(GRASP_REPO, root=GRASP_OUT)
    merged = merge_datasets([b, g], output_repo_id=FINAL_REPO, output_dir=FINAL_OUT)
    expected = (b.meta.total_episodes + g.meta.total_episodes, b.meta.total_frames + g.meta.total_frames)
    if (merged.meta.total_episodes, merged.meta.total_frames) != expected:
        raise RuntimeError(f"검증 실패: {merged.meta.total_episodes}개 {merged.meta.total_frames}프레임, 기대 {expected}")
    mapping = json.loads((B_OUT / "source_mapping.json").read_text())
    mapping["grasp_only_episodes"] = json.loads((GRASP_OUT / "source_segments.json").read_text())
    (FINAL_OUT / "source_mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")
    print(f"완료: {FINAL_OUT} ({expected[0]}개, {expected[1]}프레임)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--merge", action="store_true")
    merge() if parser.parse_args().merge else cut()
