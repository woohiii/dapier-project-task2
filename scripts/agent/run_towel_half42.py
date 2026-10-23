"""B안 단일 ACT(act_half42_gate28_grasp28, 65000 step)를 10/23 lim12 실물 평가와 같은 조건으로 실행하고,
최종 화면을 검증기로 판정한다(NOMI fold_towel용).

10/23 평가(~/towel_eval_logs/run_act_eval_half42.sh, LIMIT_DEG=12)와 같은 프로그램·인자다:
run_act_towel_bimanual_wide.py --limit-deg 12(모터 가드 17°), 30Hz 설정, 150초, Enter 시작/정지. 10회 중 8회 대문접기까지 성공.
가상 터미널·정지 스냅샷·검증기 판정은 run_towel_act70_v3.py와 같다(그 파일은 수정하지 않고 final_rgb를 가져다 쓴다).

    uv run --project ~/lerobot python run_towel_half42.py --output-dir outputs/half42_run
"""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

from run_towel_act70_v3 import HERE, LEROBOT, final_rgb

CHECKPOINT = "outputs/train/act_half42_gate28_grasp28/checkpoints/065000/pretrained_model"
HALF42_ARGS = [
    "--limit-deg", "12",
    "--checkpoint", CHECKPOINT,
    # 학습 데이터셋의 로컬 메타(허브 접속 불필요)
    "--dataset-repo", "local/towel_tape_70_half42_gate28_grasp28",
    "--dataset-root", str(LEROBOT / "outputs/datasets/towel_tape_70_half42_gate28_grasp28"),
    "--task", "Fold the towel in half, then gate-fold it",
    "--execute", "--max-steps", "0", "--control-hz", "30", "--operator-stop", "--duration-s", "150",
]


def fold_command(out: Path) -> list[str]:
    return [sys.executable, str(HERE / "run_act_towel_bimanual_wide.py"), *HALF42_ARGS,
            "--trace-dir", str(out / "trace"), "--result-json", str(out / "result.json"),
            "--stop-snapshot-dir", str(out / "stop")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if not (LEROBOT / CHECKPOINT / "model.safetensors").exists():
        raise SystemExit(f"체크포인트 없음: {LEROBOT / CHECKPOINT}")
    out = args.output_dir.resolve()
    out.mkdir(parents=True)
    cmd = fold_command(out)
    (out / "command.txt").write_text(shlex.join(cmd) + "\n")
    # -q 안내문 없음, -e 자식 종료 코드 전달, -f 출력 즉시 기록. stdin(파이프)은 가상 터미널로 전달된다.
    code = subprocess.run(["script", "-qefc", shlex.join(cmd), "/dev/null"], cwd=LEROBOT).returncode

    sys.path.insert(0, str(LEROBOT / "custom_scripts"))
    from towel_verifier import classify_rgb

    rgb = final_rgb(out)
    got = classify_rgb(rgb) if rgb is not None else "no_snapshot"
    ok = got == "book_fold"
    print(f"검증기[full]: {got} (기대 book_fold) -> {'합격' if ok else '불합격'} (정책 종료 코드 {code})", flush=True)
    with (out / "verify.jsonl").open("a") as stream:
        stream.write(json.dumps({"stage": "full", "expected": "book_fold", "got": got, "ok": ok}) + "\n")
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
