"""Rebuild the final deck and publish it to the public Pages repo (for1809/sta3115-ddareungi-deck).

Run from the project root:  python slides/publish_deck.py
  1. runs slides/build_final_deck.py (writes slides/deck_final.html)
  2. copies it to .deck_site/index.html (a clone of the public repo, gitignored here; cloned on first run)
  3. commits and pushes it if it changed; GitHub Pages then serves it at https://for1809.github.io/sta3115-ddareungi-deck/
Only the deck file goes to the public repo; the analysis repo stays private.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / ".deck_site"
REPO = "https://github.com/for1809/sta3115-ddareungi-deck.git"


def git(*a, cwd=SITE):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


subprocess.run([sys.executable, "-I", str(ROOT / "slides" / "build_final_deck.py")], check=True)
if not SITE.exists():
    git("clone", "-q", REPO, str(SITE), cwd=ROOT)
    for k in ("user.name", "user.email"):
        git("config", k, git("config", k, cwd=ROOT))
git("pull", "-q", "--ff-only")
shutil.copyfile(ROOT / "slides" / "deck_final.html", SITE / "index.html")
if not git("status", "--porcelain"):
    print("deck unchanged, nothing to publish")
    sys.exit(0)
src = git("rev-parse", "--short", "HEAD", cwd=ROOT)
git("add", "index.html")
git("commit", "-q", "-m", f"Deck from sta3115-ddareungi {src}\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
git("push", "-q")
print("published", git("rev-parse", "--short", "HEAD"), "-> https://for1809.github.io/sta3115-ddareungi-deck/")
