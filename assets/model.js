// Algemeen huishoudmodel (NL) voor de schuifjes in het rapport. Spiegel van scripts/nl_model.py.
// I = { rules (nl_regels.json), cfg (huishouden.json), A (analysis.json) }. Bedragen per jaar tenzij _m (maand).
function makeModel(I) {
  const R = I.rules, C = I.cfg, A = I.A;
  const P = C.huishouden.personen, KIDS = C.huishouden.kinderen || [];
  const T = (y) => R.belasting[String(y)];
  // ---------------------------------------------------------------- belasting
  function box1(y, inc) { let t = 0, lo = 0; for (const [up, r] of T(y).brackets) { const top = up == null ? inc : Math.min(inc, up); if (top > lo) t += (top - lo) * r; if (up == null || inc <= up) break; lo = up; } return t; }
  const ahk = (y, v) => { const p = T(y).ahk; return v <= p.start ? p.max : Math.max(0, p.max - p.rate * (v - p.start)); };
  function ak(y, x) { if (x <= 0) return 0; for (const [lo, hi, pct, base, frm] of R.arbeidskorting[String(y)]) if (hi == null || x <= hi) return Math.max(0, base + pct * (x - frm)); return 0; }
  const iack = (y, x) => { const p = T(y).iack; return x <= p.min_income ? 0 : Math.min(p.max, p.rate * (x - p.min_income)); };
  const ewf = (y, woz) => { const p = T(y).ewf; return woz <= p.villa_threshold ? p.rate * woz : p.rate * p.villa_threshold + p.villa_rate * (woz - p.villa_threshold); };
  function ib(y, fiscal, ew, iackOn) {
    const inc = Math.max(0, fiscal + ew); let tax = box1(y, inc);
    if (ew < 0) { const top = T(y).brackets[1][0]; tax += Math.min(-ew, Math.max(0, fiscal - top)) * (T(y).brackets[2][1] - T(y).deduction_max_rate); }
    return Math.max(0, tax - ahk(y, inc) - ak(y, fiscal) - (iackOn ? iack(y, fiscal) : 0));
  }
  function person(p, hours, gross) {
    const h = hours == null ? (p.uren ?? p.contracturen ?? 40) : hours, base = gross == null ? p.bruto_jaar_incl_vakantiegeld : gross;
    const g = h ? base * (h / (p.contracturen || h || 1)) : 0;
    const pens = g ? (p.pensioenpremie_werknemer_pct || 0) * Math.max(0, g - (p.pensioen_franchise || 0)) : 0;
    return { gross: g, pension: pens, fiscal: g - pens };
  }
  // ---------------------------------------------------------------- kinderopvang
  function kotPct(y, ti) { const k = R.kinderopvangtoeslag[String(y)]; for (const [u, f, n] of k.tabel) if (ti <= u) return [Math.min(0.96, f + k.plus_eerste), Math.min(0.96, n + k.plus_volgende)]; const l = k.tabel.at(-1); return [l[1], l[2]]; }
  function opvang(y, ti, kids, allWork, flat) {
    const k = R.kinderopvangtoeslag[String(y)];
    const it = kids.map(c => [c.opvang === 'bso' ? (c.bso_uren_maand ?? 23 * (c.dagen_per_week || 0)) : (c.dagen_per_week || 0) * (c.uren_per_dag || 10) * (c.weken_per_jaar || 52) / 12,
                              c.uurtarief || 0, k.max_uurprijs[c.opvang || 'dagopvang'] ?? k.max_uurprijs.dagopvang]).sort((a, b) => b[0] - a[0]);
    const cost = it.reduce((s, [h, r]) => s + h * r, 0); let toeslag = 0;
    if (allWork && it.length) { const [f, n] = flat ? [flat, flat] : kotPct(y, ti); it.forEach(([h, r, mx], i) => { toeslag += Math.min(h, k.max_uren_maand) * Math.min(r, mx) * (i === 0 ? f : n); }); }
    return { cost_m: cost, toeslag_m: toeslag, net_m: cost - toeslag };
  }
  // ---------------------------------------------------------------- huishouden
  function household(sc, ewSaldo = 0) {
    const y = sc.year, pp = {}; for (const p of P) pp[p.id] = person(p, sc.hours?.[p.id], sc.gross?.[p.id]);
    const kids = KIDS.map((c, i) => ({ ...c, dagen_per_week: sc.days?.[i] ?? c.dagen_per_week }));
    const working = P.filter(p => pp[p.id].fiscal > 0).map(p => p.id);
    const low = working.slice().sort((a, b) => pp[a].fiscal - pp[b].fiscal)[0];
    const young = kids.length > 0, allWork = working.length === P.length;
    const iackOn = (id) => young && id === low && (allWork || P.length === 1);
    const base = {}; for (const p of P) base[p.id] = ib(y, pp[p.id].fiscal, 0, iackOn(p.id));
    const baseSum = Object.values(base).reduce((a, b) => a + b, 0); let best = baseSum;
    if (ewSaldo && P.length === 2) { const [a, b] = [P[0].id, P[1].id];
      for (let k = 0; k <= 10; k++) { const sh = k / 10; if (pp[b].fiscal <= 0 && sh > 0) continue;
        best = Math.min(best, ib(y, pp[a].fiscal, ewSaldo * (1 - sh), iackOn(a)) + ib(y, pp[b].fiscal, ewSaldo * sh, iackOn(b))); } }
    else if (ewSaldo) best = ib(y, pp[P[0].id].fiscal, ewSaldo, iackOn(P[0].id));
    const net = {}; for (const p of P) net[p.id] = pp[p.id].gross - pp[p.id].pension - base[p.id];
    const ti = Object.values(pp).reduce((s, v) => s + v.fiscal, 0) + ewSaldo;
    return { pp, net, netTotal_m: Object.values(net).reduce((a, b) => a + b, 0) / 12, ewBenefit_m: (baseSum - best) / 12, ti, allWork,
             iack: Object.fromEntries(P.map(p => [p.id, iackOn(p.id) ? iack(y, pp[p.id].fiscal) : 0])), ko: opvang(y, ti, kids, allWork, sc.kotFlat) };
  }
  // ---------------------------------------------------------------- hypotheek
  const annuity = (Pr, r, n = 360) => r === 0 ? Pr / n : Pr * (r / 12) / (1 - Math.pow(1 + r / 12, -n));
  const balanceAfter = (Pr, r, n, k) => { const m = annuity(Pr, r, n), i = r / 12; return Pr * Math.pow(1 + i, k) - m * (Math.pow(1 + i, k) - 1) / i; };
  function flp(ti, tr) { const H = R.hypotheek, rows = H.financieringslast_tabel_2026; let row = rows[0]; for (const r of rows) if (r[0] <= ti) row = r;
    for (let i = 0; i < H.rente_kolommen_bovengrens.length; i++) if (tr <= H.rente_kolommen_bovengrens[i] + 1e-9) return row[1 + i]; return row.at(-1); }
  function maxMortgage(sc, other_m = 0) {
    const H = R.hypotheek, ti = P.filter(p => p.vast_contract !== false).reduce((s, p) => s + person(p, sc.hours?.[p.id], sc.gross?.[p.id]).gross, 0);
    const tr = sc.fixYears >= 10 ? sc.rate : Math.max(sc.rate, H.toetsrente_short), pct = flp(ti, tr);
    const room = ti * pct / 12 - (C.huishouden.studieschuld_maand || 0) * H.studieschuld_factor - other_m;
    return { ti, tr, pct, max: Math.max(0, room) / annuity(1, tr) + (H.energy_label_bonus[sc.label || 'C'] || 0) };
  }
  const W = C.woning || {}, curDebt = (W.hypotheken || []).reduce((s, h) => s + (h.schuld || 0), 0);
  const curInterest = (W.hypotheken || []).filter(h => (h.box || 1) === 1).reduce((s, h) => s + (h.schuld || 0) * (h.rente || 0), 0);
  const savingsBase = (A.vermogen || []).filter(v => !['zakelijk', 'kinderen', 'beleggen'].includes(v.eigenaar)).reduce((s, v) => s + Math.max(0, v.saldo), 0);
  const curEwSaldo = (y) => W.type === 'koop' && W.woz ? ewf(y, W.woz) - curInterest : 0;
  function newHouse(sc) {
    const H = R.hypotheek, kk = sc.price * (sc.starter ? 0 : H.overdrachtsbelasting) + sc.costsOther, total = sc.price + kk + sc.reno;
    const equity = W.type === 'koop' ? Math.max(0, sc.saleValue * 0.985 - curDebt) : 0;
    const available = equity + savingsBase + (sc.useInvest ? (C.vermogen?.beleggingen || 0) : 0);
    const ownFunds = Math.min(sc.ownFunds, available), loan = Math.max(0, total - ownFunds);
    const famLoan = Math.min(sc.famLoan || 0, loan), famRate = sc.famRate || 0, fam_m = famLoan ? annuity(famLoan, famRate) : 0, bankLoan = loan - famLoan;
    const max = maxMortgage(sc, fam_m), maxLtv = sc.price + sc.reno * 0.75, capacity = Math.min(max.max + famLoan, maxLtv);
    const ewr = equity, deductible = Math.max(0, Math.min(loan, total - ewr)), dedShare = loan ? deductible / loan : 0;
    const bank_m = annuity(bankLoan, sc.rate), gross_m = bank_m + fam_m, interest1 = bankLoan * sc.rate + famLoan * famRate;
    const woz = sc.price * 0.93, ewSaldo = ewf(sc.year, woz) - interest1 * dedShare, h = household(sc, ewSaldo);
    const hf = sc.houseCostFactor || 1, energyNow = (A.begroting || []).filter(l => l.naam === 'Energie').reduce((s, l) => s + l.bedrag, 0);
    const extra = { 'Gemeentelijke lasten': (600 + 0.0012 * woz) / 12 * hf, 'Opstal + inboedel': (150 + 0.0004 * sc.price) / 12 * hf,
                    'Energie': (energyNow || 150) * 1.2 * hf, 'Onderhoudsreservering': (sc.price * 0.6 + sc.reno) * sc.maintPct / 12 };
    const extra_m = Object.values(extra).reduce((a, b) => a + b, 0), overrun = sc.reno * (sc.renoOverrun || 0);
    const k = sc.fixYears * 12, rest = balanceAfter(bankLoan, sc.rate, 360, Math.min(k, 359));
    const stress_m = annuity(rest, sc.stressRate, 360 - k) + fam_m;
    const hS = household(sc, ewf(sc.year, woz) - (rest * sc.stressRate) * dedShare);
    return { kk, total, equity, available, ownFunds, loan, bankLoan, famLoan, fam_m, bank_m, gross_m, interest1, max, maxLtv, capacity, ewr, deductible,
             woz, ewSaldo, ewBenefit_m: h.ewBenefit_m, net_m: gross_m - h.ewBenefit_m, extra, extra_m, overrun, buffer: available - ownFunds - overrun,
             rest, stress_net_m: stress_m - hS.ewBenefit_m, famGift: famLoan * Math.max(0, sc.rate - famRate), ok: bankLoan <= max.max + 1 && loan <= maxLtv };
  }
  // ---------------------------------------------------------------- begroting en sleutels
  const adj = C.begroting_aanpassingen || [];
  function budget(sc, h, X) {
    const lines = [];
    const replaced = new Set(adj.filter(a => a.vervangt).map(a => a.vervangt));
    for (const l of [...(A.begroting || []), ...adj]) {
      if (replaced.has(l.naam) && !l.vervangt) continue;
      if (l.tag === 'woning_huidig' && sc.phase === 'nieuw') continue;
      if (l.tag === 'opvang') continue;               // dynamisch hieronder
      lines.push({ ...l });
    }
    lines.push({ groep: 'Kinderopvang', naam: 'Kinderopvang (bruto, volgens schuifjes)', bedrag: h.ko.cost_m, scope: 'gez', zeker: 'hoog' });
    if (sc.phase === 'nieuw' && X) {
      lines.push({ groep: 'Nieuwe woning', naam: 'Hypotheek (bruto, rente + aflossing)', bedrag: X.bank_m, scope: 'gez', zeker: 'midden' });
      if (X.famLoan) lines.push({ groep: 'Nieuwe woning', naam: 'Familielening', bedrag: X.fam_m, scope: 'gez', zeker: 'midden' });
      for (const [n, v] of Object.entries(X.extra)) lines.push({ groep: 'Nieuwe woning', naam: n, bedrag: v, scope: 'gez', zeker: 'laag' });
    }
    if (sc.spendAdj) lines.push({ groep: 'Correctie risicoprofiel', naam: sc.spendAdj > 0 ? 'Uitgaven hoger dan begroot' : 'Besparingen gerealiseerd', bedrag: sc.spendAdj, scope: 'gez', zeker: 'laag' });
    const inc = [{ naam: 'Kinderopvangtoeslag', bedrag: h.ko.toeslag_m }, { naam: 'Kinderbijslag', bedrag: A.kinderbijslag_m || 0 },
                 { naam: 'Belastingvoordeel eigen woning', bedrag: sc.phase === 'nieuw' && X ? X.ewBenefit_m : h.ewBenefit_m }];
    const sum = (f) => lines.filter(f).reduce((a, l) => a + l.bedrag, 0);
    const gez = sum(l => l.scope === 'gez'), incSum = inc.reduce((a, l) => a + l.bedrag, 0);
    const fixed = {}, vari = {}; for (const p of P) { fixed[p.id] = sum(l => l.scope === p.id && l.vast_persoonlijk); vari[p.id] = sum(l => l.scope === p.id && !l.vast_persoonlijk); }
    const need = gez - incSum + (sc.bufferBuild || 0);
    const free = h.netTotal_m - need - Object.values(fixed).reduce((a, b) => a + b, 0) - Object.values(vari).reduce((a, b) => a + b, 0);
    return { lines, inc, gez, incSum, need, fixed, vari, free };
  }
  function keys(sc, h, b) {
    if (P.length !== 2) return [];
    const [a, c] = [P[0].id, P[1].id], nA = h.net[a] / 12, nC = h.net[c] / 12, N = b.need;
    const mk = (name, s, uitleg, clamp = true) => { if (clamp || !isFinite(s)) s = Math.min(1, Math.max(0, isFinite(s) ? s : 1));
      return { name, uitleg, share: s, dA: N * s, dC: N * (1 - s), leftA: nA - N * s - b.fixed[a], leftC: nC - N * (1 - s) - b.fixed[c] }; };
    const fA = nA - b.fixed[a], fC = nC - b.fixed[c], left = fA + fC - N;
    const full = Object.fromEntries(P.map(p => [p.id, person(p, p.contracturen, sc.gross?.[p.id]).gross]));
    return [
      mk('Bruto inkomen', h.pp[a].gross / ((h.pp[a].gross + h.pp[c].gross) || 1), 'Naar verhouding van het bruto inkomen.'),
      mk('Netto inkomen', nA / ((nA + nC) || 1), 'Naar verhouding van het netto inkomen.'),
      mk('Netto na eigen vaste lasten', fA / ((fA + fC) || 1), 'Naar wat ieder overhoudt na eigen vaste lasten (bv. studieschuld).'),
      mk('Gelijk vrij besteedbaar', nC > 0 ? (fA - left / 2) / N : 1, 'Beiden houden evenveel over (volledig delen).', nC <= 0),
      mk('Bruto, gecorrigeerd voor zorg', full[a] / ((full[a] + full[c]) || 1), 'Bruto, maar alsof beiden hun volle contracturen werken: minder werken voor de kinderen telt niet tegen degene die het doet.'),
    ];
  }
  function free(sc, phase) {
    if (phase === 'nieuw') { const X = newHouse(sc), h = household(sc, X.ewSaldo), b = budget({ ...sc, phase }, h, X); return { X, h, b, free: b.free }; }
    const h = household(sc, curEwSaldo(sc.year)), b = budget({ ...sc, phase: 'nu' }, h, null); return { X: null, h, b, free: b.free };
  }
  return { household, person, ib, ewf, opvang, maxMortgage, newHouse, budget, keys, free, annuity, curEwSaldo, P, KIDS };
}
if (typeof module !== 'undefined') module.exports = { makeModel };
