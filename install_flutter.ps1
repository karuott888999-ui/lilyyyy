# install_flutter.ps1
# Abi-skript Flutteri paigaldamiseks (Windows)
# Käivita administraatorina: Open PowerShell as Administrator
# Käskude jooksmiseks: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\install_flutter.ps1

Write-Host "=== Flutter install helper ===`n"

# 1) Proovi paigaldada Git, kui winget on olemas
if (Get-Command winget -ErrorAction SilentlyContinue) {
    Write-Host "Winget leitud — proovin paigaldada Git (kui veel puudu)..."
    try {
        winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
    } catch {
        Write-Host "Winget install Git ebaõnnestus või juba paigaldatud — jätkan..."
    }
} else {
    Write-Host "Winget ei leitud. Kui sul pole Git'i, palun paigalda see käsitsi: https://git-scm.com/download/win"
}

# 2) Ava Flutter Windows installileht brauseris, et saaksid ZIP-i alla laadida
$flutterDocs = 'https://docs.flutter.dev/get-started/install/windows'
Write-Host "`nAvan brauseris Flutteri installi lehe:" $flutterDocs
Start-Process $flutterDocs

Write-Host "`nJärgmiseks:"
Write-Host "1) Klõpsa \"Windows\" ja laadi alla STABLE channel ZIP (Flutter SDK)."
Write-Host "2) Ekstraheerige ZIP sisu kausta C:\\src\\flutter  (soovitatud)."
Write-Host "   Näide: C:\\src\\flutter\\bin\\flutter.bat peab olema olemas pärast ekstraheerimist."
Write-Host "Kui oled ekstraktinud, vajuta Enter siin skriptis, et jätkata."
Read-Host -Prompt "Kui oled valmis, vajuta Enter"

# 3) Kontrolli, et folder eksisteerib ja bin\flutter.bat olemas
$flutterBin = 'C:\src\flutter\bin\flutter.bat'
if (-Not (Test-Path $flutterBin)) {
    Write-Host "`nTundub, et C:\src\flutter\\bin\\flutter.bat ei leidunud."
    Write-Host "Palun kontrolli, et oled ekstraheerinud õigele teele (C:\\src\\flutter)."
    Write-Host "Kui ekstraheerimine on teises kaustas, muuda skriptis $flutterBin vastavalt."
    exit 1
}

# 4) Lisa kasutaja PATH-i (User environment)
$addPath = 'C:\src\flutter\bin'
$cur = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($cur -notlike "*$addPath*") {
    Write-Host "Lisame $addPath sinu USER PATH-i..."
    $new = $cur
    if ($new -ne $null -and $new -ne '') { $new += ';' }
    $new += $addPath
    setx Path $new | Out-Null
    Write-Host "PATH uuendatud (USER tasandil). Sul võib vaja olla uus terminaliakna avamine uus PATH-i koormamiseks."
} else {
    Write-Host "$addPath on juba PATH-is."
}

# 5) Loo ajutine keskkonnamuutus käesolevaks sessiooniks (nii et skript saab kohe 'flutter' käivitada)
$env:Path = $env:Path + ';' + $addPath

# 6) Kontrolli flutter versiooni ja run doctor
Write-Host "`nKäivitan flutter --version ja flutter doctor -v (see võib võtta aega)...`n"
try {
    & flutter --version
    & flutter doctor -v
} catch {
    Write-Host "Tekkis viga flutteri käivitamisel. Kui sõnum: 'flutter not found', ava uus terminal pärast PATH-i muutust või logi välja/uuesti sisse."
    exit 1
}

Write-Host "`nKui flutter doctor küsib täiendavaid komponente (Android SDK, lisalitsentsid), siis järgmised käsud võivad aidata:"
Write-Host "  flutter doctor --android-licenses"
Write-Host "Kui Android SDK pole paigaldatud, paigalda Android Studio ja selle kaudu SDK/Platform Tools."

Write-Host "`nValmis — nüüd saad oma projekti käivitada:"
Write-Host "cd C:\Users\$env:USERNAME\Desktop\lilyy"
Write-Host "flutter pub get"
Write-Host "flutter run -t lib\\main_secure.dart"

Write-Host "`nKui soovid, aitan aidata ka Android Studio/AVD seadistamisel ja telefoni ühendamisel."