from pathlib import Path

import run_towel_half42 as half42


def test_fold_command_matches_lim12_eval():
    cmd = half42.fold_command(Path("/tmp/run"))
    assert cmd[1].endswith("run_act_towel_bimanual_wide.py")
    assert cmd[cmd.index("--limit-deg") + 1] == "12"
    assert cmd[cmd.index("--control-hz") + 1] == "30"
    assert "--temporal-ensemble" not in cmd  # 평가 때 쓰지 않았다
    assert cmd[cmd.index("--stop-snapshot-dir") + 1] == "/tmp/run/stop"
    assert (half42.LEROBOT / half42.CHECKPOINT / "model.safetensors").exists()
    assert (Path(cmd[cmd.index("--dataset-root") + 1]) / "meta/info.json").exists()
