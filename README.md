imp-simulator
=============

1. Starten in een nieuwe directory
2. git clone https://github.com/Foezjie/imp-simulator
3. Standaard zijn er 2 json files meegeleverd. 
      test.json.multi is een model dat over verschillende machines werkt
      test.json.simple is een model dat enkel een file en een directory deployed op 1 machine
4. De json die gebruikt wordt moet "model.json" genaamd zijn.
5. run dmv ./simulator.py
6. Het resultaat is te vinden in de database 'deployment.db'
    Deze heeft tabellen:
      Agent: de verschillende agents die in het model zaten
      Attributes: de attributen van alle objecten (naam | waarde | ID van de resource)
      Resource: de ID's van de resources.
      
Als er een fout opgemerkt wordt in de deployment volgorde (een file wordt gedeployed in een directory die nog niet bestaat bvb) wordt de resource niet weggeschreven in de deployment database en wordt dit aangegeven in de error logger.
Een tweede keer ./simulator.py oproepen komt overeen met nog eens de deployment proberen.

Interne werking:
----------------

Er wordt voor elke agent geprobeerde alle resources te deployen die geen requirements hebben.
De resources die succesvol gedeployed worden, worden dan verwijderd uit de (mogelijke) requirements van de overige resources.

Voordat een resource gedeployed wordt checkt de simulator of de deployment valide is. 
De regels hiervoor verschillen per resource:  
  Files en Directories: de parent folder moet bestaan
            ofwel moet deze reeds gedeployed zijn en dus staan in de deployment database
            ofwel is de parent folder een die behoort tot het besturingssysteem
              Een lijst van standaard mappen staat in het bestand filesystem
  Services:
    De packages die horen bij de service moeten al aanwezig zijn in de deployment database.
    De simulator weet welke files een service nodig heeft dankzij de pkgdata database. (Uitleg over hoe deze opgesteld werd onderaan)
  Packages: worden altijd gedeployed aangezien de package manager er voor verantwoordelijk is dat packages goed kunnen gedeployed worden, niet IMP

Opstellen van de pkgdata database:
----------------------------------
1. Ga naar http://mirror.eurid.eu/fedora/linux/releases/18/Everything/x86_64/os/repodata/
2. Download de bestanden die eindigen op "primary.sqlite.bz2" en "filelists.sqlite.bz2"
3. bzcat beide bestanden naar respectievelijk "primary.sqlite" en "filelists.sqlite"
4. 
>sqlite3 repodata.sqlite
sqlite> attach database 'filelists.sqlite' as filelists;
sqlite> attach database 'primary.sqlite' as prim;
sqlite> create table pkgdata as select name, dirname, filenames from prim.packages, filelists.filelist where packages.pkgKey=filelist.pkgKey;


