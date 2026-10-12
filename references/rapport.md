# Rapport: structuur, teksten en checklist

Het rapport (`assets/report_template.html`) rekent live met `assets/model.js`. Jij levert de teksten in
`work/narrative.json` en eventueel begrotingsaanpassingen in de config. Hoofdstukken:

0. **Samenvatting**: kerncijfers (live) + jouw oordeel in 3 tot 5 alinea's: wat gaat goed, waar lekt
   geld, wat betekent de wens (huis, minder werken), wat zijn de grootste risico's.
1. **Inkomsten en uitgaven**: historie, categorieën, terugkerende betalingen, besparingen, slimmere inrichting
   (potjes, toeslag naar de gezamenlijke rekening, buffer).
2. **Gezamenlijke rekening en verdeelsleutel**: wat de gezamenlijke rekening echt nodig heeft (inclusief
   jaarlijkse kosten en buffer), vijf verdeelsleutels (bruto, netto, netto na eigen vaste lasten, gelijk vrij
   besteedbaar, gecorrigeerd voor zorg) en een vergelijking met de huidige inleg.
3. **Nieuwe woning** (als `doelen.nieuwe_woning.actief`): financiering, eigen inbreng, maandlasten nu tegenover
   nieuw, stresstest.
4. **Hoe zeker is dit?**: drie risicoprofielen naast elkaar.
5. **Scenario's**: uren van de partner × salaris, met toeslag en leencapaciteit.
6. **Overige opvallende zaken**: jouw bevindingen (h5).
7. **Bijlage**: aannames, datacontrole (automatisch), bronnen (automatisch).

## narrative.json
```json
{
  "samenvatting": "<p><b>Kort en eerlijk.</b> …</p><p>…</p>",
  "h1": "<p><b>Oordeel.</b> …</p><h3>Waar valt te besparen</h3><table>…</table><h3>Slimmere inrichting</h3><ol>…</ol>",
  "h2": "<p>Hoe het nu gaat: … Advies: …</p>",
  "h3": "<ul><li><b>Volgorde verkoop/aankoop</b> …</li></ul>",
  "aannames": "<ul><li>…</li></ul>",
  "h5": [{"niveau": "bad", "titel": "…", "tekst": "…"}, {"niveau": "warn", "titel": "…", "tekst": "…"}]
}
```
`niveau`: `bad` = belangrijk risico, `warn` = actie nodig, `info` = goed om te weten, `good` = wat goed gaat.

## Schrijfwijze
- Nederlands, je/jullie, concreet, met bedragen per maand én per jaar waar dat helpt. Korte alinea's.
- Eerlijk: noem het krap als het krap is. Zeg wat een aanname is en hoe zwaar die weegt.
- Leg uit *waarom* iets zo is, niet alleen *wat* (bijvoorbeeld: "de toeslag is lager dan de opvangkosten,
  omdat jullie uurtarief boven de maximum uurprijs ligt").
- Geen beleggings- of hypotheekadvies. Wel feiten, gevolgen en vragen om aan een adviseur te stellen.
- Verdeelsleutel: wees fair naar de partner die minder werkt voor de kinderen. Noem het pensioengat, en
  overweeg een compensatie (pensioen of lijfrente).
- Historie is niet altijd representatief (bonussen, verlof, net gestarte opvang). Maak een brug van
  "afgelopen jaar" naar "nu".

## begroting_aanpassingen (config)
Basisbegroting = 12-maandsgemiddelden per (sub)categorie, met als scope de rekening waarvan het meestal betaald
wordt. Corrigeer bekende veranderingen:
```json
"begroting_aanpassingen": [
  {"groep": "Wonen", "naam": "VvE (nieuw bedrag 2027)", "bedrag": 410, "scope": "gez", "tag": "woning_huidig", "vervangt": "VvE", "zeker": "hoog"},
  {"groep": "Auto", "naam": "Reservering volgende auto", "bedrag": 150, "scope": "gez", "zeker": "laag"},
  {"groep": "Persoonlijk", "naam": "Telefoon Sam", "bedrag": 22, "scope": "p2", "vast_persoonlijk": true}
]
```
- `vervangt`: naam van een bestaande regel uit de analyse die hierdoor vervalt.
- `tag: "woning_huidig"`: vervalt in de situatie met een nieuwe woning.
- Huishoudkosten die privé worden betaald (boodschappen, klussen): zet `scope: "gez"`, zodat de gezamenlijke
  rekening het echte bedrag laat zien.

## Checklist opvallende zaken (fase 2)
- Dubbele of vergeten abonnementen: zie `analysis.json` → `terugkerend`, zeker bij "vaak 2× per maand".
  Denk aan streaming, telefoon, internet op twee adressen, Apple of Google, sportschool.
- Ongebruikte rekeningen, dubbele bankpakketten, creditcardkosten.
- Toeslag of kinderbijslag op een privérekening terwijl de kosten gezamenlijk zijn.
- Kinderopvang: uurtarief boven de maximum uurprijs (eigen bijdrage), juiste uren doorgegeven, toetsingsinkomen
  actueel (terugbetalen voorkomen).
- Box 3: vermogen boven de vrijstelling op 1 januari (inclusief tweede woning, beleggingen, kinderrekeningen).
- Gemiste aftrekposten: reisaftrek OV (reisverklaring), giften, lijfrente-jaarruimte (vooral bij hoge
  inkomens met een karige pensioenregeling), toedeling van de eigen woning aan de partner met het meeste voordeel.
- Hypotheek: einde rentevaste periode, meeneemregeling bij verhuizen, eigenwoningreserve/bijleenregeling,
  boetevrij aflossen.
- Verzekeringen: arbeidsongeschiktheid (WIA dekt tot het maximum dagloon), overlijdensrisico bij een
  hoge hypotheek, dubbele dekkingen.
- Rare pieken: eenmalige grote uitgaven, CJIB-boetes, incasso's van onbekende partijen.
- Een tweede woning: echte kosten (rente, VvE, lasten, box 3) tegenover gebruik en waardestijging; regels voor
  verhuur (Wet betaalbare huur, opkoopbescherming, toestemming geldverstrekker, Leegstandwet).
