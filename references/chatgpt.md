# Gebruik in ChatGPT (en Claude.ai)

De skill werkt in elke omgeving die Python kan draaien en bestanden kan lezen: Claude Code, Claude.ai met
code-uitvoering, of ChatGPT met "Code Interpreter / Data-analyse". Het rapport rekent in de browser van de
gebruiker, dus daar is geen Node nodig.

## Eenmalig instellen in ChatGPT
> Nieuwere versies van ChatGPT hebben ook **Skills** in de zijbalk (aanroepen met `@`). Zie je die optie, dan
> kun je proberen deze map als skill toe te voegen. Werkt dat niet of zie je de optie niet, gebruik dan een
> eigen GPT zoals hieronder.

**Optie A – eigen GPT (te delen met vrienden)**
1. ChatGPT → **Verkennen / GPT's** → **Maken** → **Configureren**.
2. Naam: "Huishoudfinanciën NL". Plak bij **Instructies** de inhoud van `CHATGPT-INSTRUCTIES.md` (uit de zip).
3. Upload bij **Kennis** het bestand `huishoudfinancien-nl.zip` (de hele skillmap gezipt).
4. Zet **Code Interpreter & data-analyse** en **Zoeken op het web** aan.
5. Opslaan → "Iedereen met de link". Deel de link. Iedereen gebruikt dan zijn eigen account, en de data
   van je vrienden komt niet bij jou terecht.

**Optie B – Project (voor jezelf)**
1. Maak een Project, plak de instructies bij projectinstructies en voeg de zip toe aan de projectbestanden.

## Hoe het in ChatGPT draait
- Bij de eerste stap pakt het model de zip uit: `/mnt/data/skill/` met `scripts/`, `assets/` en `references/`.
  De werkmap wordt `/mnt/data/financien/`, met de uploads in `data/`.
- Scripts draaien met `python /mnt/data/skill/scripts/<script>.py /mnt/data/financien`.
- pandas en openpyxl zijn er. pdfplumber of tabulate kunnen ontbreken; de scripts vallen dan terug op pypdf,
  PyMuPDF of platte tekst. Installeren met pip kan meestal niet (geen internet in de sandbox).
- Node ontbreekt. `selftest.py` slaat de JS-vergelijking dan over, en dat is prima.
- **Bestanden blijven niet bewaard** tussen gesprekken. Laat na fase 1 `config/huishouden.json` en
  `work/transactions.csv` downloaden. Laat na fase 3 het rapport downloaden. In een nieuw gesprek upload je
  die weer, zodat je niet opnieuw hoeft te beginnen.
- Uploadlimieten: veel losse CSV's kun je beter eerst zippen. Het model pakt ze uit in `data/`.

## Privacy om te vertellen aan de gebruiker
- De bankdata wordt geüpload naar OpenAI of Anthropic. Kijk in de instellingen of je gesprekken worden
  gebruikt voor training, en zet dat zo nodig uit (ChatGPT: Instellingen → Gegevensbeheer).
- Lak BSN's op loonstroken en jaaropgaven zwart. IBANs zijn nodig om rekeningen te herkennen, maar in het
  rapport worden ze gemaskeerd.
- Wil je het helemaal lokaal houden? Gebruik dan Claude Code op je eigen computer.
