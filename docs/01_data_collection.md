# 1. 데이터 수집

## 장비

| 구성 | 내용 |
|---|---|
| 로봇 | SO-101 리더 2대 + 팔로워 2대 (양팔 원격조종) |
| 카메라 | 손목 USB 카메라 2대(왼/오), Orbbec Astra S 1대(위에서 RGB + 뎁스) |
| 기록 주기 | 30 fps |
| 관측 | 관절 12개(팔당 5관절 + 그리퍼), 이미지 4개: `left_wrist`, `right_wrist`, `astra_rgb`, `astra_depth_viz` |
| 행동 | 리더 팔 관절 목표 12개 |
| 수건 위치 기준 | 작업대 위 **검은색 L자 테이프**. 시연 때마다 수건 모서리를 테이프에 맞춰 놓음 |

원격조종·녹화 코드는 [woohiii/so101-bimanual-teleop](https://github.com/woohiii/so101-bimanual-teleop)의 `record_bimanual_with_depth.py`를 썼습니다. Astra S는 OpenNI2 스트림이 가끔 멈추는 문제가 있어서, 워치독 프로세스(`run_astra_depth_watchdog.sh`)가 뎁스를 `/tmp/vsp_astra_depth_mm.npy`로 내보내고 멈추면 장치를 다시 엽니다. 녹화와 추론 모두 이 파일을 읽으므로 **워치독이 꺼져 있으면 `No fresh Astra depth data` 오류로 멈춥니다.**

## 태스크

`"Fold the towel in half, then gate-fold it"`: 펼친 수건을 두 손으로 반으로 접고(반접기), 이어서 양쪽을 가운데로 접습니다(대문접기). 한 에피소드에 두 단계가 모두 들어 있습니다.

## 수집한 데이터셋

| 데이터셋 | 에피소드 | 프레임 | 비고 |
|---|---|---|---|
| `Woohi123/towel_tape_halffold_gatefold_50_v3` | 50 | (80_v4의 ep0~49와 같음) | 처음 모은 50개 |
| `Woohi123/towel_tape_halffold_gatefold_80_v4` | 70 | 120,255 | 위 50개(ep0~49, 같은 데이터로 확인) + 추가 20개(ep50~69) |

에피소드 평균 길이는 약 57초입니다.

## 구간(단계) 경계

반접기 구간과 대문접기 구간의 경계는 웹 검토 도구로 에피소드마다 사람이 확인했습니다. 결과는 [`results/half_fold_stage_boundaries.json`](../results/half_fold_stage_boundaries.json)에 있습니다(원본 에피소드별 반접기 `start`/`end` 프레임). 이 경계로 만든 구간 데이터셋 `..._80_v4_stage_gate_fold`의 에피소드 i는 원본 ep i의 `[반접기 끝:]`과 같다는 것을 state 값으로 확인했습니다(70/70 일치).
