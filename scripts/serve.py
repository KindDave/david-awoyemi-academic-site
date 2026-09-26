"""Local preview server that resolves clean URLs the way GitHub Pages does.

The site links to pages without the .html extension (/about, /portfolio).
GitHub Pages serves about.html for /about automatically; Python's stock
http.server does not, so use this instead when previewing locally:

    python scripts/serve.py          # http://127.0.0.1:8766/
    python scripts/serve.py 8080     # another port
"""
from __future__ import annotations

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PORT = 8766


class CleanURLHandler(SimpleHTTPRequestHandler):
    """Serve path.html for an extensionless path when that file exists."""

    def translate_path(self, path: str) -> str:
        full = super().translate_path(path)
        bare = path.split("?", 1)[0].split("#", 1)[0]
        if not os.path.exists(full) and not bare.endswith("/") and not os.path.splitext(bare)[1]:
            candidate = full + ".html"
            if os.path.isfile(candidate):
                return candidate
        return full

    def end_headers(self) -> None:
        # Always revalidate so edits show up on the next reload.
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    handler = partial(CleanURLHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Serving {ROOT.name} at http://127.0.0.1:{port}/  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
