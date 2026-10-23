#!/bin/bash
# B안 단일 모델(act_half42_gate28_grasp28, 65000 step) 실물 평가. 70개 lim15 시험(act_wide_full70_1023_lim15)과 같은 조건:
#   관절 제한 LIMIT_DEG=15°(모터 가드 20°, LIMIT_DEG=12로 바꿀 수 있음), --control-hz 30(실제 약 28Hz), 150초, Enter 정지.
# 5회씩 두 번 나눠 평가: 한 번 실행하면 최대 5회 하고 멈춘다. 다시 실행하면 같은 폴더에 이어서 6~10회.
# 사용법: [LIMIT_DEG=15] run_act_eval_half42.sh [결과폴더=act_half42_<날짜>_lim<LIMIT_DEG>]
# 시행이 끝날 때마다 results.csv에 바로 저장. Ctrl+C: 실행 중이던 시행만 멈추고 결과를 입력받는다
cd ~/lerobot
LIMIT_DEG=${LIMIT_DEG:-15}; DIR=${1:-~/towel_eval_logs/act_half42_$(date +%m%d)_lim$LIMIT_DEG}; TOTAL=10; BATCH=5
CKPT=outputs/train/act_half42_gate28_grasp28/checkpoints/065000/pretrained_model
REPO=local/towel_tape_70_half42_gate28_grasp28; ROOT=outputs/datasets/towel_tape_70_half42_gate28_grasp28  # 로컬 메타
[ -f $CKPT/model.safetensors ] || { echo "체크포인트 없음: $CKPT (rsync가 끝났는지 확인)"; exit 1; }
if pgrep -f "async_inference.robot_client" >/dev/null; then echo "robot_client(그루트)가 실행 중입니다. 먼저 종료하세요."; exit 1; fi
DIR=${DIR%/}; mkdir -p "$DIR"; CSV=$DIR/results.csv
[ -f "$CSV" ] || echo "trial,outcome,note,time" > "$CSV"
summary() {
  echo "=== 요약 ($CSV) ==="
  tail -n +2 "$CSV" | cut -d, -f2 | sort | uniq -c
  n=$(tail -n +2 "$CSV" | wc -l); f=$(grep -c ",full_success," "$CSV"); h=$(grep -cE ",(half_only|right_gate|full_success)," "$CSV")
  echo "시행 $n/$TOTAL회 / 반접기 성공 $h / 대문접기까지 성공 $f"
}
trap summary EXIT
INT=0; trap 'INT=1' INT          # Ctrl+C로 스크립트가 즉시 죽지 않게 하고, 정책 프로그램만 멈추게 한다
n=$(tail -n +2 "$CSV" | wc -l); STOP=$(( n + BATCH < TOTAL ? n + BATCH : TOTAL ))
echo "시작: $DIR (제한 ${LIMIT_DEG}°) (기존 $n회, 이번 묶음 $((n + 1))~$STOP회) | 시행 중 Ctrl+C=이번 시행만 멈춤 | 종료는 Enter 대기 중 q"
echo "메모 권장: 반접기 변 정렬 ○/△/✕, 왼쪽 휨, 잡은 뒤 멈춤, 반접기→대문접기 전환 멈춤"
while [ "$n" -lt "$STOP" ] && [ $INT -eq 0 ]; do
  i=$(printf %02d $((n + 1)))
  read -rp "[$i/$TOTAL] 수건을 놓고 팔 주변을 비운 뒤 Enter (q=저장하고 종료): " a || break
  [ "$a" = "q" ] && break
  [ -e "$DIR/trial_$i" ] && mv "$DIR/trial_$i" "$DIR/trial_$i.discarded_$(date +%H%M%S)"
  uv run python ~/so101-bimanual-teleop/run_act_towel_bimanual_wide.py --limit-deg $LIMIT_DEG \
    --checkpoint $CKPT \
    --dataset-repo $REPO --dataset-root $ROOT \
    --task "Fold the towel in half, then gate-fold it" \
    --execute --max-steps 0 --control-hz 30 --operator-stop --duration-s 150 \
    --trace-dir "$DIR/trial_$i/trace" --result-json "$DIR/trial_$i/result.json" 2>&1 | tee -i "$DIR/trial_$i.log"
  INT=0   # Ctrl+C는 이번 시행만 멈추게 하고, 결과 입력 후 다음 시행으로 계속 진행한다
  while true; do
    read -rp "[$i/$TOTAL] 결과  1=반접기만  5=오른쪽 대문접기까지  2=대문접기까지 성공  3=잡았지만 못 접음  4=못 잡음  s=이번 시행 버리기 : " r || { echo; echo "(Ctrl+C 무시: 1~5 또는 s 입력)"; continue; }
    case "$r" in
      1) o=half_only;; 5) o=right_gate;; 2) o=full_success;; 3) o=grasp_fold_fail;; 4) o=no_grasp;; s) o=;; *) echo "1~5 또는 s 입력"; continue;;
    esac
    break
  done
  [ -z "$o" ] && { echo "시행 $i 버림 (기록 안 함)"; continue; }
  read -rp "메모(없으면 Enter): " note || note=
  echo "$i,$o,\"${note//,/ }\",$(date +%T)" >> "$CSV"
  n=$((n + 1))
done
[ "$n" -ge "$STOP" ] && [ "$n" -lt "$TOTAL" ] && echo "이번 묶음 끝 ($n/$TOTAL). 다음 5회: 같은 명령을 다시 실행 (같은 날이면 폴더 자동 이어짐)"
