from pathlib import Path

TARGET = Path("index.html")

def main():
    if not TARGET.exists():
        raise SystemExit(f"missing {TARGET}")

    s = TARGET.read_text(errors="ignore")
    lines = s.splitlines()

    cleaned = [line for line in lines if line.strip() != r"\n"]
    removed = len(lines) - len(cleaned)

    if removed:
        TARGET.write_text("\n".join(cleaned) + "\n")
        print(f"removed {removed} standalone literal newline rows from {TARGET}")
    else:
        print(f"no standalone literal newline rows found in {TARGET}")

if __name__ == "__main__":
    main()
