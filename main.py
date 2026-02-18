import pandas as pd
import resend
import phonenumbers
from email_validator import validate_email, EmailNotValidError
import difflib
import re


# normaliseer adres
def normalize_adresregel(regel: str) -> str:
    if pd.isna(regel) or regel.strip() == "":
        return ""

    # splits op laatste cijfergroep (huisnummer)
    match = re.match(r"^(.*?)(\d+)$", regel.strip())
    if not match:
        # geen nummer gevonden, enkel straatnaam → hoofdletter per woord
        straat = " ".join(w.capitalize() for w in regel.strip().split())
        return straat

    straat, nummer = match.groups()
    straat = " ".join(w.capitalize() for w in straat.strip().split())
    return f"{straat} {nummer}"


# Check de telefoonnummers op schrijfwijze en zet dit naar standaard schrijfwijze
def normalize_phone(num, default_region="BE"):
    if pd.isna(num) or str(num).strip() == "":
        return ""
    try:
        # parse het nummer met standaard regio (BE = België)
        parsed = phonenumbers.parse(str(num), default_region)
        if phonenumbers.is_valid_number(parsed):
            # format naar internationaal formaat (+32 ...)
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        else:
            return str(num)  # teruggeven zoals het was als het niet geldig is
    except Exception:
        return str(num)


# lijst van veelgebruikte domeinen (wereldwijd + Europa)
COMMON_DOMAINS = {
    "gmail.com", "outlook.com", "hotmail.com", "live.com", "icloud.com", "yahoo.com",
    "mail.ru",
    "telenet.be", "skynet.be", "proximus.be",
    "ziggo.nl", "kpnmail.nl", "xs4all.nl",
    "gmx.de", "web.de", "t-online.de",
    "orange.fr", "sfr.fr", "free.fr", "laposte.net",
    "telefonica.net", "ono.com",
    "libero.it", "virgilio.it", "tin.it",
    "aon.at", "bluewin.ch",
    "online.no", "telia.com",
    "seznam.cz", "wp.pl"
}


# check en corrigeer e-mailadressen
def validate_and_correct(email: str) -> str | None:
    if pd.isna(email):
        return None
    email = email.strip().lower()
    try:
        valid = validate_email(email)
        return valid.normalized
    except EmailNotValidError:
        try:
            local, domain = email.split("@")
        except ValueError:
            return None
        match = difflib.get_close_matches(domain, COMMON_DOMAINS, n=1, cutoff=0.7)
        if match:
            corrected = f"{local}@{match[0]}"
            try:
                valid = validate_email(corrected)
                return valid.normalized
            except EmailNotValidError:
                return None
        return None


# Lees de CSV
contractenlopend = pd.read_csv(r"data\Contractenlopend.csv", encoding="Latin1", sep=";")
personeelgeneral = pd.read_csv(r"data\PersoneelGeneral.csv", encoding="latin1", sep=";")
postnummer = pd.read_csv(r"data\Postcodes_Bpost.csv", encoding="utf-8", sep=",")

# Merge contractenlopend en personeelgeneral op HFPersoneelsID
personeel = contractenlopend.merge(
    personeelgeneral[['HFPersoneelID', 'Naam', 'Voornaam', 'EmailPrive', 'EmailWerk',
                      'GeboorteDatum', 'Mobiel', 'Adres', 'Huisnr', 'Postcode', 'Plaats', 'Leiderschap']],
    on='HFPersoneelID',
    how='left'   # behoud alle rijen uit contractenlopend
)

# Merge personeel en postnummer op plaats en postcode
personeel["Plaats"] = personeel["Plaats"].str.strip().str.upper()
postnummer["Plaatsnaam"] = postnummer["Plaatsnaam"].str.strip().str.upper()
personeel["Postcode"] = personeel["Postcode"].astype(str).str.strip()
postnummer["Postcode"] = postnummer["Postcode"].astype(str).str.strip()
personeel = personeel.merge(
    postnummer[["Plaatsnaam", "Postcode", "Id"]],
    left_on=["Plaats", "Postcode"],   # kolommen uit personeel
    right_on=["Plaatsnaam", "Postcode"],  # kolommen uit postnummers
    how="left"
)
personeel["Id"] = personeel["Id"].astype("Int64")

# Nieuwe kolom AdresRegel maken: Adres + spatie + Huisnr
personeel["AdresRegel"] = personeel["Adres"].astype(str) + " " + personeel["Huisnr"].astype(str)

# Hernoem meerdere kolommen tegelijk
personeel = personeel.rename(columns={
    'HFPersoneelID': 'PersoneelsNummer',
    'Naam': 'Achternaam',
    'Voornaam': 'Voornaam',
    'Bedrijf': 'VestigingId',
    'MederwerkerType': 'functie',
    'Startdatum': 'StartDatum',
    'Einddatum': 'EindDatum',
    'Leiderschap': 'StatuutId',
    'Mobiel': 'Telefoonnummer',
    'Id': 'PostcodeId'
})

# nieuwe lege kolommen toevoegen
personeel["NiveauId"] = ""
personeel["RechtenSpeakapId"] = ""
personeel["Kledingbudget"] = ""

# Zorg dat startdatum & geboortedatum een echte datum is
personeel["GeboorteDatum"] = pd.to_datetime(personeel["GeboorteDatum"], format="%Y%m%d")
personeel["GeboorteDatum"] = personeel["GeboorteDatum"].dt.strftime("%Y-%m-%d")
personeel["StartDatum"] = pd.to_datetime(personeel["StartDatum"], format="%Y%m%d")
personeel["StartDatum"] = personeel["StartDatum"].dt.strftime("%Y-%m-%d")
personeel["EindDatum"] = pd.to_datetime(personeel["EindDatum"], format="%Y%m%d")
personeel["EindDatum"] = personeel["EindDatum"].dt.strftime("%Y-%m-%d")

# Normaliseer Telefoonnummer
personeel["Telefoonnummer"] = personeel["Telefoonnummer"].apply(normalize_phone)

# Normaliseer AdresRegel
personeel["AdresRegel"] = personeel["AdresRegel"].apply(normalize_adresregel)

# Normaliseer e-mail
personeel["EmailWerk"] = personeel["EmailWerk"].str.lower()
personeel["EmailPrive"] = personeel["EmailPrive"].str.lower()
personeel["EmailPrive"] = personeel["EmailPrive"].apply(validate_and_correct)

# zet StatuutId om naar Id
statuut_map = {
    "Arbeider": 1,
    "arbeider": 1,
    "Bediende": 2,
    "bediende": 2
}
personeel["StatuutId"] = personeel["StatuutId"].map(statuut_map).astype("Int64")

# zet VestigingId om naar Id
vestiging_map = {
    "Waaslandia Autobussen": 1,
    "Autobus Kruger": 2,
    "Kempische Automobielvereniging": 3,
    "Carolus Reizen": 4
}

# nieuwe kolom VestigingId vullen met codes
personeel["VestigingId"] = personeel["VestigingId"].map(vestiging_map).astype("Int64")

# Sorteer op personeelID
personeel = personeel.sort_values("PersoneelsNummer", ascending=True)

# zet de kolommen in de juiste volgorde
personeel = personeel[['PersoneelsNummer', 'Achternaam', 'Voornaam', 'GeboorteDatum', 'AdresRegel', 'PostcodeId',
                       'Telefoonnummer', 'EmailPrive', 'EmailWerk', 'VestigingId', "StartDatum", "EindDatum",
                       'StatuutId', "NiveauId", "RechtenSpeakapId", "Kledingbudget"
                       ]]

# Controle op dubbels
dubbels = personeel[personeel.duplicated(subset=["PersoneelsNummer", "Achternaam", "Voornaam"], keep=False)]

# Controle op ontbrekende Telefoonnummer
nophone = personeel[personeel["Telefoonnummer"].isna() | (personeel["Telefoonnummer"].str.strip() == "")]

# Controle op ontbrekende Emailprive
noemailprive = personeel[personeel["EmailPrive"].isna() | (personeel["EmailPrive"].str.strip() == "")]

# Controle op ontbrekende Postcode
nopostcodeid = personeel[personeel["PostcodeId"].isna()].copy()

# Verwijder dubbels, behoud enkel de eerste (dus de meest recente)
personeel = personeel.drop_duplicates(
    subset=["PersoneelsNummer", "Achternaam", "Voornaam"],
    keep="first"
)

# Sorteer op personeelID
personeel = personeel.sort_values("PersoneelsNummer", ascending=True)

# stuur mail als dubbels niet leeg is
if not dubbels.empty or not nophone.empty or not noemailprive.empty or not nopostcodeid.empty:
    # API key instellen
    resend.api_key = "re_9q3DrTLw_7fGuZSAWyxzxFPUPS6rb3HMW"
    # Zet DataFrame om naar HTML
    html_dubbels = dubbels.to_html(index=False)
    html_nophone = nophone.to_html(index=False)
    html_noemailprive = noemailprive.to_html(index=False)
    html_nopostcodeid = nopostcodeid.to_html(index=False)

    # Combineer ze in één HTML string
    html_nophone = html_nophone.replace(
        "<table",
        '<table style="border-collapse:collapse;width:100%;"'
    ).replace(
        "<th>",
        '<th style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    ).replace(
        "<td>",
        '<td style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    )

    html_dubbels = html_dubbels.replace(
        "<table",
        '<table style="border-collapse:collapse;width:100%;"'
    ).replace(
        "<th>",
        '<th style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    ).replace(
        "<td>",
        '<td style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    )

    html_noemailprive = html_noemailprive.replace(
        "<table",
        '<table style="border-collapse:collapse;width:100%;"'
    ).replace(
        "<th>",
        '<th style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    ).replace(
        "<td>",
        '<td style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    )

    html_nopostcodeid = html_nopostcodeid.replace(
        "<table",
        '<table style="border-collapse:collapse;width:100%;"'
    ).replace(
        "<th>",
        '<th style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    ).replace(
        "<td>",
        '<td style="border:1px solid #000;padding:6px;text-align:center;" align="center">'
    )

    html_content = f"""
                    <html>
                        <body>
                            <div style="text-align:left;margin-top: 20px;margin-bottom:20px;">
                                <h2 style="margin:0; font-family:Arial; font-size:20px;">
                                     Medewerkers dubbel in personeelsprogramma
                                </h2>
                            </div>
                            {html_dubbels}
                            <div style="text-align:left;margin-top: 20px;margin-bottom:20px;">
                                <h2 style="margin:0; font-family:Arial; font-size:20px;">
                                     Medewerkers zonder GSM nummer in personeelsprogramma
                                </h2>
                            </div>
                            {html_nophone}
                            <div style="text-align:left;margin-top: 20px;margin-bottom:20px;">
                                <h2 style="margin:0; font-family:Arial; font-size:20px;">
                                     Medewerkers zonder E-Mail prive in personeelsprogramma
                                </h2>
                            </div>
                            {html_noemailprive}
                            <div style="text-align:left;margin-top: 20px;margin-bottom:20px;">
                                <h2 style="margin:0; font-family:Arial; font-size:20px;">
                                     Medewerkers met een fout in postcode en/of woonplaats
                                </h2>
                            </div>
                            {html_nopostcodeid}
                        </body>
                    </html>
                    """

    resend.Emails.send({
        "from": "sonja@notifications.waaslandia.be",
        "to": ["marc.verbeke@waaslandia.be"],
        "subject": "Overzicht werknemer dubbel of met ontbrekende info in exploitatieprog",
        "html": html_content
    })

# Bewaar personeelgeneral als CSV met UTF-8 encoding en ; als separator
try:
    with open(r"DATA\personeel.csv", "a"):
        pass
except PermissionError:
    print(f"⚠️ Bestand DATA\\personeel.csv is geopend in een ander programma. Sluit het eerst.")
else:
    try:
        personeel.to_csv(r"DATA\personeel.csv", sep=";", encoding="utf-8", index=False)
        print("Bestand succesvol weggeschreven:", r"DATA\personeel.csv")
    except Exception as e:
        print("⚠️ Fout bij wegschrijven:", e)
