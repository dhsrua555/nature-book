# /// script
# requires-python = ">=3.11"
# ///
"""로컬 미리보기 서버.

    uv run tools/serve.py          # http://localhost:8000
    uv run tools/serve.py 8080

정적 파일을 그대로 내보내고, 검수 모드(?edit)에서 누른 '저장'만 받아
data/<권>/species/<id>.json 을 고쳐 쓴다. 이 컴퓨터(127.0.0.1)에서만 열린다.
"""

import json
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAVE = re.compile(r"^/__save/(data/[a-z0-9-]+/species/[a-z0-9-]+\.json)$")


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_PUT(self):
        m = SAVE.match(self.path)
        if not m:
            self.send_error(404)
            return
        target = ROOT / m.group(1)
        if not target.exists():
            self.send_error(404, "없는 종 파일")
            return
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_error(400, "JSON 아님")
            return
        if data.get("id") != target.stem:
            self.send_error(400, "id 불일치")
            return
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.send_response(204)
        self.end_headers()
        print(f"저장: {target.relative_to(ROOT)}")


def main():
    sys.stdout.reconfigure(errors="replace")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(ROOT)))
    print(f"http://localhost:{port}  (검수 모드: http://localhost:{port}/?edit) · 끝내려면 Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
