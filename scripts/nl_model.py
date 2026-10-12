#!/usr/bin/env python3
"""Algemeen Nederlands huishoudmodel (jaarbasis): netto inkomen, kinderopvangtoeslag, eigen woning, max hypotheek.

Leest de regels uit assets/nl_regels.json. Dezelfde logica staat in assets/model.js (voor de schuifjes in het rapport);
selftest.py vergelijkt beide als Node beschikbaar is.

Bewuste vereenvoudigingen (noem ze in het rapport): werknemers in loondienst onder de AOW-leeftijd; geen ondernemers-
aftrek; pensioenpremie = pct x (bruto - franchise); IB op jaarbasis (= loonheffing + aangifte samen).
Kalibreer altijd tegen een loonstrook (zie SKILL.md fase 2) en leg het verschil vast.
"""
import json
from pathlib import Path

RULES = json.loads((Path(__file__).resolve().parent.parent / "assets" / "nl_regels.json").read_text())


def T(y):
    return RULES["belasting"][str(y)]


def box1(y, inc):
    t, lower = 0.0, 0.0
    for upper, rate in T(y)["brackets"]:
        top = inc if upper is None else min(inc, upper)
        if top > lower:
            t += (top - lower) * rate
        if upper is None or inc <= upper:
            break
        lower = upper
    return t


def ahk(y, v):
    p = T(y)["ahk"]
    return p["max"] if v <= p["start"] else max(0.0, p["max"] - p["rate"] * (v - p["start"]))


def ak(y, x):
    if x <= 0:
        return 0.0
    for lo, hi, pct, base, frm in RULES["arbeidskorting"][str(y)]:
        if hi is None or x <= hi:
            return max(0.0, base + pct * (x - frm))
    return 0.0


def iack(y, x):
    p = T(y)["iack"]
    return 0.0 if x <= p["min_income"] else min(p["max"], p["rate"] * (x - p["min_income"]))


def ewf(y, woz):
    p = T(y)["ewf"]
    return p["rate"] * woz if woz <= p["villa_threshold"] else p["rate"] * p["villa_threshold"] + p["villa_rate"] * (woz - p["villa_threshold"])


def ib(y, fiscal, ew=0.0, iack_on=False):
    inc = max(0.0, fiscal + ew)
    tax = box1(y, inc)
    if ew < 0:  # aftrek in de toptariefschijf levert maximaal het aftrektarief op
        top = T(y)["brackets"][1][0]
        tax += min(-ew, max(0.0, fiscal - top)) * (T(y)["brackets"][2][1] - T(y)["deduction_max_rate"])
    return max(0.0, tax - ahk(y, inc) - ak(y, fiscal) - (iack(y, fiscal) if iack_on else 0.0))


def person(p, hours=None, gross=None):
    """Bruto (incl. vakantiegeld) schaalt met uren t.o.v. contracturen."""
    h = p.get("uren", p.get("contracturen", 40)) if hours is None else hours
    base = p["bruto_jaar_incl_vakantiegeld"] if gross is None else gross
    g = base * (h / p.get("contracturen", h or 1)) if h else 0.0
    pens = p.get("pensioenpremie_werknemer_pct", 0.0) * max(0.0, g - p.get("pensioen_franchise", 0.0)) if g else 0.0
    return {"gross": g, "pension": pens, "fiscal": g - pens}


def kot_pct(y, ti):
    k = RULES["kinderopvangtoeslag"][str(y)]
    for upper, f, n in k["tabel"]:
        if ti <= upper:
            return min(0.96, f + k["plus_eerste"]), min(0.96, n + k["plus_volgende"])
    return k["tabel"][-1][1], k["tabel"][-1][2]


def opvang(y, ti, kids, all_work, flat=None):
    """kids = [{opvang, dagen_per_week, uren_per_dag, uurtarief}] -> maandbedragen."""
    k = RULES["kinderopvangtoeslag"][str(y)]
    items = []
    for c in kids:
        hrs = c.get("dagen_per_week", 0) * c.get("uren_per_dag", 10) * c.get("weken_per_jaar", 52) / 12 if c.get("opvang") != "bso" else c.get("bso_uren_maand", 23 * c.get("dagen_per_week", 0))
        items.append((hrs, c.get("uurtarief", 0), k["max_uurprijs"].get(c.get("opvang", "dagopvang"), k["max_uurprijs"]["dagopvang"])))
    items.sort(key=lambda t: -t[0])
    cost = sum(h * r for h, r, _ in items)
    toeslag = 0.0
    if all_work and items:
        f, n = (flat, flat) if flat else kot_pct(y, ti)
        for i, (h, r, mx) in enumerate(items):
            toeslag += min(h, k["max_uren_maand"]) * min(r, mx) * (f if i == 0 else n)
    return {"cost_m": cost, "toeslag_m": toeslag, "net_m": cost - toeslag}


def household(cfg, y=2026, hours=None, gross=None, ew_saldo=0.0, kids=None):
    """hours/gross: dict per persoon-id om scenario's te rekenen. Retourneert netto per persoon (excl. EW-voordeel) + EW-voordeel."""
    P = cfg["huishouden"]["personen"]
    hours, gross = hours or {}, gross or {}
    pp = {p["id"]: person(p, hours.get(p["id"]), gross.get(p["id"])) for p in P}
    has_young = any(True for _ in (kids if kids is not None else cfg["huishouden"].get("kinderen", [])))
    working = [i for i, v in pp.items() if v["fiscal"] > 0]
    low = min(working, key=lambda i: pp[i]["fiscal"]) if working else None
    single = len(P) == 1
    base_tax = {i: ib(y, v["fiscal"], 0.0, has_young and (i == low) and (len(working) == len(P) or single)) for i, v in pp.items()}
    best = sum(base_tax.values())
    if ew_saldo and len(P) == 2:
        a, b = P[0]["id"], P[1]["id"]
        for k in range(11):
            sh = k / 10
            t = ib(y, pp[a]["fiscal"], ew_saldo * (1 - sh), has_young and a == low) + (ib(y, pp[b]["fiscal"], ew_saldo * sh, has_young and b == low) if pp[b]["fiscal"] > 0 or sh == 0 else 1e18)
            best = min(best, t)
    elif ew_saldo:
        i = P[0]["id"]
        best = ib(y, pp[i]["fiscal"], ew_saldo, has_young)
    net = {i: v["gross"] - v["pension"] - base_tax[i] for i, v in pp.items()}
    ti = sum(v["fiscal"] for v in pp.values()) + ew_saldo
    all_work = len(working) == len(P)
    ko = opvang(y, ti, kids if kids is not None else cfg["huishouden"].get("kinderen", []), all_work)
    return {"persons": pp, "net": net, "net_total_m": sum(net.values()) / 12, "ew_benefit_m": (sum(base_tax.values()) - best) / 12,
            "toetsingsinkomen": ti, "opvang": ko, "all_work": all_work}


def annuity(P, r, n=360):
    return P / n if r == 0 else P * (r / 12) / (1 - (1 + r / 12) ** -n)


def flp(toetsinkomen, toetsrente):
    H = RULES["hypotheek"]
    row = [r for r in H["financieringslast_tabel_2026"] if r[0] <= toetsinkomen][-1]
    for i, upper in enumerate(H["rente_kolommen_bovengrens"]):
        if toetsrente <= upper + 1e-9:
            return row[1 + i]
    return row[-1]


def max_mortgage(cfg, rate, fix_years=10, other_monthly=0.0, gross=None, hours=None, label="C"):
    """Max hypotheek op inkomen (Trhk 2026). other_monthly = maandlasten van andere leningen (bv. familielening, 2e woning)."""
    H = RULES["hypotheek"]
    P = cfg["huishouden"]["personen"]
    gross, hours = gross or {}, hours or {}
    ti = sum(person(p, hours.get(p["id"]), gross.get(p["id"]))["gross"] for p in P if p.get("vast_contract", True))
    tr = rate if fix_years >= 10 else max(rate, H["toetsrente_short"])
    pct = flp(ti, tr)
    room = ti * pct / 12 - cfg["huishouden"].get("studieschuld_maand", 0) * H["studieschuld_factor"] - other_monthly
    return {"toetsinkomen": ti, "toetsrente": tr, "pct": pct, "max": max(0.0, room) / annuity(1, tr) + H["energy_label_bonus"].get(label, 0)}


if __name__ == "__main__":
    import sys
    cfg = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else json.loads((Path(__file__).resolve().parent.parent / "assets" / "huishouden.voorbeeld.json").read_text())
    h = household(cfg)
    print({k: round(v / 12) for k, v in h["net"].items()}, "netto/mnd per persoon")
    print({k: round(v) for k, v in h["opvang"].items()}, "opvang/mnd")
    d = cfg.get("doelen", {}).get("nieuwe_woning", {})
    print("max hypotheek:", {k: round(v, 3) for k, v in max_mortgage(cfg, d.get("rente", 0.042), d.get("rentevast_jaren", 10)).items()})
