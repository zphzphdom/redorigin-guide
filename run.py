# -*- coding: utf-8 -*-
"""启动入口：python run.py [--port 8770]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from server import serve  # noqa: E402

if __name__ == "__main__":
    port = 8770
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    serve(port)
