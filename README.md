Personeelsdata Opschoning & Validatie (SONJA)
+1
Dit Python-script (SONJA) automatiseert het proces van het samenvoegen, valideren en opschonen van personeelsgegevens. Het script is ontworpen om ruwe data uit verschillende bronnen te transformeren naar een uniform formaat voor gebruik in een exploitatieprogramma.
+3

🚀 Functionaliteiten

Data Merging: Combineert contractgegevens (Contractenlopend.csv) met algemene personeelsinformatie (PersoneelGeneral.csv) op basis van het personeels-ID.

Adres & Postcode Validatie:

Normaliseert straatnamen en huisnummers naar een standaard schrijfwijze.
+1

Koppelt woonplaatsen en postcodes aan een officiële database van Bpost om een PostcodeId te genereren.


Telefoonnummer Formattering: Gebruikt de phonenumbers bibliotheek om nummers automatisch om te zetten naar het internationale formaat (+32 ...).
+1

E-mail Correctie:

Valideert e-mailadressen en zet ze om naar kleine letters.
+1

Corrigeert automatisch veelvoorkomende typfouten in domeinen (zoals @telenet.be of @gmail.com) via fuzzy matching.
+1


Data Mapping: Zet tekstuele statuten (zoals "Arbeider" of "Bediende") en vestigingsnamen om naar numerieke ID's.


Foutdetectie & Notificatie: Spoort dubbele records, ontbrekende telefoonnummers of ontbrekende e-mailadressen op.


Automatische Rapportage: Verstuurt bij fouten of ontbrekende data direct een HTML-overzicht naar de beheerder via de Resend API.
+1

📂 Projectstructuur
Het script verwacht de volgende bestanden in een map genaamd data/:


Contractenlopend.csv: Lijst met actieve contracten (Encoding: Latin1, separator: ;).


PersoneelGeneral.csv: Algemene persoonsgegevens (Encoding: Latin1, separator: ;).


Postcodes_Bpost.csv: Officiële referentielijst van postcodes (Encoding: UTF-8, separator: ,).

🛠️ Installatie
Zorg dat Python geïnstalleerd is en installeer de benodigde bibliotheken:

Bash
pip install pandas resend phonenumbers email-validator
📋 Gebruik
Plaats de bronbestanden in de data/ map.

Pas indien nodig de API-key voor Resend aan in het script.

Voer het script uit:

Bash
python SONJA.py
Output
Het script genereert een opgeschoond bestand DATA\personeel.csv met UTF-8 encoding en puntkomma (;) als scheidingsteken.

📧 Foutrapportage
Indien er inconsistenties worden gevonden, wordt er automatisch een e-mail gestuurd naar marc.verbeke@waaslandia.be met tabellen voor:

Dubbele medewerkers.
+1

Medewerkers zonder GSM-nummer.

Medewerkers zonder privé e-mailadres.

Fouten in postcodes of woonplaatsen.
