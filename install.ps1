$ErrorActionPreference = 'Stop'
$repo = 'https://api.github.com/repos/karuott888999-ui/lilyyyy/zipball/copilot%2Fghost-mesh-panel'
$home = Join-Path $env:LOCALAPPDATA 'GhostMeshAI'
$tmp = Join-Path $env:TEMP ('ghost-mesh-' + [guid]::NewGuid().ToString('N'))
$zip = Join-Path $tmp 'source.zip'

Write-Host 'Ghost Mesh AI on kohalik prototüüp. See ei ühendu Ghosti serveri ega interneti AI teenusega.' -ForegroundColor Cyan
$answer = Read-Host 'Kas laadida rakenduse lähtekood GitHubist alla ja käivitada see ainult localhost-is? (J/N)'
if ($answer -notin @('J','j','Y','y')) { Write-Host 'Katkestatud.'; exit 0 }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3.10+ puudub. Paigalda Python ning märgi installimisel Add Python to PATH.' }
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
try {
  Invoke-WebRequest -Uri $repo -OutFile $zip
  Expand-Archive -Path $zip -DestinationPath $tmp -Force
  $source = Get-ChildItem $tmp -Directory | ForEach-Object { Join-Path $_.FullName 'mesh_ai' } | Where-Object { Test-Path $_ } | Select-Object -First 1
  if (-not $source) { throw 'Allalaetud arhiivist ei leitud mesh_ai kataloogi.' }
  New-Item -ItemType Directory -Path $home -Force | Out-Null
  if (Test-Path (Join-Path $home 'mesh_ai')) { Remove-Item (Join-Path $home 'mesh_ai') -Recurse -Force }
  Copy-Item $source (Join-Path $home 'mesh_ai') -Recurse -Force
  Write-Host "Rakendus paigaldatud: $home" -ForegroundColor Green
  Write-Host 'Käivitan kohaliku paneeli. Peatamiseks vajuta Ctrl+C.'
  Push-Location $home
  try { python -m mesh_ai } finally { Pop-Location }
} finally {
  Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
