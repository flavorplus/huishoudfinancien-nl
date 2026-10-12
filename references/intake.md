# Intake: vragen, documenten en invulbestand

Stel de vragen in blokjes van 3 à 4 en vat na elk blok samen wat je hebt genoteerd. Zet de antwoorden in
`config/huishouden.json` (zie `assets/huishouden.voorbeeld.json`).

## Blok 1 – Doelen (bepaalt wat je uitrekent)
1. Wat wil je vooral weten? Bijvoorbeeld: waar het geld blijft, hoeveel ieder moet storten op de gezamenlijke
   rekening, of jullie een (nieuw) huis kunnen betalen, wat minder of meer werken oplevert.
2. Is er een concreet plan? Zoals een koopsom, verbouwing, eigen inbreng, verhuizing, gezinsuitbreiding of minder
   gaan werken.
3. Met wie deel je het rapport? Met je partner, een adviseur, of alleen voor jezelf.

## Blok 2 – Personen en werk (per persoon)
- Naam (of bijnaam), geboortejaar
- Werk in loondienst? Werkgever (voor het herkennen van het salaris), contracturen, werkelijke uren, vast contract
- Bruto jaarsalaris inclusief vakantiegeld (uit de loonstrook of jaaropgave), 13e maand/IKB, variabel deel
- Pensioenregeling: werknemerspremie in % (loonstrook)
- Verlof (ouderschaps- of zwangerschapsverlof) en tot wanneer
- Ondernemer of zzp? Dan geldt het model maar deels; meld dat.

## Blok 3 – Kinderen en opvang
- Geboortedata (school vanaf 4 jaar, BSO, kinderbijslag per leeftijd)
- Soort opvang, dagen per week, uren per dag, uurtarief (staat op de factuur), geplande wijzigingen

## Blok 4 – Wonen, schulden, vermogen
- Huur of koop? Bij koop: WOZ, geschatte marktwaarde, per leningdeel de hypotheek (schuld, rente, maandlast,
  einde rentevaste periode), VvE.
- Tweede woning of vakantiehuis? (valt in box 3)
- Studieschuld (maandbedrag DUO), andere leningen, lease
- Spaarrekeningen en beleggingen die niet in de exports staan (waarde + datum)
- Familieleningen of schenkingen

## Blok 5 – Rekeningen
Lijst per rekening: bank, IBAN (de laatste 4 cijfers zijn genoeg om te praten), naam, eigenaar (persoon,
gezamenlijk, zakelijk, kinderen, beleggen), soort (betaal/spaar). Vraag ook hoe de gezamenlijke rekening
werkt: wie stort wat, wanneer, en welke potjes er zijn.

## Documentenlijst (laat ze in data/ zetten)
| Document | Waarvoor | Waar te vinden |
|---|---|---|
| Bankexports 12–13 maanden, alle rekeningen | alles | zie bankexports.md |
| Laatste loonstrook per persoon | netto-kalibratie, uren, pensioen | werkgever / salarisportal |
| Jaaropgave vorig jaar | fiscaal loon | werkgever |
| Aangifte inkomstenbelasting vorig jaar (PDF) | aftrekposten, box 3, toedeling | Mijn Belastingdienst → aangifte → afdrukken |
| Hypotheekoverzicht | schuld, rente, rentevast | app/site van de geldverstrekker |
| WOZ-beschikking | eigenwoningforfait, box 3 | gemeente / mijnoverheid.nl |
| Kinderopvangfactuur | uren, uurtarief | opvang-app (bv. Kids Office) |
| Toeslagbeschikking | controle toeslag | Mijn toeslagen |
| DUO-overzicht | studieschuld, maandbedrag | mijn.duo.nl |
| Pensioenoverzicht | pensioengat bij minder werken | mijnpensioenoverzicht.nl |
| Overzicht beleggingen/sparen elders | vermogen, box 3 | app van de aanbieder (een screenshot is goed) |

Tip voor de gebruiker: lak BSN's op loonstroken en jaaropgaven gerust zwart. Het model heeft ze niet nodig.

## Sjabloon invulbestand (config/vragen.md)
Gebruik dit voor de vragen ná fase 1. Zet onder elke vraag een regel `Antwoord:`. Vraag de gebruiker te
**bewaren** en dan in de chat "klaar" te zeggen. Mensen vergeten vaak op te slaan, dus controleer of er
antwoorden in staan.

```
# Vragen – vul je antwoord in achter "Antwoord:" (kort mag; "weet ik niet" ook)
## 1. <onderwerp>
<vraag met de concrete bedragen/datums erbij>
Antwoord:
...
## N. Ontbrekende stukken (zet ze in data/ en zet een X)
- [ ] ...
## Akkoord fase 1
Klopt de indeling op hoofdlijnen?
Antwoord:
```
