from pathlib import Path
import re

TARGETS = [
    Path("index.html"),
    Path("index_auto_market.html"),
    Path("index_publish.html"),
]

# Handles compact JSON and optional spaces.
PATTERNS = [
    # ,"projected_margin_home_before_rating_audit_fix":3.775
    re.compile(r',\s*"projected_margin_home_before_rating_audit_fix"\s*:\s*-?\d+(?:\.\d+)?'),
    # "projected_margin_home_before_rating_audit_fix":3.775,
    re.compile(r'"projected_margin_home_before_rating_audit_fix"\s*:\s*-?\d+(?:\.\d+)?\s*,'),
    # ,"projection_rating_audit_fix_note":"..."
    re.compile(r',\s*"projection_rating_audit_fix_note"\s*:\s*"(?:[^"\\]|\\.)*"'),
    # "projection_rating_audit_fix_note":"...",
    re.compile(r'"projection_rating_audit_fix_note"\s*:\s*"(?:[^"\\]|\\.)*"\s*,'),
]

def clean_file(path: Path):
    if not path.exists():
        print(f"missing {path}")
        return

    s = path.read_text(errors="ignore")
    original = s

    before = {
        "projection_rating_audit_fix_note": s.count("projection_rating_audit_fix_note"),
        "projected_margin_home_before_rating_audit_fix": s.count("projected_margin_home_before_rating_audit_fix"),
        "stale_emu_9_2": s.count("Corrected projected_margin_home from 3.8 to 9.2"),
        "stale_ndsu_8_8": s.count("Corrected projected_margin_home from 13.8 to 8.8"),
    }

    for pat in PATTERNS:
        s = pat.sub("", s)

    after = {
        "projection_rating_audit_fix_note": s.count("projection_rating_audit_fix_note"),
        "projected_margin_home_before_rating_audit_fix": s.count("projected_margin_home_before_rating_audit_fix"),
        "stale_emu_9_2": s.count("Corrected projected_margin_home from 3.8 to 9.2"),
        "stale_ndsu_8_8": s.count("Corrected projected_margin_home from 13.8 to 8.8"),
    }

    if s != original:
        bak = path.with_suffix(path.suffix + ".bak_cleanup_stale_projection_audit_notes")
        bak.write_text(original)
        path.write_text(s)
        print(f"{path}: cleaned stale projection audit fields")
    else:
        print(f"{path}: no changes")

    print("  before:", before)
    print("  after: ", after)

def main():
    for path in TARGETS:
        clean_file(path)

if __name__ == "__main__":
    main()
