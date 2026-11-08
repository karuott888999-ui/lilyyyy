# Ghost Mesh AI — kohaliku paneeli prototüüp

See on eraldiseisev Python 3 rakendus kaustas `mesh_ai/`. See ei muuda Ghosti ega teisi reposid ega kutsu Ghosti API-t. Server kuulab ainult `127.0.0.1:8765`; märkmed ja tagasiside salvestatakse sinu arvutis SQLite faili `mesh_memory.sqlite3`.

## Windowsi install

PowerShellis:

```powershell
irm https://raw.githubusercontent.com/karuott888999-ui/lilyyyy/copilot/ghost-mesh-panel/install.ps1 | iex
```

Skript küsib kinnitust, tõmbab selle repo haru ja kopeerib ainult `mesh_ai` rakenduse `%LOCALAPPDATA%\GhostMeshAI` alla. See ei muuda GitHubi repositooriumi. Python 3.10+ peab olema installitud ja `python` PATH-is. Avab veebipaneeli aadressil <http://127.0.0.1:8765>. Peata terminalis Ctrl+C-ga.

Käsitsi käivitamine repo juurest:

```powershell
python -m mesh_ai
```

## Funktsioonid ja ausad piirid

- Alpha ja Beta annavad kaks selgelt eristatud, reeglipõhist ülevaadet ning kasutavad küsimusega sobivaid kohalikke mälumärkmeid. Praegu pole ühendatud LLM-i: see prototüüp ei väida, et mudelid päriselt mõtlevad.
- Märkmed toetavad värvi, teksti suurust, tähtsust ja silte. Mälu tugevus on seletatav vananemisskoor. Automaatset kustutamist pole; „Unusta“ arhiveerib, mitte ei kustuta pöördumatult.
- Kasutaja saab paranduse talletada õppetunnina. Veasignaal arvutatakse tagasisidest; see ei ole päris viha ega tunne ning ei muuda koodi iseseisvalt.
- Reeglid/habitsid jäävad `pending` olekusse kuni kasutaja kinnitab. Agendid ei muuda ise turva-, võrgu- ega süsteemiseadeid.
- Rakendus ei tee pidevat veebiuuringut ega avatud interneti-/faili-/seadmejuurdepääsu. Kõik jääb kohalikuks.
- Ghosti ühendus pole selles prototüübis aktiveeritud. Hilisem ühendus vajab Ghosti poolel eraldi API-d, autentimist, kasutaja nõusolekut ning privaatsus- ja turvateste.

## Arendus ja kontroll

```powershell
python -m unittest discover -s mesh_ai/tests -v
```

Kasutaja andmebaas on rakenduse kaustas. Tee varukoopia enne kausta eemaldamist. Ära jaga `mesh_memory.sqlite3` faili, kui see sisaldab privaatseid märkmeid.
