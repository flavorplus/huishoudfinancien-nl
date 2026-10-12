#!/usr/bin/env python3
"""Stap 2: controleer of de saldi na ontdubbelen kloppen.

- Rekeningen met een lopend saldo (ING, Rabobank, ABN TAB, bunq): vorig saldo + bedrag = saldo, regel voor regel.
- MT940: per afschrift beginsaldo (60F) + mutaties = eindsaldo (62F).
- Optioneel: laatste saldo vergelijken met "saldo_nu" per rekening in config/huishouden.json.

Gebruik: python check_balances.py <werkmap>   ->  work/balance_check.txt
Een breuk betekent bijna altijd: ontbrekende periode, dubbel ingelezen bestand of een export die niet aansluit.
"""
import json
import sys
from pathlib import Path

import pandas as pd


def main(workdir: Path):
    work = workdir / "work"
    df = pd.read_csv(work / "transactions_raw.csv", parse_dates=["date"], dtype={"tx_id": str})
    cfg_path = workdir / "config" / "huishouden.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    saldo_nu = {r["iban"]: r.get("saldo_nu") for r in cfg.get("rekeningen", []) if r.get("saldo_nu") is not None}
    out, problems = ["== Lopend saldo per rekening"], 0
    for iban, g in df[df.balance_after.notna()].groupby("account_iban"):
        g = g.sort_values(["date", "_order"])
        diff = (g.balance_after.shift() + g.amount - g.balance_after).round(2).iloc[1:]
        breaks = diff[diff.abs() > 0.005]
        last = g.balance_after.iloc[-1]
        ref = saldo_nu.get(iban)
        ok = len(breaks) == 0 and (ref is None or abs(ref - last) < 0.01)
        problems += 0 if ok else 1
        out.append(f"{'OK       ' if ok else 'AFWIJKING'} {iban:22} n={len(g):5} breuken={len(breaks):3} laatste saldo={last:12.2f}"
                   + (f" verwacht={ref:12.2f}" if ref is not None else ""))
        for i in breaks.index[:5]:
            r = g.loc[i]
            out.append(f"          breuk op {r.date:%Y-%m-%d}: {r.amount:10.2f} {str(r.counterparty_name)[:30]} (verschil {diff[i]:.2f})")
    bal_path, bal_accounts = work / "mt940_balances.csv", set()
    if bal_path.exists() and bal_path.stat().st_size > 2:
        bal = pd.read_csv(bal_path, parse_dates=["date"])
        if len(bal):
            out.append("\n== MT940: beginsaldo + mutaties = eindsaldo")
            mt = df[df.source == "MT940"]
            bal_accounts = set(bal.account_iban)
            for iban, g in bal.groupby("account_iban"):
                g = g.sort_values("date")
                first = g[g.tag == "60F"].balance.iloc[0]
                lastb = g[g.tag == "62F"].balance.iloc[-1]
                mut = mt[mt.account_iban == iban].amount.sum()
                ok = abs(first + mut - lastb) < 0.01
                problems += 0 if ok else 1
                out.append(f"{'OK       ' if ok else 'AFWIJKING'} {iban:22} begin {first:12.2f} + mutaties {mut:12.2f} = eind {lastb:12.2f}")
    no_bal = sorted(set(df.account_iban) - set(df[df.balance_after.notna()].account_iban) - bal_accounts)
    if no_bal:
        out.append("\nZonder saldo-informatie (niet te controleren): " + ", ".join(no_bal))
    out.append(f"\n{'Alle saldi sluiten.' if problems == 0 else f'{problems} rekening(en) met afwijking – uitzoeken vóór je verder gaat.'}")
    txt = "\n".join(out)
    (work / "balance_check.txt").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
