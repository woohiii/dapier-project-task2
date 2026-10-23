"""B안 데이터셋: 반접기가 완벽한 42개는 전체 에피소드, 나머지 28개는 대문접기 구간만 합쳐 모델 하나로 학습한다.

- 전체: Woohi123/towel_tape_halffold_gatefold_80_v4 에서 선택(good) 에피소드만 남김
- 대문접기 구간: Woohi123/towel_tape_halffold_gatefold_80_v4_stage_gate_fold 에서 제외(bad) 에피소드만 남김
  (구간 데이터셋 ep i = 원본 ep i의 [반접기 끝:] 임을 state로 확인함, 70/70 일치)
- 선택: outputs/review/towel_half_fold_select/selection.json (웹 선택 결과)

Usage:
    uv run python custom_scripts/build_half42_gate_mix.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from lerobot.datasets.dataset_tools import delete_episodes, merge_datasets
from lerobot.datasets.lerobot_dataset import LeRobotDataset

HF = Path.home() / ".cache/huggingface/lerobot"
FULL = "Woohi123/towel_tape_halffold_gatefold_80_v4"
GATE = "Woohi123/towel_tape_halffold_gatefold_80_v4_stage_gate_fold"
SELECTION = Path("outputs/review/towel_half_fold_select/selection.json")
OUT_REPO = "local/towel_tape_70_half42_full_gate28"
OUT = Path("outputs/datasets/towel_tape_70_half42_full_gate28")
WORK = Path("outputs/datasets/_build_half42_gate28")


def main() -> None:
    selection = json.loads(SELECTION.read_text())
    good = sorted(int(k) for k, v in selection.items() if v == "good")
    bad = sorted(int(k) for k, v in selection.items() if v == "bad")
    if sorted(good + bad) != list(range(70)):
        raise ValueError("70개 모두 good/bad로 판정되어야 합니다")
    if OUT.exists():
        raise FileExistsError(OUT)
    shutil.rmtree(WORK, ignore_errors=True)  # 이전에 중단된 중간 결과만 지운다

    full = LeRobotDataset(FULL, root=HF / FULL)
    gate = LeRobotDataset(GATE, root=HF / GATE)
    full_good = delete_episodes(full, bad, output_dir=WORK / "full_good", repo_id="local/full_good")
    gate_bad = delete_episodes(gate, good, output_dir=WORK / "gate_bad", repo_id="local/gate_bad")
    merged = merge_datasets([full_good, gate_bad], output_repo_id=OUT_REPO, output_dir=OUT)

    expected_frames = sum(full.meta.episodes[e]["length"] for e in good) + sum(
        gate.meta.episodes[e]["length"] for e in bad)
    if (merged.meta.total_episodes, merged.meta.total_frames) != (70, expected_frames):
        raise RuntimeError(f"검증 실패: {merged.meta.total_episodes}개 {merged.meta.total_frames}프레임, "
                           f"기대 70개 {expected_frames}프레임")
    # 새 순서: 0~41 = good 전체(원본 번호 순), 42~69 = bad 대문접기 구간
    mapping = {"full_episodes": good, "gate_only_episodes": bad}
    (OUT / "source_mapping.json").write_text(json.dumps(mapping, indent=2) + "\n")
    shutil.rmtree(WORK)
    print(f"완료: {OUT} ({merged.meta.total_episodes}개, {merged.meta.total_frames}프레임)")


if __name__ == "__main__":
    main()
