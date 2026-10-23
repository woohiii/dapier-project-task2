#!/bin/bash
# B안 ACT 학습 (RTX 4090 서버 1대, 약 1시간 38분). 2026-10-23 실제로 실행한 명령과 같다.
# 1) 로컬 → 서버: 데이터셋 복사
#    rsync -avP ~/lerobot/outputs/datasets/towel_tape_70_half42_gate28_grasp28 <user>@<server>:/data/<user>/datasets/
# 2) 서버에서 이 스크립트 실행 (lerobot 저장소 루트)
# 3) 서버 → 로컬: 체크포인트 받기 (받을 폴더를 먼저 만들 것: rsync는 마지막 폴더 하나만 만든다)
#    mkdir -p ~/lerobot/outputs/train/act_half42_gate28_grasp28/checkpoints
#    rsync -avP <user>@<server>:/data/<user>/outputs/act_half42_gate28_grasp28/checkpoints/ ~/lerobot/outputs/train/act_half42_gate28_grasp28/checkpoints/
#
# 5 epoch: 104,011프레임 / 배치 8 = 13,001 step/epoch → 65,000 step
set -e
DATA=${DATA:-/data/$USER/datasets/towel_tape_70_half42_gate28_grasp28}
OUT=${OUT:-/data/$USER/outputs/act_half42_gate28_grasp28}
uv run lerobot-train \
  --dataset.repo_id=local/towel_tape_70_half42_gate28_grasp28 --dataset.root=$DATA \
  --policy.type=act --policy.device=cuda --policy.push_to_hub=false \
  --batch_size=8 --steps=65000 --save_freq=10000 --log_freq=100 --num_workers=4 --seed=42 \
  --output_dir=$OUT --job_name=act_half42_gate28_grasp28 --wandb.enable=false 2>&1 | tee $OUT.log
