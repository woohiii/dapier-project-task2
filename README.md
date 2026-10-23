# 다피어 프로젝트 태스크 2: SO-101 양팔 수건 접기 (B안 단일 ACT)

SO-101 양팔 로봇이 펼친 수건을 **반접기 → 대문접기**까지 한 번에 접는 ACT 모방학습 정책입니다. 시연 데이터를 단계별로 골라 다시 구성(B안)한 뒤, 모델 하나로 학습했습니다. 실물 평가에서 **10회 중 8회 대문접기까지 성공**했습니다(관절 제한 12°).

- **결과 보고서 (그래프):** https://claude.ai/artifact/HeEQYUe4Gk3qFpaMjXTgHa
- 같은 보고서 파일: [`report/towel_half42_eval_1023.html`](report/towel_half42_eval_1023.html). GitHub에서는 소스로 보이니 내려받아 브라우저로 여세요.
- 이전 작업(태스크 1, 70개 통 학습): [woohiii/dapier-task1-towel-folding](https://github.com/woohiii/dapier-task1-towel-folding)

## 한눈에 보기

| 조건 | 대문접기까지 성공 |
|---|---|
| **B안 lim12** | **8 / 10** |
| B안 lim15 | 7 / 10 |
| B안 lim12, 트롤리를 멀리 둠 | 1 / 10 |
| 70개 통 모델 lim12 (참고) | 4 / 5 |
| 70개 통 모델 lim15 (참고) | 3 / 5 |

## 진행 순서 (문서)

| 단계 | 문서 | 내용 |
|---|---|---|
| 1 | [데이터 수집](docs/01_data_collection.md) | 장비, 카메라 4대, L자 테이프 기준, 50개 + 추가 20개 시연, 단계 경계 |
| 2 | [데이터 분석과 재구성](docs/02_data_curation.md) | 50개 대 20개 비교, 반접기 42개 웹 판정, 분할 실행을 버린 이유, B안 98개 구성 |
| 3 | [학습](docs/03_training.md) | ACT 설정, 65,000 step(5 epoch), RTX 4090 약 1시간 38분 |
| 4 | [실물 평가](docs/04_evaluation.md) | 관절 제한 확대(lim12/15), 평가 절차, 결과, 시간 분석, 먼 거리 실패 원인 |

## 폴더 구성

```
docs/        단계별 문서 + 그림
report/      실물 평가 보고서 (HTML)
results/     평가 결과표(csv), 시행별 지표, 반접기 판정, 단계 경계, 데이터 구성 매핑, 학습 설정
scripts/
  data/      50/20 비교, 반접기 판정 웹, B안 데이터셋 생성, 집기 구간 자르기
  train/     서버 학습 명령
  eval/      관절 제한 확대 추론 래퍼, 평가 스크립트, 지표·자세 분석
```

## 실행 환경과 의존성

- 이 저장소의 스크립트는 다음 두 작업 폴더에 놓고 실행하는 것을 전제로 합니다.
  - `scripts/data/*` → `~/lerobot/custom_scripts/`
  - `scripts/eval/*.py` → `~/so101-bimanual-teleop/`
- 기존 모듈을 import해서 씁니다. `duplicate_towel_dataset.py`, `serve_towel_boundary_review.py`는 lerobot의 custom_scripts에 있고, `run_act_towel_bimanual_lim9.py`, `record_bimanual_with_depth.py`는 [so101-bimanual-teleop](https://github.com/woohiii/so101-bimanual-teleop) 작업본에 있습니다.
- LeRobot([huggingface/lerobot](https://github.com/huggingface/lerobot)), Python 3.12, `uv`가 필요합니다. 실물 실행에는 Astra 뎁스 워치독이 필요합니다.
- 데이터셋(약 2.9GB)과 체크포인트(약 200MB)는 용량 때문에 넣지 않았습니다.

## 검증

```bash
# 결과표 집계 (README 표와 같아야 함)
for f in results/act_*.csv; do echo "$(basename $f .csv): $(tail -n +2 $f | cut -d, -f2 | sort | uniq -c | tr '\n' ' ')"; done
```
