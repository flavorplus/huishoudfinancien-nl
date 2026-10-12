#!/usr/bin/env python3
"""Fase 2: vaste analyses -> work/analysis.json (invoer voor het rapport en voor jouw teksten).

Bevat: historie per maand/categorie, spaargedrag (met eenmalige posten apart), inleg gezamenlijk per persoon,
terugkerende betalingen (abonnementen, mogelijke dubbelingen), begrotingsregels voor de toekomst (basis =
12-maandsgemiddelden, per scope), vermogen (laatste saldi), kalibratie model vs werkelijk ontvangen salaris.

Gebruik: python analysis.py <werkmap>
Pas daarna desgewenst config/begroting_aanpassingen toe (zie references/rapport.md) en draai build_report.py.
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nl_model  # noqa: E402

HOUSING_SUBS = {"Hypotheek", "Huur", "VvE", "Gemeentelijke belastingen / waterschap", "Water", "Energie"}
INCIDENTAL_SUBS = {"Gift/schenking ontvangen", "Belastingteruggave", "Cashback/refund"}


def norm_cp(s):
    s = str(s).upper()
    s = re.sub(r"^(BCK\*|CCV\*|SUMUP \*|ZETTLE_?\*|PAY\.NL\*|MOL\*)", "", s)
    s = re.sub(r"[\d\*#/.,:\-]+", " ", s)
    s = re.sub(r"\b(B V|BV|NV|N V|NEDERLAND|NETHERLANDS|VIA .*|NLD|AMSTERDAM|ROTTERDAM|UTRECHT)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()[:28]


def main(workdir: Path):
    work = workdir / "work"
    cfg = json.loads((workdir / "config" / "huishouden.json").read_text())
    per_info = json.loads((work / "period.json").read_text())
    start, end, months = pd.Timestamp(per_info["start"]), pd.Timestamp(per_info["eind"]), per_info["maanden"]
    df = pd.read_csv(work / "transactions.csv", parse_dates=["date"])
    persons = [p["id"] for p in cfg["huishouden"]["personen"]]
    names = {p["id"]: p["naam"] for p in cfg["huishouden"]["personen"]}
    per = df[(df.date >= start) & (df.date < end)]
    hh = per[per.owner.isin(persons + ["gezamenlijk", "?"])]
    ext = hh[hh.category != "Intern"]
    M = max(months, 1)

    # --- historie
    cat_month = ext.pivot_table(index="month", columns="category", values="amount", aggfunc="sum", fill_value=0).round(0)
    inc = ext[ext.amount > 0].amount.sum()
    out = -ext[ext.amount < 0].amount.sum()
    incidental = ext[ext.subcategory.isin(INCIDENTAL_SUBS) & (ext.amount > 0)].amount.sum()
    sparen = dict(inkomsten=round(inc), uitgaven=round(out), saldo=round(inc - out), eenmalig_mogelijk=round(incidental),
                  structureel=round(inc - out - incidental), structureel_m=round((inc - out - incidental) / M),
                  noot="Belastingteruggave is als eenmalig geteld; als het een jaarlijkse teruggave is (bv. renteaftrek, IACK), tel hem terug.")

    # --- inleg gezamenlijk
    j = per[(per.owner == "gezamenlijk") & (per.category == "Intern")]
    inleg = {names.get(p, p): round(j[(j.subcategory == f"Inleg gezamenlijk ({p})") & (j.amount > 0)].amount.sum() / M) for p in persons}
    terug = {names.get(p, p): round(-j[(j.subcategory == f"Van gezamenlijk naar {p}") & (j.amount < 0)].amount.sum() / M) for p in persons}
    jext = per[(per.owner == "gezamenlijk") & (per.category != "Intern")]
    joint = dict(inleg_per_persoon_m=inleg, terug_naar_persoon_m=terug, uitgaven_m=round(-jext[jext.amount < 0].amount.sum() / M),
                 inkomsten_m=round(jext[jext.amount > 0].amount.sum() / M))

    # --- terugkerende betalingen
    o = ext[ext.amount < 0].assign(cp=lambda d: d.counterparty_name.map(norm_cp))
    rec = []
    for cp, g in o.groupby("cp"):
        nm = g.month.nunique()
        if nm >= 3 and cp:
            per_month = g.groupby("month").amount.agg(["size", "sum"])
            rec.append(dict(tegenpartij=cp, maanden=int(nm), keer=int(len(g)), gem_m=round(-g.amount.sum() / M, 2),
                            mediaan=round(-g.amount.median(), 2), categorie=g.category.mode().iat[0], sub=g.subcategory.mode().iat[0],
                            rekeningen=sorted(set(g.account_iban)), mogelijk_dubbel=bool((per_month["size"] >= 2).mean() > 0.5 and g.amount.round(0).nunique() >= 1)))
    rec = sorted(rec, key=lambda r: -r["gem_m"])

    # --- begroting (basis = gemiddelden), scope = rekening waarvan het meestal betaald wordt
    lines = []
    for (cat, sub), g in ext[ext.amount < 0].groupby(["category", "subcategory"]):
        if cat in ("Overig",) and -g.amount.sum() / M < 5:
            continue
        own = g.groupby("owner").amount.sum()
        scope = "gez" if (own.get("gezamenlijk", 0) <= own.min()) or cat in ("Wonen", "Kinderopvang", "Boodschappen", "Verzekeringen", "Kinderen") else own.idxmin()
        if cat == "Studieschuld/leningen":
            scope = own.idxmin() if own.idxmin() in persons else scope
        tag = "woning_huidig" if (cat == "Wonen" and sub in HOUSING_SUBS) else ("opvang" if cat == "Kinderopvang" else None)
        lines.append(dict(groep=cat, naam=sub, bedrag=round(-g.amount.sum() / M, 2), scope="gez" if scope in ("gezamenlijk", "gez", "?") else scope,
                          kind="historisch gemiddelde", zeker="midden", tag=tag,
                          vast_persoonlijk=cat in ("Studieschuld/leningen", "Abonnementen", "Verzekeringen", "Sport & hobby") and scope in persons))
    # inkomsten die bij het huishouden horen
    kb = ext[ext.subcategory == "Kinderbijslag"].amount.sum() / M

    # --- vermogen: laatste saldo per rekening
    bal = df[df.balance_after.notna()].sort_values(["date", "_order"]).groupby("account_iban").tail(1)
    accts = {r["iban"]: r for r in cfg.get("rekeningen", [])}
    vermogen = [dict(iban=r.account_iban, naam=accts.get(r.account_iban, {}).get("naam", r.account_iban), eigenaar=accts.get(r.account_iban, {}).get("eigenaar", "?"),
                     saldo=round(r.balance_after, 2), per=str(r.date.date())) for r in bal.itertuples()]

    # --- kalibratie: model vs ontvangen salaris (laatste 3 volle maanden)
    h = nl_model.household(cfg)
    kal = {}
    for p in cfg["huishouden"]["personen"]:
        sal = per[(per.subcategory == f"Salaris {p['naam']}")]
        last3 = sal[sal.date >= end - pd.DateOffset(months=3)].amount.sum() / 3 if len(sal) else None
        kal[p["naam"]] = dict(model_netto_m=round(h["net"][p["id"]] / 12), ontvangen_m_laatste3=round(last3) if last3 else None,
                              loonstrook_netto=p.get("netto_maand_loonstrook"),
                              noot="model = jaargemiddelde incl. vakantiegeld/IKB en heffingskortingen; loonstrook-netto is één maand")

    out_json = dict(periode=per_info, sparen=sparen, gezamenlijk=joint, terugkerend=rec[:60], begroting=lines, kinderbijslag_m=round(kb, 2),
                    vermogen=vermogen, kalibratie=kal, history=dict(months=list(cat_month.index), categories=cat_month.to_dict(orient="list")),
                    personen=names)
    (work / "analysis.json").write_text(json.dumps(out_json, indent=1, default=float, ensure_ascii=False))
    print(json.dumps(dict(sparen=sparen, gezamenlijk=joint, kalibratie=kal), indent=1, ensure_ascii=False))
    print("\nTop terugkerende betalingen:")
    for r in rec[:15]:
        print(f"  {r['tegenpartij']:28} €{r['gem_m']:8.2f}/mnd  {r['maanden']} mnd  {r['categorie']}{'  ← meerdere per maand' if r['mogelijk_dubbel'] else ''}")


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
