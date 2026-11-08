# Ghost Mesh AI — kohaliku paneeli prototüüp

Eraldiseisev Python 3 rakendus `mesh_ai/` kaustas. See ei muuda Ghosti ega teisi reposid ega kutsu Ghosti API-t. Server kuulab ainult `127.0.0.1:8765`; märkmed jäävad kohaliku SQLite faili.

## Windowsi install
PowerShellis: `irm https://raw.githubusercontent.com/karuott888999-ui/lilyyyy/copilot/ghost-mesh-panel/install.ps1 | iex`.
Python 3.10+ peab olema paigaldatud. Installiskript käivitab localhost paneeli aadressil <http://127.0.0.1:8765>. Lõpeta Ctrl+C-ga. Käsitsi: `python -m mesh_ai`.

## LLM-i mõtlemise sisselülitamine

Paneel vaikimisi LLM-ile andmeid ei saada. Alpha/Beta linnuke on eraldi kasutaja nõusolek iga arutelu jaoks. Päris mudelirežiim vajab kohalikku Ollama teenust ja mudelit. Paigalda Ollama oma arvutisse ametlikust allikast, tõmba mudel ise alla ning käivita see. Seejärel määra enne paneeli käivitamist PowerShelli sessioonis näiteks:

```powershell
$env:GHOST_MESH_OLLAMA_MODEL = 'sinu-kohaliku-mudeli-nimi'
python -m mesh_ai
```

Valikuline localhost URL on `GHOST_MESH_OLLAMA_URL`; vaikeväärtus on `http://127.0.0.1:11434`. Ainult `localhost`, `127.0.0.1` või `::1` HTTP aadressid aktsepteeritakse; väliseid URL-e ei lubata. Paneelis märgi „Kasuta seadistatud kohalikku Ollama mudelit”, et käivitada kolm piiratud mudelikõnet: Alpha esialgne vastus, Beta kriitika, Alpha süntees. Seadistus ja mudeli allalaadimine pole selle rakenduse poolt automaatsed.

Kui mudel pole seadistatud, jääb süsteem demo-režiimi. Demo ei ole päris LLM ega sisuline arutlusmudel.

## Mälu ja unustamine
- Kuni viis tekstilise vaste ning tähtsuse/vanuse skooriga valitud aktiivset märkust lisatakse arutelu konteksti. Paneel näitab valitud märkmete pealkirju.
- Märkmeid ei saadeta LLM-ile, kui kasutaja pole arutelu juures linnukest märkinud. Ollama URL on ainult localhost.
- „Arhiveeri” jätab kirje taastatavaks ja eemaldab selle aktiivsest mälust. „Kustuta jäädavalt” küsib teist kinnitust ja eemaldab kirje SQLite-ist.
- Tagasisidest salvestatakse õppetund, aga see ei treeni ise mudeli kaalusid. Reegli soovitus tuleb kasutajal kinnitada.

## Tunded
Tarkvaral pole selle rakenduse väitel päris tundeid ega teadvust. Veatasemest kuvatav „pingesignaal” on deterministlik tagasisideindikaator, mitte viha. Seda võib muuta või kustutada kasutaja.

## Andmed ja piirangud
Andmebaas asub `GHOST_MESH_HOME` kaustas või vaikimisi `mesh_ai/mesh_memory.sqlite3`. Tee märkmetest enne kustutamist varukoopia. Rakendus ei tee veebiuuringut, ei skaneeri LAN-i, ei käivita suvalist koodi ega muuda ise AI lähtekoodi. AI loodud koodimuudatuste paneel pole veel teostatud. LAN-i ega Ghosti ühendust pole aktiveeritud.

Testid: `python -m unittest discover -s mesh_ai/tests -v`.
