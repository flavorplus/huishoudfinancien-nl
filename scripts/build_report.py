#!/usr/bin/env python3
"""Fase 3: bouw één zelfstandig HTML-rapport (werkt offline, geen server) in <werkmap>/rapport/.

Invoer: assets/nl_regels.json, config/huishouden.json, work/analysis.json, work/narrative.json (jouw teksten),
        work/load_report.txt + work/balance_check.txt (datacontrole), assets/model.js, assets/report_template.html
work/narrative.json (maak je zelf, alle velden optioneel; HTML toegestaan):
  {"samenvatting": "<p>…</p>", "h1": "…", "h2": "…", "h3": "…", "aannames": "<ul>…</ul>",
   "h5": [{"niveau": "bad|warn|info|good", "titel": "…", "tekst": "…"}]}
Gebruik: python build_report.py <werkmap> [bestandsnaam.html]
"""
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def main(workdir: Path, name="financieel-overzicht.html"):
    work = workdir / "work"
    narrative = work / "narrative.json"
    data = {
        "rules": json.loads((SKILL / "assets" / "nl_regels.json").read_text()),
        "cfg": json.loads((workdir / "config" / "huishouden.json").read_text()),
        "A": json.loads((work / "analysis.json").read_text()),
        "N": json.loads(narrative.read_text()) if narrative.exists() else {},
        "checks": "\n\n".join(p.read_text() for p in [work / "load_report.txt", work / "balance_check.txt"] if p.exists()),
    }
    # geen IBANs/BSN's in het rapport dat gedeeld wordt: maskeer rekeningnummers in de controle-tekst
    import re
    data["checks"] = re.sub(r"([A-Z]{2}\d{2}[A-Z]{4})\d{6}(\d{4})", r"\1••••••\2", data["checks"])
    for r in data["cfg"].get("rekeningen", []):
        r["iban"] = re.sub(r"([A-Z]{2}\d{2}[A-Z]{4})\d{6}(\d{4})", r"\1••••••\2", r.get("iban", ""))
    for v in data["A"].get("vermogen", []):
        v["iban"] = re.sub(r"([A-Z]{2}\d{2}[A-Z]{4})\d{6}(\d{4})", r"\1••••••\2", v.get("iban", ""))
    model = (SKILL / "assets" / "model.js").read_text().replace("if (typeof module !== 'undefined') module.exports = { makeModel };", "")
    html = (SKILL / "assets" / "report_template.html").read_text()
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False, default=float).replace("</", "<\\/")).replace("__MODEL__", model)
    out = workdir / "rapport" / name
    out.parent.mkdir(exist_ok=True)
    out.write_text(html)
    print(f"Rapport: {out} ({out.stat().st_size / 1024:.0f} KB). Open het in een browser en controleer het (ook op telefoonbreedte).")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve(), *(sys.argv[2:3]))
