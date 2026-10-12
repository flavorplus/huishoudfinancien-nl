# Regels controleren en bijwerken (begin van fase 2)

`assets/nl_regels.json` bevat de belasting-, toeslag- en leenregels die zijn opgezocht op de datum in
`_meta.geraadpleegd`. Ligt die datum meer dan een paar maanden terug, of is het belastingjaar veranderd,
controleer dan het onderstaande. Werk het JSON-bestand bij, met de bron per onderdeel in `_meta.bronnen`.
Kun je niet zoeken (geen internet)? Zeg dat dan expliciet in het rapport ("regels van <datum>, niet
gecontroleerd").

| Onderdeel | Sleutel in JSON | Waar zoeken (voorkeur: officieel) |
|---|---|---|
| Box 1-schijven en tarieven | `belasting.<jaar>.brackets` | belastingdienst.nl → tarieven en heffingskortingen |
| Algemene heffingskorting | `belasting.<jaar>.ahk` (max, start, rate) | belastingdienst.nl → tabel algemene heffingskorting |
| Arbeidskorting | `arbeidskorting.<jaar>` (knikpunten) | belastingdienst.nl → tabel arbeidskorting |
| IACK | `belasting.<jaar>.iack` | belastingdienst.nl (wordt vanaf 2027 in 9 stappen afgeschaft) |
| Eigenwoningforfait + villataks | `belasting.<jaar>.ewf` | belastingdienst.nl → eigenwoningforfait |
| Aftrektarief eigen woning | `belasting.<jaar>.deduction_max_rate` | = tarief 2e schijf |
| Box 3 | `belasting.<jaar>.box3` | belastingdienst.nl → box 3 (vanaf 2028 werkelijk rendement: let op) |
| Kinderopvangtoeslag | `kinderopvangtoeslag.<jaar>` (max uurprijs, tabel) | rijksoverheid.nl → bedragen kinderopvangtoeslag <jaar> |
| Stelsel 2029 | `kinderopvangtoeslag.2029` | rijksoverheid.nl → nieuwe financiering kinderopvang |
| Kindgebonden budget | `kindgebonden_budget` | belastingdienst.nl / rijksoverheid.nl |
| Financieringslastpercentages | `hypotheek.financieringslast_tabel_2026` | Staatscourant: "Wijzigingsregeling hypothecair krediet <jaar>" (Tabel 1) of Nibud |
| Toetsrente, energielabel, studieschuld | `hypotheek.*` | Staatscourant / Nibud / NHG |
| Overdrachtsbelasting, startersvrijstelling | `hypotheek.overdrachtsbelasting*` | belastingdienst.nl |
| Actuele hypotheekrente | `hypotheek.rente_sep_2026` | vergelijkingssite (geld.nl, hypotheekrente.nl) met datum |
| Schenkvrijstelling ouder–kind | `familielening` | belastingdienst.nl → schenkbelasting |

Na Prinsjesdag (derde dinsdag van september) staat het belastingplan voor volgend jaar online. Neem dat jaar
op als `"voorlopig": true` en markeer het in het rapport. Ontbreekt er een detail (bijvoorbeeld een knikpunt),
maak dan een aanname, zet die in een `_noot` en benoem hem in het rapport.

**Een nieuw jaar toevoegen:** kopieer het laatste jaarblok in `belasting`, `arbeidskorting` en
`kinderopvangtoeslag`, pas de cijfers aan, en zet in het rapport de knoppen voor het jaar. `model.js` en
`nl_model.py` lezen alles uit het JSON, dus code aanpassen is niet nodig.

## Bekende vereenvoudigingen (noem ze in de bijlage)
- Alleen werknemers onder de AOW-leeftijd. Ondernemers (zelfstandigenaftrek, MKB-winstvrijstelling), DGA's
  en AOW'ers vallen erbuiten.
- Pensioenpremie = percentage × (bruto − franchise). Een IKB of 13e maand neem je mee in het bruto.
- Box 3, kindgebonden budget, zorg- en huurtoeslag worden niet live gerekend. Schat ze apart als ze
  relevant zijn: lage inkomens (toeslagen) of veel vermogen (box 3).
- WW ≈ 70% van het loon tot het maximum dagloon (~€78k/jaar, controleren).
