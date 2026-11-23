"""Build slides/talk_script.pdf from slides/talk_script.html.

{{thumb:NN}} in the source becomes slide NN's picture (PNG files 01.png ... 17.png in the folder given),
embedded as base64 so the PDF needs nothing else. The pictures are screenshots of slides/deck_standalone.html
(slides 5, 7 and 11 at their last step: #5-4, #7-2, #11-2). Fonts come from Google Fonts (Inter, Noto Sans KR),
the same as the deck, so build while online.
Run from the project root:  python slides/build_talk_script.py <thumbs dir>
"""
import base64
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC, OUT = ROOT / "talk_script.html", ROOT / "talk_script.pdf"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

thumbs = Path(sys.argv[1])
html = SRC.read_text(encoding="utf-8")


def thumb(m):
    b = base64.b64encode((thumbs / f"{m.group(1)}.png").read_bytes()).decode("ascii")
    return f'<img src="data:image/png;base64,{b}" alt="slide {int(m.group(1))}">'


html, n = re.subn(r"\{\{thumb:(\d\d)\}\}", thumb, html)
OUT.unlink(missing_ok=True)
with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
    page = Path(tmp) / "talk_script_print.html"
    page.write_text(html, encoding="utf-8")
    # msedge.exe hands the job to a child process and returns at once, so wait for the PDF to appear and settle
    subprocess.run([EDGE, "--headless", "--disable-gpu", f"--user-data-dir={Path(tmp) / 'profile'}",
                    "--no-pdf-header-footer", "--virtual-time-budget=15000",
                    f"--print-to-pdf={OUT}", page.as_uri()], check=True, timeout=180)
    size, t0 = -1, time.time()
    while time.time() - t0 < 180:
        time.sleep(2)
        if OUT.exists() and OUT.stat().st_size == size and size > 0:
            break
        size = OUT.stat().st_size if OUT.exists() else -1
    else:
        sys.exit("PDF did not appear within 180 s")
print(n, "slide pictures ->", OUT, round(OUT.stat().st_size / 1e6, 2), "MB")
