# Ühine tuum ja mõttekaardi mälu

Painti visuaalne kaart salvestatakse nüüd kohaliku SQLite'i `paint_graphs` tabelisse, mitte ainult brauseri mällu. Keskne koordinaator leiab sõlmi märksõnade järgi ja liigub kasutaja loodud seoseid mööda maksimaalselt kaks sammu; tulemused piiratakse kümne sõlmega, tsükleid välditakse ning iga seoserada märgitakse kasutaja loodud andmeks. Värvid ei määra tähendust.

Koordinaator ei ole bioloogiline aju ega iseõppiv närvivõrk. See on seletatav andmebaasiotsing ja piiratud graafikäik. Alpha/Beta LLM-ile antakse koordinaatori kontekst ainult siis, kui kasutaja märgib kohaliku Ollama valiku sisse.

Varasem brauseri localStorage'i lõuend imporditakse paneelis olemasoleva JSON-impordi kaudu; uut serveripoolset salvestust kasutades jääb graph SQLite'i alles. Tee andmebaasist varukoopia enne failide eemaldamist.
