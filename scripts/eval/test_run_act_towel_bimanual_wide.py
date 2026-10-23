"""넓힌 관절 제한이 lim9 함수와 모터 가드에 실제로 들어가는지 하드웨어 없이 검사."""

import numpy as np

import record_bimanual_with_depth
import run_act_towel_bimanual_lim9 as lim9
from run_act_towel_bimanual_wide import apply_limits, pop_limit


def test_limits_reach_policy_waypoints_and_follower_guard():
    original = (lim9.bound_policy_target, lim9.plan_guarded_waypoints, record_bimanual_with_depth.MAX_RELATIVE_TARGET)
    try:
        assert apply_limits(15.0) == 20.0
        current, target = np.zeros(12), np.full(12, 40.0)
        assert np.allclose(lim9.bound_policy_target(current, target), 15.0)
        waypoints = lim9.plan_guarded_waypoints(current, np.full(12, 15.0))
        assert len(waypoints) == 1  # 한 스텝에 한 번 전송
        assert record_bimanual_with_depth.MAX_RELATIVE_TARGET == 20.0
    finally:
        lim9.bound_policy_target, lim9.plan_guarded_waypoints, record_bimanual_with_depth.MAX_RELATIVE_TARGET = original


def test_pop_limit_strips_own_option():
    assert pop_limit(["x.py", "--limit-deg", "12", "--execute"]) == (12.0, ["x.py", "--execute"])
    assert pop_limit(["x.py", "--execute"]) == (15.0, ["x.py", "--execute"])
