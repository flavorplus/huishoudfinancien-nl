#!/usr/bin/env python3
"""Stap 3: interne overboekingen herkennen en transacties categoriseren met regels.

- Eigen rekeningen en eigenaren komen uit config/huishouden.json ("rekeningen", "eigen_ibans_extra").
  Elke rekening die in de exports voorkomt is per definitie eigen; staat hij niet in de config, dan wordt de
  eigenaar '?' en meldt het script hem (vraag de gebruiker van wie hij is).
- Eigen regels gaan vóór de standaardregels: config "regels_extra" = [{"categorie","sub","patroon","voorwaarde"}],
  voorwaarde = null | "in" | "out" | eigenaar-id. Zo leg je antwoorden van de gebruiker vast.
- Werkgevers: config personen[].werkgever_zoekterm (regex) -> Inkomen/Salaris <naam>.

Gebruik: python categorize.py <werkmap>  ->  work/transactions.csv, work/uncategorized.csv, work/unknown_accounts.txt
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

R = []


def rule(cat, sub, pat, cond=None):
    R.append((cat, sub, re.compile(pat, re.I), cond))


# --- interne stromen die niet via een eigen IBAN herkenbaar zijn
rule("Intern", "Creditcard aflossing", r"AMERICAN EXPRESS|HARTELIJK BEDANKT VOOR UW BETALING|ICS CUSTOMER|INTERNATIONAL CARD SERVICES|CREDITCARD AFREKENING")
rule("Intern", "Top-up eigen rekening", r"Top Up from (NL|DE)\d\d|TOP-UP VIA BUNQ|iDEAL Top Up")
rule("Intern", "Beleggingen (storting/opname)", r"STORTING BELEG|OPNAME BELEG|DEGIRO|FLATEX|MEESMAN|BRAND NEW DAY|TRADE REPUBLIC|BUX|SAXO|LYNX|PEAKS|EVERYDAYHEROES|NORTHERN TRUST")
# --- inkomen
rule("Inkomen", "Salaris (controleer werkgever)", r"SALARIS|SALARY|LOON |LOONBETALING|NETTOLOON", "in")
rule("Inkomen", "Uitkering (UWV/SVB)", r"\bUWV\b|WW-UITKERING|ZIEKTEWET|WIA", "in")
rule("Inkomen", "Kinderbijslag", r"SOCIALE VERZEKERINGSBANK|KINDERBIJSLAG", "in")
rule("Inkomen", "Kinderopvangtoeslag", r"KINDEROPVANG.*TOESLAG|VOORSCHOT KINDEROP|TOESLAG KINDEROPVANG", "in")
rule("Inkomen", "Zorgtoeslag", r"ZORGTOESLAG", "in")
rule("Inkomen", "Huurtoeslag", r"HUURTOESLAG", "in")
rule("Inkomen", "Kindgebonden budget", r"KINDGEBONDEN", "in")
rule("Inkomen", "Belastingteruggave", r"TERUGGAAF|BELASTINGDIENST", "in")
rule("Inkomen", "Rente", r"CREDITRENTE|RENTE EN/OF KOSTEN|RENTEBIJSCHRIJVING|Payday|RENTE SPAAR", "in")
rule("Inkomen", "Cashback/refund", r"REFUND|TERUGBETALING|RESTITUTIE|CASHBACK|teruggewonnen", "in")
rule("Inkomen", "Gift/schenking ontvangen", r"SCHENKING|VERJAARDAG|CADEAU", "in")
# --- wonen
rule("Wonen", "Hypotheek", r"HYPOTHE|HYP\.?NR|OBVION|FLORIUS|MUNT HYPOTHEKEN|NATIONALE-NEDERLANDEN HYP|ASR HYP|AEGON HYP|DE HYPOTHEEKSHOP|BIJBOUWE|VENN HYP|TULP HYP|ING HYPOTHEKEN|ROBUUST", "out")
rule("Wonen", "Huur", r"\bHUUR\b|HUURPENNING|WONINGCORPORATIE|WOONSTICHTING|YMERE|EIGEN HAARD|STADGENOOT|DE ALLIANTIE|VESTEDA|MVGM|HOLLAND2STAY", "out")
rule("Wonen", "VvE", r"\bVVE\b|VERENIGING VAN EIGENAARS|EIGENAARS|SERVICEKOSTEN", "out")
rule("Wonen", "Gemeentelijke belastingen / waterschap", r"GEMEENTE|BELASTINGSAMENWERKING|BSR|BGHU|COCENSUS|GBLT|SVHW|WATERSCHAP|HOOGHEEMRAADSCHAP|BELASTINGEN RIJNMOND|NOORD-HOLLAND NOORD|BWB|GEMEENTEBELASTINGEN", "out")
rule("Wonen", "Water", r"WATERNET|VITENS|EVIDES|\bPWN\b|BRABANT WATER|\bWML\b|OASEN|DUNEA|WATERBEDRIJF|\bWMD\b", "out")
rule("Wonen", "Energie", r"VATTENFALL|ENECO|ESSENT|GREENCHOICE|BUDGET ?ENERGIE|FRANK ENERGIE|TIBBER|ZONNEPLAN|ENERGIEDIRECT|PURE ENERGIE|VANDEBRON|OXXIO|ENGIE|DELTA ENERGIE|EASYENERGY|NLE |UNITED CONSUMERS|ANWB ENERGIE", "out")
rule("Wonen", "Onderhoud/klussen", r"HORNBACH|GAMMA|PRAXIS|KARWEI|HUBO|TOOLSTATION|BOUWMAAT|HOUTHANDEL|BOUWMARKT|FORMIDO|INSTALLAT|LOODGIETER|SCHILDERS?BEDRIJF|WARMTEPOMP|CV[- ]?ONDERHOUD|QUOOKER")
rule("Wonen", "Inrichting", r"IKEA|\bHEMA\b|\bACTION\b|KWANTUM|LEEN BAKKER|JYSK|FONQ|BLOKKER|XENOS|SOSTRENE|FLYING TIGER|LOODS 5|BEDDENWINKEL|AUPING|SWISS SENSE")
# --- kinderen
rule("Kinderopvang", "Kinderopvang", r"KINDEROPVANG|KINDERDAGVERBLIJF|\bKDV\b|\bBSO\b|PARTOU|KINDERDAM|SMALLSTEPS|HUMANKIND|KINDERRIJK|KIDS OFFICE|DEBICARE|SKIPPY|GASTOUDER|KINDERCENTRUM|KIDSFIRST|KION|KOMPAN|DOK ?12|BINK|SPRING KINDEROPVANG|2SAMEN|COMPASS KINDEROPVANG")
rule("Kinderen", "Kinderen overig", r"INTERTOYS|PRENATAL|BABY|SPEELGOED|BART SMIT|KINDERSCHOENEN|JOOLZ|BUGABOO|ZWEMLES|ZWEMSCHOOL|SCHOOLGELD|OUDERBIJDRAGE")
# --- verzekeringen, zorg
rule("Verzekeringen", "Zorgverzekering", r"ZILVEREN KRUIS|ZORGVERZEKER|MENZIS|\bCZ\b|\bVGZ\b|\bONVZ\b|\bDSW\b|ZEKUR|INTERPOLIS ZORG|ANDERZORG|FBTO ZORG|OHRA ZORG|UNIVE ZORG|DITZO|NATIONALE-NEDERLANDEN ZORG|\bIZA\b|\bIZZ\b|SALLAND|ZORG EN ZEKERHEID|DE FRIESLAND|HEALTHY ?WORLD|EUCARE")
rule("Verzekeringen", "Overige verzekeringen", r"VERZEKER|UNIVE|INTERPOLIS|CENTRAAL BEHEER|\bOHRA\b|FBTO|ALLIANZ|NATIONALE[- ]NEDERLANDEN|\bNN\b|\bASR\b|\bDELA\b|AEGON|REAAL|INSHARED|LEMONADE|ALLSECUR|DIRECT ?VERZEKERD|HEMA VERZEKERING|ANWB VERZ|ACHMEA|TAF BV|MONUTA|YAREN|ARAG|DAS RECHTSBIJSTAND")
rule("Gezondheid", "Zorgkosten", r"INFOMEDICS|APOTHEEK|APOTHEKEN|TANDARTS|MONDZORG|ORTHODONT|FYSIO|HUISARTS|ZIEKENHUIS|OPTIEK|HANS ANDERS|PEARLE|SPECSAVERS|EYE WISH|MEDISCH|PSYCHOLO|LOGOPED|DIETIST|CBR")
rule("Huisdier", "Huisdier", r"DIERENKLINIEK|DIERENARTS|ANICURA|DIERENSPECIAAL|PETS PLACE|ZOOPLUS|MEDPETS|JUMPER|BOERENBOND|WELKOOP|TOM&CO|TOM & CO")
# --- abonnementen
rule("Abonnementen", "Telecom/internet", r"ODIDO|T-MOBILE|ZIGGO|\bKPN\b|FREEDOM INTERNET|VODAFONE|SIMYO|\bBEN\b|LEBARA|YOUFONE|DELTA FIBER|CAIWAY|TELE2|HOLLANDSNIEUWE|LYCAMOBILE|SIMPEL|ROUTIT|CANAL DIGITAAL")
rule("Abonnementen", "Streaming/media", r"NETFLIX|SPOTIFY|DISNEY|VIDEOLAND|HBO|\bMAX\b|STORYTEL|AUDIBLE|YOUTUBE|APPLE\.COM/BILL|APPLE\.COM BILL|ITUNES|GOOGLE ?PLAY|AMAZON PRIME|AMZNPRIME|PRIME VIDEO|NPO|DE VOLKSKRANT|NRC|PAROOL|TROUW|\bAD\b|TELEGRAAF|FINANCIEELE DAGBLAD|BLENDLE|DPG MEDIA|MEDIAHUIS|KINDLE|VIAPLAY|ESPN|DAZN|SKYSHOWTIME")
rule("Abonnementen", "Software/cloud", r"OPENAI|CHATGPT|ANTHROPIC|CLAUDE|GITHUB|GOOGLE ONE|GOOGLE \*|DROPBOX|1PASSWORD|MICROSOFT|ADOBE|NOTION|ICLOUD|CANVA")
rule("Abonnementen", "Lidmaatschappen/goede doelen", r"MUSEUMKAART|NATUURMONUMENTEN|STAATSBOSBEHEER|LIDMAATSCHAP|CONTRIBUTIE|VERENIGING|UNICEF|KWF|ARTSEN ZONDER|GREENPEACE|WAKKER DIER|RODE KRUIS|AMNESTY|WNF|HARTSTICHTING|LOTERIJ|POSTCODE")
rule("Sport & hobby", "Sport", r"DAVID LLOYD|BASIC[- ]FIT|SPORTCITY|TRAINMORE|FIT FOR FREE|ANYTIME FITNESS|SPORTSCHOOL|TENNIS|HOCKEY|VOETBAL|GOLF|ZWEMBAD|DECATHLON|BEVER|RUN2DAY")
# --- schulden, belasting, bank
rule("Studieschuld/leningen", "DUO", r"\bDUO\b|DIENST UITVOERING ONDERWIJS")
rule("Studieschuld/leningen", "Lening/krediet", r"KREDIET|LENING|FINANCIERING|IN3|KLARNA|AFTERPAY|RIVERTY|BILLINK|SANTANDER CONSUMER|DEFAM|FREO|ALPHACREDIT")
rule("Belasting", "Belastingdienst", r"BELASTINGDIENST|CJIB BELAST", "out")
rule("Bankkosten", "Bankkosten", r"BASISPAKKET|ORANJEPAKKET|KOSTEN BETAALREKENING|PAKKET BETALEN|BUNQ B\.?V|bunq invoice|KOSTEN GELDOPNAME|RABO ?(BASIS|DIRECT) ?PAKKET|KOSTEN RABO|ABN AMRO BANK N\.V\.")
# --- vervoer
rule("Vervoer", "Brandstof/laden", r"TANK|SHELL|ESSO|\bBP\b|TOTALENERGIES|TINQ|ARAL|TANGO|ARGOS|FIELDMANN|AVIA|GULF|\bOMV\b|Q8|FASTNED|IONITY|ALLEGO|VATTENFALL INCHARGE|SHELL RECHARGE|EVBOX|NEWMOTION")
rule("Vervoer", "Motorrijtuigenbelasting", r"MOTORRIJTUIG|\b[0-9A-Z]{1,3}-[0-9A-Z]{2,3}-[0-9A-Z]{1,3}\b.*BELASTINGDIENST|BELASTINGDIENST.*\b[0-9A-Z]{1,3}-[0-9A-Z]{2,3}-[0-9A-Z]{1,3}\b")
rule("Vervoer", "Onderhoud/parkeren/wegenwacht", r"CARWASH|WASSTRAAT|PARKEER|PARKING|Q-PARK|YELLOWBRICK|PARKMOBILE|EASYPARK|ANWB|BANDEN|GARAGE|AUTOBEDRIJF|KWIK-?FIT|\bAPK\b|EUROMASTER|RDW")
rule("Vervoer", "OV/taxi/deelvervoer", r"\bNS\b|NS GROEP|NS INTERNATIONAAL|UBER(?! ?EATS)|BOLT|\bGVB\b|\bRET\b|\bHTM\b|OV-CHIPKAART|TRANSLINK|CONNEXXION|ARRIVA|\bQBUZZ\b|KEOLIS|EBS|TAXI|SWAPFIETS|DONKEY|FELYX|CHECK TECH|OVPAY|GREENWHEELS|MYWHEELS|SNAPPCAR")
rule("Vervoer", "Verkeersboetes", r"CJIB")
rule("Vervoer", "Lease/auto", r"LEASE|ALPHABET|ATHLON|LEASEPLAN|AYVENS|DIRECTLEASE|PRIVATE LEASE")
# --- huishouden
rule("Boodschappen", "Supermarkt", r"ALBERT HEIJN|\bAH |JUMBO|LIDL|ALDI|\bPLUS\b|DIRK|DEKAMARKT|HOOGVLIET|\bCOOP\b|\bSPAR\b|EKOPLAZA|MARQT|PICNIC|CRISP|SLIGRO|MAKRO|TOKO|VOMAR|EDEKA|REWE|NETTO MARKT|KAUFLAND|CARREFOUR|DELHAIZE|COLRUYT|BAKKER|SLAGER|KAASHANDEL|VISHANDEL|GROENTEBOER|NOTENBAR|POIESZ|JAN LINDERS|BONI|NETTORAMA|\bMARKT\b")
rule("Persoonlijke verzorging", "Drogist", r"ETOS|KRUIDVAT|DM[ -]?DROGERIE|DROGIST|TREKPLEISTER|DOUGLAS|RITUALS|LUSH|ICI PARIS|SEPHORA")
rule("Persoonlijke verzorging", "Kapper/beauty", r"KAPSALON|KAPPER|HAIR|BARBER|NAGELSTUDIO|SALON|BEAUTY|MASSAGE")
# --- vrije tijd / consumptie
rule("Shopping", "Online/kleding/elektronica", r"ZALANDO|VINTED|BOL\.COM|AMAZON|AMZN|COOLBLUE|MEDIAMARKT|TEMU|ALIEXPRESS|ALIPAY|SHEIN|H&M|UNIQLO|ZARA|COS |ARKET|WEEKDAY|MANGO|WE FASHION|C&A|PRIMARK|SCAPINO|VAN HAREN|NIKE|ADIDAS|APPLE STORE|MARKTPLAATS|WEHKAMP|OTTO|BIJENKORF|HUDSON|BRUNA|AKO|WIBRA|ZEEMAN|TUINCENTRUM|INTRATUIN|GROENRIJK|BLOEMEN|BLOEMIST|POSTNL|DHL|FEDEX")
rule("Horeca", "Bezorging", r"UBER ?EATS|THUISBEZORGD|TAKEAWAY|DELIVEROO|FLINK|GETIR|TOO GOOD TO GO|FOODTICKET")
rule("Horeca", "Restaurant/café", r"RESTAURANT|CAFE|CAFÉ|\bBAR\b|BISTRO|PIZZA|SUSHI|BURGER|KOFFIE|COFFEE|ESPRESSO|BRASSERIE|EETCAFE|GRILL|\bPHO\b|RAMEN|DINER|LUNCH|TAVERNE|MCDONALD|STARBUCKS|FEBO|KFC|SUBWAY|BURGER KING|DOMINO|NEW YORK PIZZA|WOK|SNACK|FRITUUR|FRIET|IJSSALON|GELATO|BAKERY|PANCAKE|PANNENKOEK|STRANDTENT|BEACH")
rule("Vakantie & uitjes", "Reizen/verblijf", r"HOTEL|BOOKING\.COM|AIRBNB|\bKLM\b|TRANSAVIA|EASYJET|RYANAIR|VUELING|LUFTHANSA|CORENDON|TUI|SUNWEB|D-REIZEN|CENTER PARCS|CAMPING|ROOMPOT|LANDAL|EUROCAMP|EXPEDIA|SKI|HOSTEL|FLIXBUS|EUROSTAR|THALYS|\bDB\b BAHN|SNCF")
rule("Vakantie & uitjes", "Uitjes", r"MUSEUM|DIERENTUIN|ARTIS|BLIJDORP|EFTELING|WALIBI|DUINRELL|TOVERLAND|SLAGHAREN|PATHE|PATHÉ|VUE |KINEPOLIS|BIOSCOOP|THEATER|CONCERT|TICKETMASTER|EVENTIM|FESTIVAL|SPEELTUIN|KINDERBOERDERIJ|APENHEUL|NEMO|ESCAPE")
rule("Cadeaus & giften", "Cadeaus", r"SINTERKLAAS|CADEAU|KADO|GREETZ|VERJAARDAG|BRUILOFT|HUWELIJK")
rule("Contant geld", "Geldopname", r"GELDMAAT|GELDAUTOMAAT|\bGEA\b|WITHDRAWAL|\bATM\b|OPNAME")
rule("Betaalverzoeken", "Tikkie/betaalverzoek (doel onbekend)", r"TIKKIE|BETAALVERZOEK|bunq\.me|paid with bunq")

OWNERS_PERSONAL = None


def build_rules(cfg):
    extra = []
    for p in cfg.get("huishouden", {}).get("personen", []):
        if p.get("werkgever_zoekterm"):
            extra.append(("Inkomen", f"Salaris {p['naam']}", re.compile(p["werkgever_zoekterm"], re.I), "in"))
    for r in cfg.get("regels_extra", []):
        extra.append((r["categorie"], r.get("sub", r["categorie"]), re.compile(r["patroon"], re.I), r.get("voorwaarde")))
    return extra + R


def classify(df, cfg):
    rules = build_rules(cfg)
    accounts = {r["iban"]: r for r in cfg.get("rekeningen", [])}
    own = set(df.account_iban) | set(accounts) | set(cfg.get("eigen_ibans_extra", []))
    persons = {p["id"] for p in cfg.get("huishouden", {}).get("personen", [])}
    owner = df.account_iban.map(lambda i: accounts.get(i, {}).get("eigenaar", "?"))
    # top-ups: echte eigen IBAN staat in de omschrijving
    iban_in_desc = df.description.fillna("").str.extract(r"((?:NL|DE|BE)\d\d[A-Z]{4}\d{7,10})", expand=False)
    topup = df.counterparty_name.fillna("").str.contains(r"top-up via bunq|Adyen Merchant Payout|via bunq$", case=False) & iban_in_desc.isin(own)
    cp_iban = df.counterparty_iban.fillna("").where(~topup, iban_in_desc)
    cp_owner = cp_iban.map(lambda i: accounts.get(i, {}).get("eigenaar", "eigen?" if i in own else "extern"))
    text = (df.counterparty_name.fillna("") + " | " + df.description.fillna("")).str.replace(r"\s+", " ", regex=True)
    cats, subs, hits = [], [], []
    for t, amt, o, co, ci in zip(text, df.amount, owner, cp_owner, cp_iban):
        cat = sub = None
        hit = ""
        if ci and ci in own:
            cat, hit = "Intern", "eigen IBAN"
            if o in persons and co == "gezamenlijk":
                sub = f"Inleg gezamenlijk ({o})" if amt < 0 else f"Van gezamenlijk naar {o}"
            elif o == "gezamenlijk" and co in persons:
                sub = f"Inleg gezamenlijk ({co})" if amt > 0 else f"Van gezamenlijk naar {co}"
            elif o == co:
                sub = f"Binnen {o}"
            else:
                sub = f"{o} <-> {co}"
        else:
            for c, s, pat, cond in rules:
                if cond == "in" and amt <= 0: continue
                if cond == "out" and amt >= 0: continue
                if cond not in (None, "in", "out") and cond != o: continue
                if pat.search(t):
                    cat, sub, hit = c, s, pat.pattern[:50]
                    break
        if o in ("zakelijk", "kinderen", "beleggen") and cat != "Intern":
            cat, sub = {"zakelijk": "Zakelijk", "kinderen": "Kinderrekening", "beleggen": "Beleggen"}[o], sub or "overig"
        if cat is None:
            if -100 < amt < 0:
                cat, sub = "Overig", "Diversen (<€100, geen regel)"
            else:
                cat, sub = "Onbekend", "Ontvangst onbekend" if amt > 0 else "Uitgave onbekend (≥€100)"
        cats.append(cat); subs.append(sub); hits.append(hit)
    df = df.assign(owner=owner, counterparty_owner=cp_owner, category=cats, subcategory=subs, rule=hits)
    df["month"] = df.date.dt.to_period("M").astype(str)
    return df


def main(workdir: Path):
    work = workdir / "work"
    cfg_path = workdir / "config" / "huishouden.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    df = pd.read_csv(work / "transactions_raw.csv", parse_dates=["date"], dtype={"tx_id": str, "counterparty_iban": str})
    df = classify(df, cfg)
    df.to_csv(work / "transactions.csv", index=False)
    unk = df[df.category == "Onbekend"]
    unk.to_csv(work / "uncategorized.csv", index=False)
    unknown_acc = sorted(df[df.owner == "?"].account_iban.unique())
    (work / "unknown_accounts.txt").write_text("\n".join(unknown_acc))
    print(df.category.value_counts().to_string())
    print(f"\nOnbekend: {len(unk)} posten (≥€100 of ontvangsten), som {unk.amount.sum():.2f}")
    if unknown_acc:
        print("Rekeningen zonder eigenaar in de config (vraag de gebruiker):", ", ".join(unknown_acc))


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve())
