# 3. 학습

## 설정

| 항목 | 값 |
|---|---|
| 정책 | ACT (LeRobot `--policy.type=act`) |
| 비전 백본 | ResNet18 |
| 입력 | 관절 12개 + 이미지 4개 (왼/오 손목, Astra RGB, Astra 뎁스 시각화) |
| 청크 크기 | 100 스텝 (`n_action_steps` 100, temporal ensemble 없음) |
| 모델 | dim 512, 인코더 4층, 디코더 1층, VAE 사용(kl_weight 10), dropout 0.1 |
| 배치 · 학습률 | 8 · 1e-5 (백본도 1e-5) |
| 스텝 | 65,000 = 104,011프레임 / 8 × 5 epoch |
| 시드 | 42 |
| 장비 | RTX 4090 1대 |
| 학습 시간 | 약 1시간 38분 (1만 스텝당 약 15분, 초당 약 11스텝) |

epoch 수는 앞선 두 모델(50개, 70개) 사이의 중간값으로 정했습니다. 전체 설정은 [`results/act_policy_config.json`](../results/act_policy_config.json)과 [`results/act_train_config.json`](../results/act_train_config.json)에 있습니다.

## 실행

[`scripts/train/train_half42.sh`](../scripts/train/train_half42.sh)에 데이터 복사, 학습, 체크포인트 받기 순서가 모두 들어 있습니다. 평가에는 마지막 체크포인트 `checkpoints/065000/pretrained_model`을 썼습니다.

주의: `rsync`는 받을 경로의 마지막 폴더 하나만 만듭니다. `outputs/train/<job>/checkpoints/`처럼 중간 폴더가 없으면 `mkdir failed` 오류가 나므로 먼저 `mkdir -p`를 해야 합니다.
