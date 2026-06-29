$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$TK = "C:\AI\agent-workspace\toolkit"
$OUT = "C:\AI\agent-workspace\videos"
$results = New-Object System.Collections.ArrayList
function Rec($cat,$name,$goal,$ok,$detail){
  $line = "[{0}] {1} · {2} :: {3}" -f $(if($ok){'PASS'}else{'FAIL'}), $cat, $name, $detail
  Write-Host $line
  [void]$results.Add($line)
}
function WaitFile($path,$sec){ for($i=0;$i -lt $sec;$i++){ if((Test-Path $path) -and ((Get-Item $path).Length -gt 1000)){return $true}; Start-Sleep 1 }; return (Test-Path $path) }

# 1. Image SDXL
$p1 = "$OUT\scen_sdxl.png"; Remove-Item $p1 -EA SilentlyContinue
& "$TK\generate.ps1" "a serene mountain lake at sunrise, photorealistic" -Model sdxl -Out $p1 2>&1 | Out-Null
$ok = WaitFile $p1 90
$sz = if($ok){[int]((Get-Item $p1).Length/1KB)}else{0}
Rec "Image" "SDXL generation" "generate a photorealistic image (SDXL)" $ok "file=$p1 size=${sz}KB"

# 2. Image flux-schnell
$p2 = "$OUT\scen_flux.png"; Remove-Item $p2 -EA SilentlyContinue
& "$TK\generate.ps1" "a cute robot reading a book, digital art" -Model flux-schnell -Out $p2 2>&1 | Out-Null
$ok = WaitFile $p2 90
$sz = if($ok){[int]((Get-Item $p2).Length/1KB)}else{0}
Rec "Image" "Flux-schnell generation" "generate an image (Flux schnell)" $ok "file=$p2 size=${sz}KB"

# 3. Video LTX-2B
$p3 = "$OUT\scen_video.mp4"; Remove-Item $p3 -EA SilentlyContinue
& "$TK\genvideo.ps1" "ocean waves at sunset, cinematic" -Ckpt "ltx-video-2b-v0.9.5.safetensors" -Length 49 -Steps 20 -Out $p3 2>&1 | Out-Null
$ok = WaitFile $p3 180
$sz = if($ok){[int]((Get-Item $p3).Length/1KB)}else{0}
Rec "Video" "LTX-2B generation" "generate a short cinematic video (2B)" $ok "file=$p3 size=${sz}KB"

# 4. TTS English to WAV
$w1 = "$env:TEMP\scen_en.wav"; Remove-Item $w1 -EA SilentlyContinue
& "$TK\speak.ps1" "Nova control center, all systems operational." -Save $w1 2>&1 | Out-Null
$ok = (Test-Path $w1) -and ((Get-Item $w1).Length -gt 1000)
$sz = if($ok){[int]((Get-Item $w1).Length/1KB)}else{0}
Rec "Voice" "TTS English to WAV" "save English speech to a WAV file" $ok "file=$w1 size=${sz}KB"

# 5. TTS Arabic to WAV
$w2 = "$env:TEMP\scen_ar.wav"; Remove-Item $w2 -EA SilentlyContinue
& "$TK\speak.ps1" "مركز نوفا للتحكم يعمل بكامل طاقته." -Save $w2 2>&1 | Out-Null
$ok = (Test-Path $w2) -and ((Get-Item $w2).Length -gt 1000)
$sz = if($ok){[int]((Get-Item $w2).Length/1KB)}else{0}
Rec "Voice" "TTS Arabic to WAV" "save Arabic speech to a WAV file" $ok "file=$w2 size=${sz}KB"

# build a text image for OCR/vision
Add-Type -AssemblyName System.Drawing
$imgp = "$env:TEMP\scen_ocr.png"
$bmp = New-Object System.Drawing.Bitmap(760,200)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::White)
$f = New-Object System.Drawing.Font('Arial',40,[System.Drawing.FontStyle]::Bold)
$g.DrawString('Nova OCR 7788 Test', $f, [System.Drawing.Brushes]::Black, 20, 70)
$g.Dispose(); $bmp.Save($imgp); $bmp.Dispose()

# 6. OCR (Windows OCR)
$txt = (& "$TK\ocr.ps1" $imgp 2>&1 | Out-String)
$ok = ($txt -match '7788') -and ($txt -match 'Nova')
Rec "Vision" "OCR (Windows)" "extract text from an image" $ok ("got: " + ($txt.Trim() -replace '\s+',' ').Substring(0,[Math]::Min(70,($txt.Trim() -replace '\s+',' ').Length)))

# 7. Vision (qwen2.5vl)
$txt2 = (& "$TK\ocr.ps1" $imgp -Vision 2>&1 | Out-String)
$ok = ($txt2 -match '7788') -or ($txt2 -match 'Nova')
Rec "Vision" "Vision model (qwen2.5vl)" "read image text with vision model" $ok ("got: " + ($txt2.Trim() -replace '\s+',' ').Substring(0,[Math]::Min(70,($txt2.Trim() -replace '\s+',' ').Length)))

$results -join "`n" | Set-Content "C:\Users\E121\AppData\Local\Temp\claude\C--AI\ddc0f43e-34e5-439b-acd3-3222c1072f6e\scratchpad\media_results.txt" -Encoding UTF8
$pass = ($results | Where-Object { $_ -match '^\[PASS\]' }).Count
Write-Host "`n==== media: $pass/$($results.Count) passed ===="
