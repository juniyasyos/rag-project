import shutil
from pathlib import Path
from rag_project.paths import INPUT_DIR, DOCS_DIR, PROJECT_ROOT

TEMPLATE_NAMES = {"template.md"}

def is_template(path: Path) -> bool:
    return path.name in TEMPLATE_NAMES

def clean_input_dir():
    if INPUT_DIR.exists():
        count = 0
        for f in INPUT_DIR.iterdir():
            if f.is_file():
                f.unlink()
                count += 1
        print(f"  🧹  Cleaned {count} existing file(s) from {INPUT_DIR}")
    else:
        INPUT_DIR.mkdir(parents=True, exist_ok=True)
        print(f"  📁  Created {INPUT_DIR}")

def collect_markdown_files() -> list[Path]:
    files = []
    if DOCS_DIR.exists():
        for f in sorted(DOCS_DIR.glob("*.md")):
            if not is_template(f):
                files.append(f)
        releases_dir = DOCS_DIR / "releases"
        if releases_dir.exists():
            for f in sorted(releases_dir.glob("*.md")):
                if not is_template(f):
                    files.append(f)
    return files

def copy_files(files: list[Path]) -> list[Path]:
    copied = []
    for src in files:
        dest = INPUT_DIR / src.name
        shutil.copy2(src, dest)
        copied.append(dest)
    return copied

def sync_docs():
    print("=" * 50)
    print("  Sync Docs → rag/input/")
    print("=" * 50)
    clean_input_dir()
    md_files = collect_markdown_files()
    if not md_files:
        print("  ⚠️  No markdown files found in docs/ or docs/releases/.")
        return
    copied = copy_files(md_files)
    print(f"  ✅  Copied {len(copied)} file(s) to {INPUT_DIR}")
