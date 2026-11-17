"""Builds prompts.json and prompts.csv from prompts/**/*.md and refreshes the
category table in README.md (between the CATEGORIES markers).

Run from the repo root: python3 scripts/build.py
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"
KINDS = [("image-to-image", "Image-to-image"), ("text-to-image", "Text-to-image")]

ITEM = re.compile(
    r"^## (\d+)\. (.+?)\n+Tags: (.+?)\n+```text\n(.+?)\n```", re.M | re.S
)


def parse(path):
    text = path.read_text(encoding="utf-8")
    title = re.search(r"^# (.+)$", text, re.M).group(1).strip()
    items = []
    for num, name, tags, body in ITEM.findall(text):
        items.append({
            "number": int(num),
            "title": name.strip(),
            "tags": [t.strip() for t in tags.split(",") if t.strip()],
            "prompt": " ".join(body.split()),
        })
    return title, items


def main():
    rows, sections, total = [], [], 0
    for kind, label in KINDS:
        lines = []
        for path in sorted((PROMPTS / kind).glob("*.md")):
            title, items = parse(path)
            rel = path.relative_to(ROOT).as_posix()
            for it in items:
                rows.append({
                    "id": f"{kind}/{path.stem}/{it['number']}",
                    "type": kind,
                    "category": path.stem,
                    "category_title": title,
                    **it,
                })
            total += len(items)
            lines.append(f"| [{title}]({rel}) | {len(items)} |")
        count = sum(1 for r in rows if r["type"] == kind)
        sections.append(f"**{label}** ({count})\n\n| Category | Prompts |\n|---|---|\n" + "\n".join(lines))

    (ROOT / "prompts.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with open(ROOT / "prompts.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "category", "title", "tags", "prompt"])
        for r in rows:
            w.writerow([r["id"], r["type"], r["category"], r["title"], ";".join(r["tags"]), r["prompt"]])

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    block = "<!-- CATEGORIES:START -->\n" + "\n\n".join(sections) + "\n<!-- CATEGORIES:END -->"
    text = re.sub(r"<!-- CATEGORIES:START -->.*?<!-- CATEGORIES:END -->", block, text, flags=re.S)
    text = re.sub(r"<!-- TOTAL -->\d*\+?<!-- /TOTAL -->", f"<!-- TOTAL -->{total}<!-- /TOTAL -->", text)
    readme.write_text(text, encoding="utf-8")
    print(f"{total} prompts in {len(rows) and len({r['category'] for r in rows})} categories")


if __name__ == "__main__":
    main()
