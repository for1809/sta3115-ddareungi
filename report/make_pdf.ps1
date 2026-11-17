# report.html -> report.pdf with headless Microsoft Edge (Windows).
# Run from anywhere: powershell -File report/make_pdf.ps1
# Fonts: Noto Serif KR and Noto Sans KR must be installed (they are embedded in the PDF).
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$html = "file:///" + (Join-Path $here "report.html").Replace("\", "/")
$tmp = Join-Path $env:TEMP ("report_pdf_" + [guid]::NewGuid().ToString("N"))
$out = Join-Path $tmp "report.pdf"
New-Item -ItemType Directory -Force $tmp | Out-Null
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
# a fresh profile each run, so Edge never reuses cached figures
Start-Process -FilePath $edge -Wait -ArgumentList @(
  "--headless=new", "--disable-gpu", "--no-first-run", "--user-data-dir=$tmp\profile",
  "--no-pdf-header-footer", "--virtual-time-budget=6000", "--print-to-pdf=$out", $html)
if (-not (Test-Path $out)) { Write-Error "PDF was not written"; exit 1 }
Copy-Item $out (Join-Path $here "report.pdf") -Force
Remove-Item -LiteralPath $tmp -Recurse -Force
Write-Output "report.pdf written"
