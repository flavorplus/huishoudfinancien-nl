#!/usr/bin/env python3
"""Stap 4 (einde fase 1): overzicht per categorie per maand + onduidelijke posten + inleg gezamenlijk.

Analyseperiode: config "periode" of automatisch de laatste 12 volle maanden in de data.
Gebruik: python phase1_report.py <werkmap>  ->  rapport/fase1_overzicht.xlsx en .md, work/period.json
"""
import json
import sys
from pathlib import Path

import pandas as pd



def period(df, cfg):
    """Laatste 12 volle maanden in de data (of korter als er minder data is)."""
    p = cfg.get("periode", {}) or {}
    if p.get("start") and p.get("eind"):
        return pd.Timestamp(p["start"]), pd.Timestamp(p["eind"])
    first, last = df.date.min(), df.date.max()
    first_full = first.normalize() if first.day == 1 else (first + pd.offsets.MonthBegin(1)).normalize()
    end = pd.Timestamp(last.year, last.month, 1)
    if last.day == last.days_in_month:
        end = end + pd.offsets.MonthBegin(1)
    return max(end - pd.DateOffset(months=12), first_full), end


def mdtab(df, index=True):
    """Markdown-tabel; valt terug op platte tekst als 'tabulate' ontbreekt (bv. in ChatGPT)."""
    try:
        return df.to_markdown(index=index)
    except ImportError:
        return "```\n" + df.to_string(index=index) + "\n```"


def main(workdir: Path):
    work, out = workdir / "work", workdir / "rapport"
    out.mkdir(exist_ok=True)
    cfg_path = workdir / "config" / "huishouden.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    df = pd.read_csv(work / "transactions.csv", parse_dates=["date"])
    start, end = period(df, cfg)
    months = (end.year - start.year) * 12 + end.month - start.month
    (work / "period.json").write_text(json.dumps({"start": str(start.date()), "eind": str(end.date()), "maanden": months}))
    persons = [p["id"] for p in cfg.get("huishouden", {}).get("personen", [])] or sorted(set(df.owner) - {"gezamenlijk", "zakelijk", "kinderen", "beleggen", "?"})
    names = {p["id"]: p["naam"] for p in cfg.get("huishouden", {}).get("personen", [])}
    per = df[(df.date >= start) & (df.date < end)]
    hh = per[per.owner.isin(persons + ["gezamenlijk", "?"])]
    ext = hh[hh.category != "Intern"]

    def pivot(d, index):
        pv = d.pivot_table(index=index, columns="month", values="amount", aggfunc="sum", fill_value=0)
        pv["Totaal"] = pv.sum(axis=1)
        pv["Gem/mnd"] = pv["Totaal"] / max(months, 1)
        return pv.round(0)

    cat = pivot(ext, "category").sort_values("Totaal")
    cat.loc["SALDO (inkomen − uitgaven)"] = cat.sum()
    sub = pivot(ext, ["category", "subcategory"])
    intern = per[(per.category == "Intern") & (per.owner == "gezamenlijk")]
    inleg = intern[intern.subcategory.str.startswith("Inleg") & (intern.amount > 0)]
    inleg_pv = inleg.pivot_table(index="subcategory", columns="month", values="amount", aggfunc="sum", fill_value=0) if len(inleg) else pd.DataFrame()
    if len(inleg_pv):
        inleg_pv["Totaal"] = inleg_pv.sum(axis=1)
        idx = list(inleg_pv.index)
        for k, v in names.items():
            idx = [i.replace(f"({k})", f"({v})") for i in idx]
        inleg_pv.index = idx
    ondui = ext[(ext.category.isin(["Onbekend", "Betaalverzoeken"])) & (ext.amount.abs() >= 100)]
    cols = ["date", "account_iban", "owner", "amount", "counterparty_name", "description", "category", "subcategory"]
    with pd.ExcelWriter(out / "fase1_overzicht.xlsx") as xw:
        cat.to_excel(xw, sheet_name="Categorie x maand")
        sub.to_excel(xw, sheet_name="Subcategorie x maand")
        if len(inleg_pv): inleg_pv.to_excel(xw, sheet_name="Inleg gezamenlijk")
        ondui[cols].to_excel(xw, sheet_name="Onduidelijke posten", index=False)
        df[cols + ["source", "file", "rule"]].to_excel(xw, sheet_name="Alle transacties", index=False)
    short = cat.copy()
    short.columns = [c[2:].replace("-", "") if str(c).startswith("20") else c for c in short.columns]
    md = [f"# Fase 1 – per categorie per maand ({start:%b %Y} – {(end - pd.Timedelta(days=1)):%b %Y}, {months} mnd)", "",
          "Huishouden = persoonlijke + gezamenlijke rekeningen; zonder interne overboekingen, zakelijk, kinder- en beleggingsrekeningen.", "",
          mdtab(short.astype(int)), ""]
    if len(inleg_pv):
        md += ["## Inleg gezamenlijke rekening(en)", "", mdtab(inleg_pv.round(0).astype(int)), ""]
    md += [f"## Onduidelijke posten (≥ €100): {len(ondui)}", "", mdtab(ondui[["date", "amount", "counterparty_name", "description"]].head(40), index=False)]
    (out / "fase1_overzicht.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
