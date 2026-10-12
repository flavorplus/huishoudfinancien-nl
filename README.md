# Huishoudfinanciën NL

Een AI-assistent (Claude of ChatGPT) leidt je stap voor stap van je bankexports naar een eerlijk, interactief
rapport. Het rapport is één HTML-bestand dat je offline opent en kunt delen met je partner. Het gaat over:

- waar je geld blijft, waar je kunt besparen en hoe je je rekeningen en potjes slimmer inricht;
- een eerlijke verdeling van de inleg op de gezamenlijke rekening (vijf verdeelsleutels naast elkaar);
- je maximale hypotheek, en wat een nieuwe woning doet met je maandlasten en buffer, met stresstest;
- scenario's met schuifjes: minder of meer werken, salaris, kinderopvang, rente, eigen inbreng;
- belasting, kinderopvangtoeslag en leennormen 2026/2027, met bronnen.

Werkt met exports van **ING, Rabobank, ABN AMRO** (en bunq, Amex, of elk CSV-formaat via een kolomindeling).

## Installeren
**Claude Code (aanbevolen: alles blijft op je eigen computer)**
1. Zet de map `huishoudfinancien-nl` in `~/.claude/skills/`. Of installeer het bestand `huishoudfinancien-nl.skill`.
2. Zorg voor Python 3 met `pip install pandas openpyxl pdfplumber tabulate`.
3. Open Claude Code in een lege map en zeg bijvoorbeeld: *"Ik wil inzicht in onze financiën en weten of we een huis kunnen kopen."*

**Claude.ai**: Instellingen → Mogelijkheden → Skills → upload `huishoudfinancien-nl.skill` (of de zip).
Zet code-uitvoering aan.

**ChatGPT**: zie `references/chatgpt.md`. Kort: maak een eigen GPT, plak `CHATGPT-INSTRUCTIES.md` bij
Instructies, upload `huishoudfinancien-nl.zip` bij Kennis, en zet Code Interpreter en Zoeken aan.

## Eerst proberen zonder eigen data
`python scripts/selftest.py demo` maakt een fictief huishouden en een demorapport in `demo/rapport/`.

## Privacy
Je bankdata is gevoelig. Met Claude Code blijft alles lokaal. Met ChatGPT of Claude.ai upload je de bestanden
naar die dienst; kijk dan in de instellingen of je gesprekken voor training worden gebruikt. Lak BSN's op
loonstroken zwart. Het rapport maskeert IBANs.

## Belangrijk
Dit is een hulpmiddel voor inzicht, geen erkend financieel, fiscaal of hypotheekadvies. De regels worden elk jaar
gecontroleerd en bijgewerkt (`assets/nl_regels.json`, zie `references/regels.md`). Laat grote beslissingen toetsen door
een onafhankelijk adviseur.

## Downloads
De kant-en-klare pakketten (`huishoudfinancien-nl.skill` voor Claude, `huishoudfinancien-nl.zip` + `CHATGPT-INSTRUCTIES.md` voor ChatGPT) staan onder **Releases** rechts op deze pagina.

## Licentie
MIT – zie `LICENSE`. Gebruik op eigen risico; geen financieel advies.
