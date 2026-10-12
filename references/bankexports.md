# Bankexports – instructies per bank

Geef de gebruiker alleen de instructies voor de eigen bank(en). Menu's veranderen regelmatig. Lukt een stap
niet, laat dan een screenshot van het scherm maken; dan zoek je samen verder. Vraag om **12 tot 13 maanden**,
**alle rekeningen** (ook spaar- en gezamenlijke rekeningen), en van **beide partners**. Dubbele downloads
van een gezamenlijke rekening zijn geen probleem.

Exporteren gaat bijna altijd via **internetbankieren in de browser**, niet via de app.

## ING
1. Log in op Mijn ING (ing.nl) in de browser.
2. Ga naar **Service** (of het menu) → **Overzichten en downloads** / **Je downloads & overzichten** →
   **Af- en bijschrijvingen downloaden**.
3. Kies de rekening, de periode (max ~18 maanden terug) en het formaat **Kommagescheiden CSV** (of
   puntkommagescheiden). Kies Nederlands of Engels; beide worden herkend.
4. Herhaal dit voor elke betaalrekening. Spaarrekeningen geven bij ING vaak alleen een PDF. Noteer dan het
   saldo en de rente, en zet die in de config (`vermogen`).
- Herkend aan: kopregel `"Datum";"Naam / Omschrijving";"Rekening";…;"Af Bij";"Bedrag (EUR)";…;"Saldo na mutatie"`.
- Saldo na mutatie zit erin, dus de saldo-controle werkt.

## Rabobank
1. Log in op Rabo Internetbankieren (rabobank.nl) in de browser.
2. Ga naar je rekening → **Download transacties** (of **Betalen en sparen → Downloaden transacties**) →
   tabblad **Aangepast overzicht**.
3. Kies het formaat **CSV**, de rekening(en) en de periode. Per rekening kan maximaal ~12 maanden per keer,
   voor alle rekeningen samen soms minder. Download eventueel in twee delen. Overlap is geen probleem.
- Herkend aan: kopregel `"IBAN/BBAN","Munt","BIC","Volgnr","Datum",…,"Bedrag","Saldo na trn",…`.
- Volgnr wordt gebruikt om te ontdubbelen. Saldo na transactie zit erin.

## ABN AMRO
1. Log in op Internet Bankieren (abnamro.nl) in de browser.
2. Ga naar **Zelf regelen / Betalen** → **Bij- en afschrijvingen downloaden** (of: rekening → **Downloaden**).
3. Kies het formaat **TXT** (tab-gescheiden) of **MT940**. Beide worden herkend. Kies CAMT.053 of XLS alleen
   als de andere niet lukken; die worden niet automatisch gelezen. Periode: max ~18 maanden.
4. Kies bij MT940 als einddatum gisteren; het bestand loopt een werkdag achter.
- TXT/TAB: geen kopregel. Elke regel bevat rekeningnummer, munt, datum (JJJJMMDD), beginsaldo, eindsaldo,
  rentedatum, bedrag en omschrijving. Het IBAN wordt uit het rekeningnummer berekend.
- MT940 (`.STA`/`.940`): blokken met `:25:` (rekening), `:60F:`/`:62F:` (saldi), `:61:`/`:86:` (transacties).
  Ook ING- en Rabobank-MT940 worden gelezen.
- Een beleggingsrekening (geldrekening van een mandaat) heeft eigen stortingen en opnames. Die worden als
  intern gezien. Vraag de waarde van de portefeuille apart op (kwartaalrapport of screenshot).

## bunq (optioneel)
- In de app: Rekening → **Afschriften** → **CSV** per rekening. De kolommen verschillen per versie. Herkent
  `load.py` het bestand niet, maak dan een `formaten`-regel (zie hieronder).
- Gevorderd: via de bunq API kun je alle (sub)rekeningen in één keer exporteren met `payment_id` en
  `balance_after`. Dat formaat wordt herkend. Gezamenlijke rekeningen, via beide partners geëxporteerd,
  worden ontdubbeld op IBAN + payment_id. Trek de API-sleutel daarna in.

## Creditcards
- **American Express**: Online account → Afschriften → Download → CSV (één bestand per afschrift is prima).
  Wordt herkend aan de kolommen `Datum,Omschrijving,Bedrag`.
- **ICS (Visa/Mastercard via ING/ABN/Rabo)**: meestal alleen PDF. Neem de totaalbedragen per maand over,
  of laat ze ongemoeid. De aflossing van de creditcard staat al in de bankexport (als 'Intern' als de
  uitgaven er los in staan, anders als één uitgavepost).

## Andere banken of een afwijkend formaat
Zet in `config/huishouden.json`:
```json
"formaten": [{
  "naam": "ASN CSV", "bestand_patroon": "*asn*.csv", "scheidingsteken": ",",
  "kolommen": {"datum": "Boekingsdatum", "bedrag": "Bedrag", "tegenpartij": "Naam tegenrekening",
               "tegenrekening": "Tegenrekeningnummer", "omschrijving": "Omschrijving", "rekening": "Eigen rekening",
               "saldo": "Saldo na boeking"},
  "datum_formaat": "%d-%m-%Y"
}]
```
Optioneel: `"af_bij": "<kolom>"` met `"bij_waarden": ["Bij","Credit","C"]` als het bedrag altijd positief is.
Ontbreekt een rekeningkolom, gebruik dan `"rekening_iban": "NL.."`. Kijk eerst naar de eerste regels van
het bestand en vul dan de mapping in.

## Veelvoorkomende problemen
- *Saldo sluit niet*: er ontbreekt een maand, of een tweede export begint later dan de eerste eindigt.
  Laat de ontbrekende periode alsnog downloaden.
- *Bedragen 100× te groot of te klein*: verkeerd decimaalteken in een eigen formaat. Controleer de eerste regels.
- *Niets herkend*: het bestand is geopend en opnieuw opgeslagen in Excel. Laat het opnieuw downloaden en
  niet openen in Excel.
