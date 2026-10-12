#!/usr/bin/env python3
"""Stap 1: lees alle bankexports in data/, herken het formaat, normaliseer en ontdubbel.

Ondersteunde formaten (automatisch herkend):
  - ING CSV (Nederlands of Engels, ; of , gescheiden)
  - Rabobank CSV (26 kolommen, "IBAN/BBAN", "Volgnr", "Saldo na trn")
  - ABN AMRO TXT/TAB (tab-gescheiden, geen kopregel) en MT940 (.STA/.940; ook ING/Rabo MT940)
  - bunq API-export (payments_*.csv met payment_id, balance_after)
  - American Express NL CSV (Datum, Omschrijving, Bedrag)
  - Eigen kolomindeling via config/huishouden.json -> "formaten" (zie references/bankexports.md)

Gebruik:  python load.py <werkmap>
Output:   <werkmap>/work/transactions_raw.csv, work/load_report.txt, work/mt940_balances.csv
De originele bestanden in <werkmap>/data/ worden alleen gelezen.
"""
import csv
import io
import json
import re
import sys
from pathlib import Path

import pandas as pd

COLS = ["source", "file", "account_iban", "date", "amount", "counterparty_name", "counterparty_iban",
        "description", "tx_type", "tx_id", "balance_after"]
IBAN_RE = r"[A-Z]{2}\d{2}[A-Z]{4}\d{7,10}"


def read_text(p: Path) -> str:
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def nl_num(x) -> float:
    """'1.234,56' / '-12,30' / '+5,00' / '12.30' -> float."""
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return float("nan")
    s = str(x).strip().replace(" ", "").replace(" ", "").replace("€", "")
    if not s:
        return float("nan")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)


def sniff_sep(first_line: str) -> str:
    return max([";", ",", "\t"], key=first_line.count)


# ------------------------------------------------------------------ ING
def is_ing(header):
    h = [c.strip().strip('"').lower() for c in header]
    return ("naam / omschrijving" in h or "name / description" in h) and ("af bij" in h or "debit/credit" in h)


def load_ing(p, text, header, sep):
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    nl = "Naam / Omschrijving" in df.columns
    c = (lambda nlname, enname: nlname if nl else enname)
    amt = df[c("Bedrag (EUR)", "Amount (EUR)")].map(nl_num)
    credit = df[c("Af Bij", "Debit/credit")].str.strip().str.lower().isin(["bij", "credit"])
    amt = amt.where(credit, -amt)
    notes = df[c("Mededelingen", "Notifications")].fillna("")
    desc = notes.str.extract(r"(?:Omschrijving|Description): (.*?)(?: IBAN:| Kenmerk:| Reference:| Valutadatum:| Value date:|$)")[0]
    desc = desc.fillna(notes.where(~notes.str.match(r"(Pasvolgnr|Card|Pas)"), ""))
    bal_col = c("Saldo na mutatie", "Resulting balance")
    return pd.DataFrame({
        "source": "ING", "file": p.name,
        "account_iban": df[c("Rekening", "Account")].str.strip(),
        "date": pd.to_datetime(df[c("Datum", "Date")].str.strip(), format="%Y%m%d"),
        "amount": amt,
        "counterparty_name": df[c("Naam / Omschrijving", "Name / Description")].fillna(""),
        "counterparty_iban": df[c("Tegenrekening", "Counterparty")].fillna(""),
        "description": desc,
        "tx_type": df[c("Mutatiesoort", "Transaction type")].fillna(""),
        "tx_id": "",
        "balance_after": df[bal_col].map(nl_num) if bal_col in df.columns else float("nan"),
        "_order": list(range(len(df)))[::-1],  # ING: nieuwste eerst
    })


# ------------------------------------------------------------------ Rabobank
def is_rabo(header):
    h = [c.strip().strip('"') for c in header]
    return "IBAN/BBAN" in h and "Volgnr" in h


def load_rabo(p, text, header, sep):
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
    desc = df[[c for c in ["Omschrijving-1", "Omschrijving-2", "Omschrijving-3"] if c in df.columns]].fillna("").agg(" ".join, axis=1).str.strip()
    name = df.get("Naam tegenpartij", pd.Series([""] * len(df))).fillna("")
    return pd.DataFrame({
        "source": "Rabobank", "file": p.name,
        "account_iban": df["IBAN/BBAN"].str.strip(),
        "date": pd.to_datetime(df["Datum"].str.strip()),
        "amount": df["Bedrag"].map(nl_num),
        "counterparty_name": name,
        "counterparty_iban": df.get("Tegenrekening IBAN/BBAN", pd.Series([""] * len(df))).fillna(""),
        "description": desc,
        "tx_type": df.get("Code", pd.Series([""] * len(df))).fillna(""),
        "tx_id": "rabo-" + df["IBAN/BBAN"].str.strip() + "-" + df["Volgnr"].str.strip(),
        "balance_after": df["Saldo na trn"].map(nl_num) if "Saldo na trn" in df.columns else float("nan"),
        "_order": df["Volgnr"].map(lambda v: int(re.sub(r"\D", "", v) or 0)),
    })


# ------------------------------------------------------------------ omschrijvingen ontleden (ABN TAB / MT940)
FIELD_KEYS = "TRTP|IBAN|BIC|NAME|REMI|EREF|CSID|MARF|ORDP|ID"


def parse_info(info: str):
    info = re.sub(r"\s{2,}", " ", info.replace("\n", "")).strip()
    if info.startswith("/"):
        f = dict(re.findall(rf"/({FIELD_KEYS})/(.*?)(?=/(?:{FIELD_KEYS})/|$)", info))
        return f.get("NAME", "").strip(), f.get("IBAN", "").strip(), f.get("REMI", f.get("TRTP", "")).strip()
    name = re.search(r"Naam: (.*?)\s*(?=Omschrijving:|Machtiging:|Kenmerk:|IBAN:|BIC:|ID debiteur:|$)", info, re.I)
    iban = re.search(rf"IBAN: ({IBAN_RE})", info)
    desc = re.search(r"Omschrijving: (.*?)\s*(?=Kenmerk:|IBAN:|Machtiging:|ID debiteur:|$)", info, re.I)
    if not name:  # pinbetaling 'BEA, Betaalpas  ALBERT HEIJN 1234,PAS123 ...'
        m = re.search(r"(?:BEA|GEA|eCom|Apple Pay)[^ ]*,?\s+(?:Betaalpas\s+|Google Pay\s+|Apple Pay\s+)?(.+?)(?:,PAS|\s+NR:|$)", info)
        if m:
            return m.group(1).strip(), "", ""
    return (name.group(1).strip() if name else info[:45]), (iban.group(1) if iban else ""), (desc.group(1).strip() if desc else info)


# ------------------------------------------------------------------ ABN AMRO TAB
def is_abn_tab(text):
    first = text.splitlines()[0] if text else ""
    parts = first.split("\t")
    return len(parts) >= 8 and re.fullmatch(r"\d{8}", parts[2].strip() or "") is not None


def iban_nl(bank, acct):
    bban = bank + acct.zfill(10)
    num = "".join(str(int(c, 36)) for c in bban + "NL00")
    return f"NL{98 - int(num) % 97:02d}{bban}"


def load_abn_tab(p, text):
    rows = []
    for i, line in enumerate(text.splitlines()):
        parts = line.split("\t")
        if len(parts) < 8:
            continue
        acct = parts[0].strip()
        iban = acct if re.fullmatch(IBAN_RE, acct) else iban_nl("ABNA", acct)
        name, ciban, desc = parse_info(parts[7])
        rows.append(dict(source="ABN AMRO", file=p.name, account_iban=iban, date=pd.to_datetime(parts[2], format="%Y%m%d"),
                         amount=nl_num(parts[6]), counterparty_name=name, counterparty_iban=ciban, description=desc,
                         tx_type="TAB", tx_id="", balance_after=nl_num(parts[4]), _order=i))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ MT940
def is_mt940(text):
    return ":20:" in text and ":25:" in text and ":61:" in text


def load_mt940(p, text, balances):
    text = text.replace("\r", "")
    rows = []
    for block in re.split(r"\n-\s*\n|\n-$", text):
        m = re.search(r"^:25:(\S+)", block, re.M)
        if not m:
            continue
        acct = m.group(1).replace("EUR", "")
        iban = acct if re.fullmatch(IBAN_RE, acct) else iban_nl("ABNA", re.sub(r"\D", "", acct)) if acct.isdigit() else acct
        for tag in ("60F", "62F"):
            b = re.search(rf"^:{tag}:([CD])(\d{{6}})EUR([\d,]+)", block, re.M)
            if b:
                v = nl_num(b.group(3)) * (1 if b.group(1) == "C" else -1)
                balances.append(dict(account_iban=iban, tag=tag, date=pd.to_datetime(b.group(2), format="%y%m%d"), balance=v, file=p.name))
        for part in re.split(r"^(?=:61:)", block, flags=re.M)[1:]:
            l61 = re.match(r":61:(\d{6})(\d{4})?(R?[CD])([\d,]+)N(\w{3})", part)
            if not l61:
                continue
            amount = nl_num(l61.group(4)) * (-1 if l61.group(3).endswith("D") else 1)
            info = re.search(r":86:(.*?)(?=^:\d\d\w?:|\Z)", part, re.S | re.M)
            name, ciban, desc = parse_info(info.group(1) if info else "")
            rows.append(dict(source="MT940", file=p.name, account_iban=iban, date=pd.to_datetime(l61.group(1), format="%y%m%d"),
                             amount=amount, counterparty_name=name, counterparty_iban=ciban, description=desc,
                             tx_type="MT940/" + l61.group(5), tx_id="", balance_after=float("nan"), _order=len(rows)))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ bunq (API-export) en Amex
def is_bunq(header):
    return "payment_id" in header and "balance_after" in header


def load_bunq(p, text, sep):
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype={"payment_id": str, "counterparty_iban": str})
    return pd.DataFrame({
        "source": "bunq", "file": p.name, "account_iban": df.account_iban, "date": pd.to_datetime(df.date),
        "amount": df.amount.astype(float), "counterparty_name": df.counterparty_name.fillna(""),
        "counterparty_iban": df.counterparty_iban.fillna(""), "description": df.description.fillna(""),
        "tx_type": df.type.fillna("") + "/" + df.sub_type.fillna(""), "tx_id": "bunq-" + df.payment_id,
        "balance_after": df.balance_after.astype(float), "_order": df.payment_id.astype("int64"),
    })


def is_amex(header):
    h = [c.strip() for c in header]
    return h[:3] == ["Datum", "Omschrijving", "Bedrag"]


def load_amex(p, text, sep):
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str)
    return pd.DataFrame({
        "source": "Amex", "file": p.name, "account_iban": "CREDITCARD-AMEX",
        "date": pd.to_datetime(df.Datum, format="%m/%d/%Y", errors="coerce").fillna(pd.to_datetime(df.Datum, dayfirst=True, errors="coerce")),
        "amount": -df.Bedrag.map(nl_num),  # Amex: positief = uitgave
        "counterparty_name": df.Omschrijving.str.replace(r"\s{2,}", " ", regex=True).str.strip(),
        "counterparty_iban": "", "description": df.get("Aanvullende informatie", pd.Series([""] * len(df))).fillna(""),
        "tx_type": df.get("Categorie", pd.Series([""] * len(df))).fillna(""),
        "tx_id": "amex-" + df.get("Referentie", pd.Series(range(len(df)))).astype(str).str.strip("'"),
        "balance_after": float("nan"), "_order": range(len(df)),
    })


# ------------------------------------------------------------------ eigen kolomindeling
def load_custom(p, text, fmt):
    df = pd.read_csv(io.StringIO(text), sep=fmt.get("scheidingsteken", ";"), dtype=str)
    k = fmt["kolommen"]
    amt = df[k["bedrag"]].map(nl_num)
    if "af_bij" in k:
        credit = df[k["af_bij"]].str.lower().isin([v.lower() for v in fmt.get("bij_waarden", ["Bij", "Credit", "C"])])
        amt = amt.abs().where(credit, -amt.abs())
    return pd.DataFrame({
        "source": fmt.get("naam", "eigen formaat"), "file": p.name,
        "account_iban": df[k["rekening"]] if "rekening" in k else fmt.get("rekening_iban", p.stem),
        "date": pd.to_datetime(df[k["datum"]], format=fmt.get("datum_formaat")),
        "amount": amt, "counterparty_name": df.get(k.get("tegenpartij", ""), ""),
        "counterparty_iban": df.get(k.get("tegenrekening", ""), ""), "description": df.get(k.get("omschrijving", ""), ""),
        "tx_type": "", "tx_id": "", "balance_after": df[k["saldo"]].map(nl_num) if "saldo" in k else float("nan"),
        "_order": range(len(df)),
    })


# ------------------------------------------------------------------ hoofdlijn
def main(workdir: Path):
    data, work = workdir / "data", workdir / "work"
    work.mkdir(exist_ok=True)
    cfg_path = workdir / "config" / "huishouden.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    customs = cfg.get("formaten", [])
    frames, balances, report, skipped = [], [], [], []
    for p in sorted(data.rglob("*")):
        if not p.is_file() or p.name.startswith(".") or p.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".xls", ".json", ".md", ".py"):
            continue
        custom = next((f for f in customs if p.match(f.get("bestand_patroon", "__none__"))), None)
        try:
            text = read_text(p)
            first = text.splitlines()[0] if text.strip() else ""
            sep = sniff_sep(first)
            header = next(csv.reader([first], delimiter=sep)) if first else []
            if custom:
                df = load_custom(p, text, custom)
            elif is_mt940(text):
                df = load_mt940(p, text, balances)
            elif is_abn_tab(text):
                df = load_abn_tab(p, text)
            elif is_rabo(header):
                df = load_rabo(p, text, header, sep)
            elif is_ing(header):
                df = load_ing(p, text, header, sep)
            elif is_bunq(header):
                df = load_bunq(p, text, sep)
            elif is_amex(header):
                df = load_amex(p, text, sep)
            else:
                skipped.append(f"{p.relative_to(data)} (onbekend formaat; kop: {first[:80]!r})")
                continue
        except Exception as e:  # noqa: BLE001 - rapporteren en doorgaan
            skipped.append(f"{p.relative_to(data)} (fout bij inlezen: {e})")
            continue
        report.append(f"{p.relative_to(data)}: {df.source.iloc[0] if len(df) else '?'} – {len(df)} regels")
        frames.append(df)
    if not frames:
        print("Geen bankbestanden herkend in", data)
        print("\n".join(skipped))
        sys.exit(1)
    df = pd.concat(frames, ignore_index=True)
    n0 = len(df)
    # 1) harde ontdubbeling op transactie-ID (bunq payment_id, Rabobank volgnr, Amex referentie)
    has_id = df.tx_id.astype(str).str.len() > 0
    dup_id = has_id & df.duplicated(subset=["account_iban", "tx_id"], keep="first")
    df = df[~dup_id]
    # 2) zachte ontdubbeling: dezelfde regel in een ANDER bestand (overlappende exports). Binnen één bestand
    #    blijven identieke regels staan: twee keer koffie van €3 op één dag is echt.
    key = ["account_iban", "date", "amount", "counterparty_name", "description"]
    df = df.assign(_k=df[key].astype(str).agg("|".join, axis=1))
    first_file = df.groupby("_k").file.transform("first")
    dup_soft = (df.file != first_file) & ~df.tx_id.astype(str).str.len().gt(0)
    df = df[~dup_soft]
    report.append(f"\nTotaal {n0} regels; {int(dup_id.sum())} dubbel op transactie-ID; {int(dup_soft.sum())} dubbel tussen bestanden; {len(df)} uniek.")
    if skipped:
        report.append("\nNiet ingelezen (controleer!):\n  " + "\n  ".join(skipped))
    df = df.sort_values(["account_iban", "date", "_order"]).drop(columns=["_k"]).reset_index(drop=True)
    df.to_csv(work / "transactions_raw.csv", index=False)
    pd.DataFrame(balances).to_csv(work / "mt940_balances.csv", index=False)
    accts = df.groupby("account_iban").agg(n=("amount", "size"), van=("date", "min"), tot=("date", "max"), bron=("source", "first"))
    report.append("\nRekeningen in de data:\n" + accts.to_string())
    (work / "load_report.txt").write_text("\n".join(report))
    print("\n".join(report))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
