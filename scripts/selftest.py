#!/usr/bin/env python3
"""Zelftest: maakt een fictief huishouden met exports van ING, Rabobank en ABN AMRO (incl. een overlappende
dubbele ING-export), draait de hele pijplijn en controleert de uitkomsten. Geen echte data nodig.

Gebruik: python selftest.py [doelmap]   (standaard ./demo-huishouden)
Vergelijkt ook Python- en JS-model als Node beschikbaar is (niet nodig in ChatGPT).
"""
import json
import random
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
random.seed(7)


def months(start, n):
    y, m = start.year, start.month
    for _ in range(n):
        yield date(y, m, 1)
        m += 1
        if m > 12:
            y, m = y + 1, 1


def make(work: Path):
    if work.exists():
        shutil.rmtree(work)
    (work / "data" / "ing").mkdir(parents=True)
    (work / "data" / "rabo").mkdir(parents=True)
    (work / "data" / "abn").mkdir(parents=True)
    (work / "config").mkdir()
    ING, RABO, ABN = "NL11INGB0001234567", "NL22RABO0123456789", "NL51ABNA0987654321"  # ABN: geldig berekend uit rekeningnummer
    tx = {ING: [], RABO: [], ABN: []}

    def add(acc, d, amt, name, cp="", desc=""):
        tx[acc].append((d, round(amt, 2), name, cp, desc))

    for m0 in months(date(2025, 8, 1), 13):
        d = lambda day: m0 + timedelta(days=day - 1)
        add(ING, d(25), 4150.0, "ACME BV", "NL99ABNA0000000001", "SALARIS " + m0.strftime("%m-%Y"))
        add(RABO, d(23), 3190.0, "Gemeente Utrecht", "NL98BNGH0000000002", "Salaris " + m0.strftime("%B"))
        add(ING, d(26), -2600.0, "Fam Voorbeeld gezamenlijk", ABN, "Inleg huishouden")
        add(RABO, d(24), -1900.0, "Fam Voorbeeld gezamenlijk", ABN, "Inleg huishouden")
        add(ABN, d(26), 2600.0, "A VOORBEELD", ING, "Inleg huishouden")
        add(ABN, d(24), 1900.0, "S VOORBEELD", RABO, "Inleg huishouden")
        add(ABN, d(1), -1250.0, "ING HYPOTHEKEN", "NL97INGB0000000003", "HYP.NR. 123")
        add(ABN, d(3), -145.0, "VATTENFALL KLANTEN BV", "NL96INGB0000000004", "Termijnbedrag energie")
        add(ABN, d(5), -1023.0, "PARTOU BV", "NL95RABO0000000005", "Kinderopvang " + m0.strftime("%m-%Y"))
        add(ABN, d(6), -310.0, "ZILVEREN KRUIS ZORGVERZEKERINGEN", "NL94INGB0000000006", "Premie")
        add(ABN, d(8), -15.99, "NETFLIX INTERNATIONAL B.V.", "NL93INGB0000000007", "Netflix")
        add(ABN, d(9), -55.0, "ODIDO NETHERLANDS B.V.", "NL92INGB0000000008", "Internet")
        add(ABN, d(20), 610.0, "BELASTINGDIENST", "NL86INGB0002445588", "VOORSCHOT KINDEROPVANGTOESLAG")
        for _ in range(9):
            add(ABN, d(random.randint(1, 28)), -round(random.uniform(25, 140), 2), random.choice(["ALBERT HEIJN 1234", "JUMBO UTRECHT", "LIDL"]), "", "Betaalpas")
        for _ in range(4):
            add(ING, d(random.randint(1, 28)), -round(random.uniform(15, 90), 2), random.choice(["CAFE DE ZWAAN", "RESTAURANT LUX", "BOL.COM", "SHELL TANKSTATION"]), "", "")
            add(RABO, d(random.randint(1, 28)), -round(random.uniform(10, 70), 2), random.choice(["KRUIDVAT 123", "ZALANDO", "HEMA UTRECHT", "ETOS"]), "", "")
        add(RABO, d(12), -310.0, "DUO HOOFDREKENING", "NL91INGB0000000009", "Studieschuld")
        add(ING, d(15), -33.0, "BASIC-FIT NEDERLAND", "NL90ABNA0000000010", "Lidmaatschap")
    add(ABN, date(2026, 3, 14), -480.0, "J DE VRIES", "NL89ASNB0000000011", "terugbetaling weekend")

    # ---- ING CSV (Nederlands, ;, nieuwste eerst, saldo na mutatie)
    def ing_rows(rows, bal0):
        rows = sorted(rows, key=lambda r: r[0]); out, bal = [], bal0
        for d0, a, n, cp, desc in rows:
            bal = round(bal + a, 2)
            out.append([d0.strftime("%Y%m%d"), n, ING, cp, "GT" if cp else "BA", "Bij" if a > 0 else "Af", f"{abs(a):.2f}".replace(".", ","),
                        "Overschrijving" if cp else "Betaalautomaat", (f"Naam: {n} Omschrijving: {desc} IBAN: {cp}" if cp else "Pasvolgnr: 001 Transactie: 123"), f"{bal:.2f}".replace(".", ","), ""])
        return out[::-1], bal
    hdr = '"Datum";"Naam / Omschrijving";"Rekening";"Tegenrekening";"Code";"Af Bij";"Bedrag (EUR)";"Mutatiesoort";"Mededelingen";"Saldo na mutatie";"Tag"'
    allrows, _ = ing_rows(tx[ING], 1500.0)
    q = lambda r: ";".join('"' + str(x) + '"' for x in r)
    (work / "data/ing/ING_2025-08_2026-08.csv").write_text(hdr + "\n" + "\n".join(q(r) for r in allrows if r[0] < "20260901"))
    (work / "data/ing/ING_2026-07_2026-09.csv").write_text(hdr + "\n" + "\n".join(q(r) for r in allrows if r[0] >= "20260701"))  # overlap jul-aug
    # ---- Rabobank CSV
    rh = ["IBAN/BBAN", "Munt", "BIC", "Volgnr", "Datum", "Rentedatum", "Bedrag", "Saldo na trn", "Tegenrekening IBAN/BBAN", "Naam tegenpartij", "Naam uiteindelijke partij",
          "Naam initiërende partij", "BIC tegenpartij", "Code", "Batch ID", "Transactiereferentie", "Machtigingskenmerk", "Incassant ID", "Betalingskenmerk", "Omschrijving-1",
          "Omschrijving-2", "Omschrijving-3", "Reden retour", "Oorspr bedrag", "Oorspr munt", "Koers"]
    lines, bal = [",".join(f'"{h}"' for h in rh)], 800.0
    for i, (d0, a, n, cp, desc) in enumerate(sorted(tx[RABO], key=lambda r: r[0]), 1):
        bal = round(bal + a, 2)
        row = [RABO, "EUR", "RABONL2U", f"{i:018d}", d0.isoformat(), d0.isoformat(), f"{a:+.2f}".replace(".", ","), f"{bal:+.2f}".replace(".", ","), cp, n, "", "", "", "cb" if cp else "bc", "", "", "", "", "", desc, "", "", "", "", "", ""]
        lines.append(",".join(f'"{x}"' for x in row))
    (work / "data/rabo/CSV_A_20260930.csv").write_text("\n".join(lines), encoding="cp1252")
    # ---- ABN AMRO TAB
    lines, bal = [], 3000.0
    for d0, a, n, cp, desc in sorted(tx[ABN], key=lambda r: r[0]):
        start = bal; bal = round(bal + a, 2)
        info = f"SEPA Overboeking                 IBAN: {cp}        BIC: XXXXNL2A                    Naam: {n}  Omschrijving: {desc}" if cp else f"BEA, Betaalpas                   {n},PAS123"
        lines.append("\t".join([ABN[8:].lstrip("0"), "EUR", d0.strftime("%Y%m%d"), f"{start:.2f}".replace(".", ","), f"{bal:.2f}".replace(".", ","), d0.strftime("%Y%m%d"), f"{a:.2f}".replace(".", ","), info]))
    (work / "data/abn/TXT260930.TAB").write_text("\n".join(lines))
    cfg = json.loads((SKILL / "assets" / "huishouden.voorbeeld.json").read_text())
    cfg["rekeningen"] = [{"iban": ING, "naam": "ING Alex", "eigenaar": "p1"}, {"iban": RABO, "naam": "Rabo Sam", "eigenaar": "p2"}, {"iban": ABN, "naam": "ABN gezamenlijk", "eigenaar": "gezamenlijk"}]
    cfg["huishouden"]["personen"][0]["werkgever_zoekterm"] = "ACME"
    cfg["huishouden"]["personen"][1]["werkgever_zoekterm"] = "Gemeente Utrecht.*Salaris|Salaris.*Gemeente Utrecht"
    cfg["huishouden"]["studieschuld_maand"] = 310
    cfg["huishouden"]["kinderen"][0].update({"dagen_per_week": 2, "uurtarief": 11.8, "weken_per_jaar": 52})
    (work / "config" / "huishouden.json").write_text(json.dumps(cfg, indent=1, ensure_ascii=False))
    (work / "work").mkdir()
    (work / "work" / "narrative.json").write_text(json.dumps({"samenvatting": "<p>Demo-huishouden (fictief).</p>", "h5": [{"niveau": "info", "titel": "Demo", "tekst": "Dit is testdata."}]}, ensure_ascii=False))


def run(step, work):
    r = subprocess.run([sys.executable, str(HERE / step), str(work)], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); raise SystemExit(f"FOUT in {step}")
    return r.stdout


def main():
    work = Path(sys.argv[1] if len(sys.argv) > 1 else "demo-huishouden").resolve()
    make(work)
    out = run("load.py", work)
    assert "dubbel tussen bestanden" in out
    n_dup = int(out.split("dubbel op transactie-ID; ")[1].split(" dubbel")[0])
    assert n_dup > 0, "overlappende ING-export niet ontdubbeld"
    bal = run("check_balances.py", work); assert "Alle saldi sluiten." in bal, bal
    cat = run("categorize.py", work)
    run("phase1_report.py", work)
    an = run("analysis.py", work)
    run("build_report.py", work)
    import pandas as pd
    t = pd.read_csv(work / "work" / "transactions.csv")
    assert (t.subcategory == "Inleg gezamenlijk (p1)").sum() > 0 and (t.subcategory == "Inleg gezamenlijk (p2)").sum() > 0
    assert (t.subcategory == "Salaris Alex").sum() >= 12 and (t.subcategory == "Salaris Sam").sum() >= 12
    assert (t.category == "Kinderopvang").sum() >= 12 and (t.subcategory == "Hypotheek").sum() >= 12
    unk = (t.category == "Onbekend").sum()
    print(f"OK: {n_dup} dubbele regels verwijderd, saldi sluiten, {len(t)} transacties, {unk} onbekend (verwacht: 1 = J de Vries).")
    # model Python vs JS
    sys.path.insert(0, str(HERE)); import nl_model
    cfg = json.loads((work / "config" / "huishouden.json").read_text())
    py = nl_model.household(cfg)
    if shutil.which("node"):
        js = subprocess.run(["node", "-e", f"""const {{makeModel}}=require({json.dumps(str(SKILL / 'assets' / 'model.js'))});
const M=makeModel({{rules:require({json.dumps(str(SKILL / 'assets' / 'nl_regels.json'))}),cfg:require({json.dumps(str(work / 'config' / 'huishouden.json'))}),A:require({json.dumps(str(work / 'work' / 'analysis.json'))})}});
const h=M.household({{year:2026}},0);console.log(JSON.stringify({{net:h.net,ko:h.ko}}));"""], capture_output=True, text=True)
        j = json.loads(js.stdout)
        for pid, val in py["net"].items():
            assert abs(val - j["net"][pid]) < 1, (pid, val, j["net"][pid])
        assert abs(py["opvang"]["toeslag_m"] - j["ko"]["toeslag_m"]) < 0.5
        print("OK: Python- en JS-model geven hetzelfde netto inkomen en dezelfde toeslag.")
    else:
        print("Node niet gevonden: JS-vergelijking overgeslagen (prima in ChatGPT).")
    print("Rapport:", work / "rapport" / "financieel-overzicht.html")


if __name__ == "__main__":
    main()
