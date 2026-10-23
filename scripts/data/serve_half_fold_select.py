"""70개 반접기 구간을 웹으로 보며 '완벽한 반접기'만 골라 저장한다 (학습용 에피소드 선택).

Run:  uv run --no-sync python custom_scripts/serve_half_fold_select.py
Open: http://127.0.0.1:8767
선택: outputs/review/towel_half_fold_select/selection.json ({"000": "good" | "bad"})
페이지 위쪽에 '완벽' 에피소드 목록이 --dataset.episodes 형식으로 나온다.
기존 serve_towel_boundary_review.py의 영상 스트리밍을 그대로 쓰고, 그 파일은 수정하지 않는다.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import serve_towel_boundary_review as review

review.DATASET = review.ROOT / "outputs/datasets/towel_tape_70_stage_half_fold"
SELECTION = review.ROOT / "outputs/review/towel_half_fold_select/selection.json"
PAGE = Path(__file__).with_name("towel_half_fold_select.html")
CHOICES = ("good", "bad")


def load_selection() -> dict[str, str]:
    return json.loads(SELECTION.read_text()) if SELECTION.exists() else {}


def hints() -> dict[str, dict]:
    """참고 지표: 왼손 놓기 pan(원래 50개 범위 -17.8~-2.8°), 끝/시작 수건 면적비(0.5=정확한 반)."""
    from compare_half_fold_groups import BOUNDARIES, SOURCE_ROOT, episode_metrics, load_actions

    actions = load_actions(SOURCE_ROOT)
    layout_file = review.ROOT / "outputs/half_fold_compare/towel_layout.json"
    layout = json.loads(layout_file.read_text()) if layout_file.exists() else {}
    out = {}
    for s in json.loads(BOUNDARIES.read_text())["samples"]:
        ep = s["source_episode"]
        m = episode_metrics(actions[ep][s["start"]:s["end"]])
        start, end = layout.get(str(ep), (None, None))
        out[f"{ep:03d}"] = {
            "left_pan": None if m is None else round(float(m["left"]["release_pose"][0]), 1),
            "area_ratio": None if start is None else round(end[2] / start[2], 3),
        }
    return out


class Handler(review.Handler):
    hint_data: dict = {}

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.respond(PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/episodes":
            self.json_response({"episodes": self.episodes, "selection": load_selection(), "hints": self.hint_data})
        else:
            super().do_GET()  # 영상 byte-range 스트리밍

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/select":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1024:
                raise ValueError("invalid request length")
            payload = json.loads(self.rfile.read(length))
            episode, choice = payload["episode"], payload["choice"]
            if type(episode) is not int or not 0 <= episode < len(self.episodes):
                raise ValueError("episode out of range")
            if choice not in (*CHOICES, None):
                raise ValueError("choice must be good, bad or null")
            with review.LOCK:
                selection = load_selection()
                if choice is None:
                    selection.pop(f"{episode:03d}", None)
                else:
                    selection[f"{episode:03d}"] = choice
                SELECTION.parent.mkdir(parents=True, exist_ok=True)
                temporary = SELECTION.with_suffix(".json.tmp")
                temporary.write_text(json.dumps(selection, indent=2, sort_keys=True) + "\n")
                temporary.replace(SELECTION)
            self.json_response({"ok": True, "selection": selection})
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            self.json_response({"error": str(error)}, HTTPStatus.BAD_REQUEST)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()
    Handler.episodes = review.episode_list()
    Handler.hint_data = hints()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"반접기 선택: http://127.0.0.1:{args.port}  (저장: {SELECTION})", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
