# 5. LLM(NOMI) 연결

음성이나 텍스트 명령을 받으면 LLM이 순서를 정합니다. 수건 작업대로 이동하고, 작업대를 확인하고, 수건을 접은 뒤, 복귀합니다. 이 저장소는 그중 **접기 단계에 B안 lim12를 연결한 부분**만 다룹니다. 에이전트 코드는 별도 저장소 `woohiii/towel-llm-agent`(비공개)에 있습니다.

## 구성

| 부분 | 내용 |
|---|---|
| LLM | Ollama 로컬 Qwen (`qwen3.5:9b`, 프로필 `qwen35_single`) |
| 에이전트 | NOMI (ROS 2 Jazzy) `nomi_agent.agent_node`, 도구 등록·안전 검사·실행 하네스 |
| 웹 콘솔 | `server/towel_console.py` (포트 8090): 음성(Whisper)·텍스트 명령, Astra 스냅샷, 단계 표시, 정지 |
| 작업대 확인 도구 `check_towel_station` | `towel_station.py`: Astra 뎁스로 작업대까지 거리 판정 + 수건이 펼쳐졌는지 판정 (검증기, 파인튜닝한 VLM) |
| 접기 도구 `fold_towel` | **[`scripts/agent/run_towel_half42.py`](../scripts/agent/run_towel_half42.py)** |

## run_towel_half42.py

평가 때(`run_act_eval_half42.sh`, `LIMIT_DEG=12`)와 같은 프로그램과 인자로 정책을 한 번 실행합니다.

- `run_act_towel_bimanual_wide.py --limit-deg 12`, `--control-hz 30`, `--duration-s 150`, `--operator-stop`
- 체크포인트 `act_half42_gate28_grasp28/checkpoints/065000`
- lim9는 `--operator-stop`을 터미널(tty)에서만 허용합니다. 그래서 `script`로 가상 터미널을 붙입니다. stdin 첫 줄이 시작, 다음 줄이 정지입니다.
- 끝나면 정지 스냅샷(없으면 trace 마지막 프레임)을 검증기로 판정합니다. `book_fold`이면 합격이고, 결과를 `verify.jsonl`에 `stage: "full"`로 남깁니다. 에이전트는 이 판정을 보고 성공 여부를 정합니다.

NOMI 쪽에서는 `towel_skill.py`의 `DEFAULT_FOLD_CMD`를 이 래퍼로 바꿨습니다. `NOMI_TOWEL_FOLD_CMD` 환경변수로 덮어쓸 수 있습니다. 변경 후에는 에이전트를 재시작해야 반영됩니다.

```bash
# 확인: 접기 도구가 부르는 명령
cd ~/dapier_project11/ros2_ws/src/nomi_agent && source /opt/ros/jazzy/setup.bash && \
  ~/venvs/nomi/bin/python -c "from nomi_agent.skills.towel_skill import TowelSkill; print(' '.join(TowelSkill().fold_cmd))"
# → uv run --project ~/lerobot python ~/so101-bimanual-teleop/run_towel_half42.py
```
