# Gebruik in OpenAI Codex (CLI, IDE-extensie, app)

Codex ondersteunt skills in hetzelfde formaat als Claude: een map met `SKILL.md` plus `scripts/`, `references/`
en `assets/`. Deze skill werkt er dus zonder aanpassingen in. Codex draait lokaal op je eigen computer,
net als Claude Code. Je bankbestanden blijven op je schijf; alleen wat het model leest of laat zien gaat naar
OpenAI als gesprekscontext.

## Installeren
Codex zoekt skills onder meer in `~/.agents/skills/` (voor jezelf) en `.agents/skills/` in een repository.
Kies één van deze manieren:

1. **Via Codex zelf** (in een Codex-sessie):
   ```
   $skill-installer installeer de skill uit https://github.com/flavorplus/huishoudfinancien-nl
   ```
2. **Met git** (in de terminal):
   ```bash
   git clone https://github.com/flavorplus/huishoudfinancien-nl ~/.agents/skills/huishoudfinancien-nl
   ```
   Bijwerken doe je later met `git -C ~/.agents/skills/huishoudfinancien-nl pull`.
3. **Handmatig:** download `huishoudfinancien-nl.zip` onder Releases en pak de zip uit in `~/.agents/skills/`.
   Het resultaat is `~/.agents/skills/huishoudfinancien-nl/SKILL.md`.

Controleer met `/skills` of hij erbij staat. Staat hij er niet? Herstart Codex. Sommige oudere versies kijken
in `~/.codex/skills/`; zet de map daar neer als `~/.agents/skills/` niet werkt.

## Voorbereiden (eenmalig)
- **Python 3 met pakketten.** De sandbox van Codex blokkeert vaak internet, dus `pip install` binnen een
  sessie kan mislukken. Installeer daarom vooraf in je terminal:
  ```bash
  python3 -m pip install --user pandas openpyxl pdfplumber tabulate
  ```
  Alleen pandas en openpyxl zijn echt nodig; de rest heeft een terugvaloptie.
- **Werkmap.** Maak een lege map, bijvoorbeeld `~/Financien`, en zet je exports en PDF's in `~/Financien/data/`.
  Start Codex in die map. Zo kan Codex daar schrijven (`config/`, `work/`, `rapport/`) zonder dat je overal
  toestemming voor hoeft te geven.
- **Webzoeken voor fase 2.** Om de belastingregels te controleren moet Codex kunnen zoeken. Zet webzoeken aan
  als je versie dat ondersteunt (bijvoorbeeld met `codex --search`, of via de instellingen in de app). Kan dat
  niet, dan gebruikt de skill de opgeslagen regels en zegt dat in het rapport.

## Gebruiken
- Typ gewoon je vraag, bijvoorbeeld *"Ik wil inzicht in onze uitgaven en weten wat we kunnen lenen voor een
  huis"*. Codex kiest de skill zelf op basis van de beschrijving. Of roep hem expliciet aan met
  `$huishoudfinancien-nl`.
- De scripts draaien zo: `python3 ~/.agents/skills/huishoudfinancien-nl/scripts/<script>.py .`
  (met `.` als werkmap).
- Node is in Codex meestal beschikbaar. `selftest.py` vergelijkt dan ook het Python- en het JS-model.
- Het rapport open je zelf in de browser: `open rapport/financieel-overzicht.html` (macOS) of dubbelklik het
  bestand. Codex kan het niet altijd zelf bekijken. Laat het daarom ook op telefoonbreedte controleren door
  het venster smal te maken.

## Eerst proberen
```bash
python3 ~/.agents/skills/huishoudfinancien-nl/scripts/selftest.py ~/Financien-demo
open ~/Financien-demo/rapport/financieel-overzicht.html
```
