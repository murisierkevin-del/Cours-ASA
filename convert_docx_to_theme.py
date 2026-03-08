#!/usr/bin/env python3
"""
Convertit un ou plusieurs .docx (1 fichier = 1 thème) en fichiers JSON utilisables par la web-app.

Usage:
  python convert_docx_to_theme.py "MesThemes/*.docx" --out webapp/themes

Format attendu dans Word:
  - Chaque question doit finir par "?" (point d'interrogation)
  - La/les ligne(s) suivantes sont la réponse (jusqu'à la prochaine question)
"""
import argparse, glob, json, re
from pathlib import Path
from datetime import datetime
from docx import Document

def slugify(name: str):
    s = name.lower().strip()
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "theme"

def parse_docx(docx_path: Path):
    doc = Document(str(docx_path))
    lines = [re.sub(r"\s+", " ", p.text.strip()) for p in doc.paragraphs]
    def is_q(s): return bool(s) and s.rstrip().endswith("?")
    cards = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if is_q(line):
            q = line
            i += 1
            ans = []
            while i < len(lines) and not is_q(lines[i].strip()):
                l = lines[i].strip()
                if l:
                    l = re.sub(r"^[\-\u2022]\s*", "", l)
                    ans.append(l)
                i += 1
            a = "\n".join(ans).strip() or "Réponse manquante — à compléter dans le fichier Word."
            cards.append({"q": q, "a": a})
        else:
            i += 1
    return cards

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("patterns", nargs="+", help="Chemins ou patterns vers .docx")
    ap.add_argument("--out", default="themes", help="Dossier de sortie (themes)")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    themes = []
    for pat in args.patterns:
        for fp in glob.glob(pat):
            p = Path(fp)
            theme_name = p.stem
            theme_id = slugify(theme_name)
            cards = parse_docx(p)
            theme_json = {
                "id": theme_id,
                "name": theme_name,
                "version": "1.0.0",
                "generated_at": datetime.utcnow().isoformat()+"Z",
                "cards": [{"id": f"q{i+1:03d}", **c} for i,c in enumerate(cards)]
            }
            (out / f"{theme_id}.json").write_text(json.dumps(theme_json, ensure_ascii=False, indent=2), encoding="utf-8")
            themes.append({"id": theme_id, "name": theme_name, "file": f"themes/{theme_id}.json"})

    index = {"version":"1.0.0", "generated_at": datetime.utcnow().isoformat()+"Z", "themes": themes}
    # IMPORTANT: index.json doit être dans webapp/themes/index.json
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: {len(themes)} thème(s) exporté(s) vers {out}")

if __name__ == "__main__":
    main()
