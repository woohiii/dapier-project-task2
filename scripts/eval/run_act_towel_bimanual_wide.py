#!/usr/bin/env python
"""run_act_towel_bimanual_lim9.py를 그대로 실행하되 관절 제한각만 넓힌다 (lim9 파일은 수정하지 않음).

수건을 끌고 올 때 팔이 늦으면 목표가 "현재 ±9°"(정책 제한)와 "현재 ±10°"(팔로워 모터 가드)에 잘려
끄는 힘에 상한이 생긴다. 여기서는 두 제한을 함께 올린다.
- 정책 제한: --limit-deg (기본 15°)
- waypoint 분할: 같은 값 → 스텝당 한 번에 전송 (분할하면 내부 sleep이 늘어 루프가 다시 느려짐)
- 팔로워 모터 가드: limit + 5° (관측이 모터 값보다 몇 도 늦을 수 있어 여유를 둠)

사용 (lim9와 같은 옵션 + --limit-deg):
    cd ~/lerobot
    uv run python ~/so101-bimanual-teleop/run_act_towel_bimanual_wide.py --limit-deg 15 <lim9 옵션들>
"""

from __future__ import annotations

import sys

import run_act_towel_bimanual_lim9 as lim9

GUARD_MARGIN_DEG = 5.0


def apply_limits(limit_deg: float) -> float:
    """lim9의 정책 제한·waypoint 크기와 팔로워 모터 가드를 바꾸고, 적용된 모터 가드 값을 돌려준다."""
    import record_bimanual_with_depth

    bound, plan = lim9.bound_policy_target, lim9.plan_guarded_waypoints
    lim9.bound_policy_target = lambda current, target: bound(current, target, max_delta_deg=limit_deg)
    lim9.plan_guarded_waypoints = lambda current, target: plan(current, target, max_delta_deg=limit_deg)
    lim9.MAX_POLICY_RELATIVE_DEG = lim9.MAX_PLANNED_STEP_DEG = limit_deg
    # build_devices()가 호출 시점에 이 전역값을 읽어 SOFollowerConfig.max_relative_target에 넣는다
    record_bimanual_with_depth.MAX_RELATIVE_TARGET = limit_deg + GUARD_MARGIN_DEG
    return record_bimanual_with_depth.MAX_RELATIVE_TARGET


def pop_limit(argv: list[str]) -> tuple[float, list[str]]:
    """--limit-deg 값을 꺼내고 나머지 인자는 lim9에 넘긴다."""
    if "--limit-deg" not in argv:
        return 15.0, argv
    i = argv.index("--limit-deg")
    return float(argv[i + 1]), argv[:i] + argv[i + 2:]


if __name__ == "__main__":
    limit, sys.argv = pop_limit(sys.argv)
    if not 9.0 <= limit <= 20.0:
        raise SystemExit("--limit-deg must be between 9 and 20")
    guard = apply_limits(limit)
    print(f"WIDE LIMITS: policy={limit:.1f}deg waypoint={limit:.1f}deg follower_guard={guard:.1f}deg", flush=True)
    raise SystemExit(lim9.main())
