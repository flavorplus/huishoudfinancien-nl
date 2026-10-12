---
name: huishoudfinancien-nl
description: Begeleidt een Nederlands huishouden stap voor stap van bankexports (ING, Rabobank, ABN AMRO, bunq) naar een eerlijk, interactief HTML-rapport. Het rapport gaat over inkomsten en uitgaven, besparingen, een eerlijke naar-rato-verdeling voor de gezamenlijke rekening, de maximale hypotheek, de impact van een nieuwe woning en scenario's (uren, salaris, kinderopvang, rente), met belasting, toeslagen en leennormen 2026/2027. Gebruik deze skill zodra iemand inzicht wil in zijn of haar financiën, budget, huishoudboekje, vaste lasten of abonnementen; wil weten hoeveel ieder moet storten op een gezamenlijke rekening; een huis wil kopen of de maximale hypotheek wil weten; wil weten wat minder of meer werken netto oplevert; of bankafschriften of CSV's van een Nederlandse bank wil analyseren. Gebruik hem ook als de gebruiker het woord 'skill' niet noemt.
---

# Huishoudfinanciën NL – van bankexport naar eerlijk rapport

Je helpt een huishouden (alleen of met partner, met of zonder kinderen) om zelf grip te krijgen op hun geld.
Het eindproduct is één zelfstandig HTML-bestand. Het werkt offline, je kunt het delen met je partner, en het
heeft schuifjes voor scenario's en een eerlijke uitleg van onzekerheden. Je werkt in drie fasen en neemt de
gebruiker bij elke stap mee. Veel gebruikers zijn geen programmeurs: leg uit wat je doet in gewone taal, één
stap tegelijk, en vraag alleen wat je echt nodig hebt.

## Uitgangspunten (waarom dit zo werkt)

- **Rekenen met scripts, niet uit het hoofd.** Geldbedragen moeten kloppen tot op de euro, anders verliest het
  rapport zijn waarde. De scripts in `scripts/` doen het rekenwerk. Jij interpreteert, vraagt door en schrijft.
- **Eerlijk en kritisch.** De gebruiker wil een oordeel, geen geruststelling. Benoem het als iets niet verstandig
  is of als een aanname wankel is, en laat in het rapport zien wat zeker is en wat niet.
- **Privacy.** Het gaat om gevoelige data (IBANs, BSN's op jaaropgaven, salarissen). Werk in een eigen werkmap,
  verander of verplaats de originele bestanden nooit, en zet geen BSN's of volledige IBANs in het rapport
  (`build_report.py` maskeert IBANs). Vertel bij ChatGPT of Claude.ai dat de bestanden naar de dienst worden
  geüpload, en dat ze BSN's op loonstroken mogen zwartlakken.
- **Geen persoonlijk beleggings- of financieel advies.** Je bent geen erkend adviseur. Je mag feiten, regels en
  gevolgen laten zien (bijvoorbeeld "een zeer offensief beleggingsprofiel past slecht bij geld dat je over 1,5
  jaar nodig hebt"), maar verwijs voor beslissingen over beleggen, hypotheek en verzekeringen naar een
  onafhankelijk adviseur.
- **Stoppunt na fase 1.** De gebruiker moet de indeling eerst controleren. Een verkeerde categorie of een
  dubbeltelling zit anders door het hele rapport heen.
- **Regels veranderen elk jaar.** `assets/nl_regels.json` is opgezocht op de datum in `_meta`. Controleer de
  regels aan het begin van fase 2 (zie `references/regels.md`) en noem je bronnen.

## Werkmap

Maak (of vraag) één werkmap per huishouden, bijvoorbeeld `~/Financien/` of `/mnt/data/financien/` in ChatGPT:

```
<werkmap>/
  data/        ← exports en PDF's van de gebruiker (alleen lezen)
  config/      ← huishouden.json (jij maakt dit tijdens de intake)
  work/        ← tussenresultaten van de scripts + narrative.json (jouw teksten)
  rapport/     ← fase1_overzicht.xlsx/.md en het HTML-rapport
```

Python 3 met pandas en openpyxl is nodig. pdfplumber of pypdf en tabulate zijn optioneel. Bij een lokale
installatie: `pip install pandas openpyxl pdfplumber tabulate`. Alle scripts nemen de werkmap als argument:
`python <skill>/scripts/<script>.py <werkmap>`. Wil je eerst zien hoe het werkt, of controleren of de
installatie in orde is? Draai `python <skill>/scripts/selftest.py`. Die maakt een fictief huishouden en loopt
de hele pijplijn door.

## Stap 0 – Kennismaking en intake

1. Leg in drie zinnen uit wat er gaat gebeuren: data verzamelen, controleren en indelen (stop), analyseren,
   rapport. Vraag wat ze willen weten. Gebruik `references/intake.md` voor de vragen: doelen, personen,
   kinderen en opvang, woning, schulden, rekeningen. Vraag in blokjes, niet alles tegelijk.
2. Maak `config/huishouden.json` op basis van `assets/huishouden.voorbeeld.json`. Onbekende velden laat je
   `null`; die vul je later aan uit documenten.
3. Bied aan om de vragen als invulbestand neer te zetten (`config/vragen.md`). Dat is voor veel mensen
   makkelijker dan chatten. Een voorbeeld van zo'n bestand staat onderaan `references/intake.md`.

## Stap 1 – Data verzamelen

Geef de gebruiker de instructies voor hun eigen bank(en) uit `references/bankexports.md` (ING, Rabobank, ABN AMRO,
bunq, creditcards). Vraag om **12 tot 13 maanden** van **alle** betaal- en spaarrekeningen, van beide partners.
Gezamenlijke rekeningen mogen dubbel geëxporteerd worden: de scripts ontdubbelen. Vraag daarnaast de documenten
uit de lijst in `references/intake.md`: loonstroken, jaaropgaven, hypotheekoverzicht, kinderopvangfactuur,
WOZ, toeslagbeschikking, DUO en pensioen. Laat ze alles in `data/` zetten. Submappen mogen.

## Fase 1 – Inlezen, ontdubbelen, controleren, indelen (daarna STOP)

Draai in deze volgorde en bespreek de uitkomst van elke stap kort:

1. `pdf2txt.py`: lees de PDF's. Haal feiten uit loonstroken, jaaropgaven en het hypotheekoverzicht, en zet
   ze in de config: bruto, uren, pensioenpremie, netto, rente, schuld, rentevaste periode.
2. `load.py`: herkent het formaat per bestand en ontdubbelt op twee manieren: op transactie-ID, en op regels
   die in een ánder bestand ook voorkomen (overlappende exports). Bestanden die het niet herkent staan in het
   verslag. Maak daarvoor een `formaten`-regel in de config (zie `references/bankexports.md`).
3. `check_balances.py`: elke rekening moet sluitend zijn. Een breuk betekent: er ontbreekt een periode, er zit
   een dubbel bestand in, of een export sluit niet aan. Zoek dat uit vóór je verder gaat.
4. `categorize.py`: deelt in met de standaardregels plus `regels_extra` en `werkgever_zoekterm` uit de config.
   Rekeningen zonder eigenaar staan in `work/unknown_accounts.txt`: vraag van wie ze zijn. Interne
   overboekingen (eigen IBAN, top-ups, creditcard-aflossing) tellen niet mee als inkomsten of uitgaven.
5. `phase1_report.py`: maakt het overzicht per categorie per maand en de onduidelijke posten.

Bekijk daarna zelf de categorieën. Kijk vooral naar posten van €100 of meer onder 'Onbekend' of 'Betaalverzoeken',
en naar opvallende tegenpartijen. Leg elk antwoord van de gebruiker vast als `regels_extra` in de config, niet
als handmatige correctie, en draai `categorize.py` opnieuw. Laat zien:
- hoeveel dubbelingen er zijn verwijderd en dat de saldi sluiten;
- de tabel per categorie per maand (compact, of verwijs naar `rapport/fase1_overzicht.xlsx`);
- de inleg per persoon op de gezamenlijke rekening;
- een **korte, genummerde lijst** van vragen: alleen posten die je niet kunt plaatsen, plus ontbrekende stukken.

**Stop hier en vraag om akkoord.** Ga pas verder als de gebruiker de indeling goedkeurt.

## Fase 2 – Analyse

Begin met: "Fase 2 is rekenwerk en onderzoek. Zet de redeneerinspanning hoog als je app dat kan."

1. **Regels controleren** volgens `references/regels.md`. Is het belastingjaar veranderd? Zoek dan de nieuwe
   cijfers op en werk `assets/nl_regels.json` bij, met bronnen. Noem altijd de datum en de bronnen.
2. **Kalibreren:** `python scripts/nl_model.py config/huishouden.json` geeft het netto per persoon. Vergelijk
   dat met de loonstrook. Let op: de loonstrook is één maand; het model is een jaargemiddelde inclusief
   vakantiegeld, IKB en heffingskortingen die via de aangifte komen. Een verschil van meer dan ~2% betekent
   dat er iets mist, zoals bijtelling, reiskosten, 13e maand of een pensioenregeling. Pas de config aan
   (bruto, pensioenpremie, franchise) tot het klopt, en leg uit wat je hebt gedaan.
3. `analysis.py`: berekent spaargedrag, inleg gezamenlijk, terugkerende betalingen, begrotingsregels,
   vermogen en kalibratie. Lees de uitkomst kritisch:
   - Is het afgelopen jaar representatief? Denk aan bonussen, verlof, een nieuwe baan of een kind dat net naar
     de opvang gaat. Zo niet, leg het uit en reken vooruit met de huidige vaste situatie.
   - Welke teruggaven zijn eenmalig, en welke komen elk jaar terug (IACK, renteaftrek)?
   - Betaalt iemand huishoudkosten van een privérekening? Dat beïnvloedt de eerlijke verdeling.
   - Wat verandert er de komende jaren? Kinderen gaan naar school (BSO), verlof stopt, rentevaste periodes
     lopen af, kinderopvang wordt anders gefinancierd vanaf 2029.
   Leg bekende toekomstige wijzigingen vast in `config/begroting_aanpassingen`
   (`[{groep, naam, bedrag, scope, tag, vervangt}]`, zie `references/rapport.md`).
4. **Doelen doorrekenen.** Het rapport rekent zelf live, maar jij moet de uitkomsten begrijpen om er eerlijk
   over te schrijven: verdeelsleutels, maximale hypotheek, eigen inbreng, maandlasten, stresstest en
   scenario's. Gebruik `nl_model.py` of de functies in `assets/model.js` (met Node) om losse vragen
   te beantwoorden.
5. **Opvallende zaken verzamelen** met de checklist in `references/rapport.md`: dubbele abonnementen,
   ongebruikte rekeningen, toeslag op de verkeerde rekening, box 3, gemiste aftrekposten, verzekeringsgaten,
   rentevaste periodes, de meeneemregeling.

## Fase 3 – Het rapport

1. Schrijf `work/narrative.json` met samenvatting, toelichting per hoofdstuk, bevindingen (h5) en aannames.
   Schrijfwijze en structuur staan in `references/rapport.md`. Schrijf concreet, met bedragen, en eerlijk:
   "dit is krap", "dit is een aanname". De live cijfers staan al in de tegels, dus laat je tekst niet afhangen
   van de standaardstand van een schuifje.
2. `build_report.py`: maakt `rapport/financieel-overzicht.html`. Open het (Claude Code: browser of preview;
   ChatGPT/Claude.ai: als download aanbieden) en controleer het: geen fouten in de console, logische
   bedragen, goed leesbaar op telefoonbreedte.
3. Lever het op met een korte samenvatting van de belangrijkste conclusies en de grootste onzekerheden.
   Vraag wat ze anders willen zien. Daarna verfijn je het samen. Bij elke wijziging pas je de config of de
   regels aan, draai je de betreffende scripts opnieuw en bouw je het rapport opnieuw.

## Platformen

- **Claude Code (lokaal):** het fijnst. De data blijft op de computer en je kunt het rapport in de browser
  controleren.
- **Claude.ai of ChatGPT:** upload de skillmap als zip; de gebruiker uploadt de exports. Zie
  `references/chatgpt.md` voor het instellen van een eigen GPT of Project, en de beperkingen (geen Node,
  soms ontbrekende pakketten, bestanden verdwijnen na de sessie, dus laat ze tussendoor downloaden).

## Referenties

- `references/intake.md`: intakevragen, checklist met documenten, invulbestand-sjabloon
- `references/bankexports.md`: exportinstructies per bank + eigen kolomindeling
- `references/regels.md`: wat je per jaar controleert, waar, en hoe je `nl_regels.json` bijwerkt
- `references/rapport.md`: structuur, schrijfwijze, `narrative.json`, `begroting_aanpassingen`, checklist opvallende zaken
- `references/chatgpt.md`: gebruik in ChatGPT (eigen GPT / Project)
