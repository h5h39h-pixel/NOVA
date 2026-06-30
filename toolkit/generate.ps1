<#
Text-to-image via local ComfyUI (auto-starts the ComfyUI server if needed).
  .\generate.ps1 "a cat sitting on a spaceship"
  .\generate.ps1 "futuristic city at sunset" -Model flux-schnell -Out C:\AI\out.png
  Models: sdxl (default) | flux-schnell | flux-dev
#>
param(
  [Parameter(Mandatory,Position=0)][string]$Prompt,
  [string]$Model='sdxl',
  [string]$Negative='blurry, low quality, distorted, watermark, text',
  [int]$Width=1024,[int]$Height=1024,
  [string]$Out,
  [string]$InitImage,          # IDEA-9: img2img — refine/edit an existing image instead of from noise
  [double]$Denoise=0.6         # how much to change the init image (0=identical, 1=ignore it)
)
$ErrorActionPreference='Stop'
$COMFY='C:\AI\ComfyUI'; $PY="$COMFY\venv\Scripts\python.exe"; $SRV='http://127.0.0.1:8188'
$cfg = switch ($Model) {
  'flux-schnell' { @{ ckpt='flux1-schnell-fp8.safetensors'; steps=4;  cfg=1.0; sampler='euler'; sched='simple' } }
  'flux-dev'     { @{ ckpt='flux1-dev-fp8.safetensors';     steps=20; cfg=1.0; sampler='euler'; sched='simple' } }
  default        { @{ ckpt='sd_xl_base_1.0.safetensors';    steps=25; cfg=7.0; sampler='dpmpp_2m'; sched='karras' } }
}
if (-not (Test-Path "$COMFY\models\checkpoints\$($cfg.ckpt)")) { throw "Model not downloaded yet: $($cfg.ckpt)" }

# Arabic prompt -> auto-translate to English (diffusion text encoders are English-trained)
if ($Prompt -match '\p{IsArabic}') {
  try {
    $tb = @{ model='qwen2.5:7b'; prompt="Translate this image description to concise English. Output ONLY the translation:`n$Prompt"; stream=$false; options=@{ temperature=0.2; num_predict=200 } } | ConvertTo-Json
    $en = (Invoke-RestMethod "http://127.0.0.1:11434/api/generate" -Method Post -Body ([Text.Encoding]::UTF8.GetBytes($tb)) -ContentType 'application/json; charset=utf-8' -TimeoutSec 60).response.Trim()
    if ($en) { Write-Host "Arabic prompt -> '$en'"; $Prompt = $en }
  } catch { Write-Host "(prompt translation skipped: $($_.Exception.Message))" }
}

# --- ensure ComfyUI server is up ---
function Up { try { Invoke-RestMethod "$SRV/system_stats" -TimeoutSec 3 | Out-Null; $true } catch { $false } }
if (-not (Up)) {
  Write-Host "Starting ComfyUI server..."
  Start-Process -WindowStyle Hidden -FilePath $PY -ArgumentList "$COMFY\main.py","--port","8188" -WorkingDirectory $COMFY
  for($i=0;$i -lt 90;$i++){ Start-Sleep 2; if(Up){break} }
  if (-not (Up)) { throw "ComfyUI did not start in time." }
}

$prefix = "gen_" + (Get-Random)
$seed = Get-Random -Maximum 2147483647
$denoise = 1.0
$g = @{
  '4' = @{ class_type='CheckpointLoaderSimple'; inputs=@{ ckpt_name=$cfg.ckpt } }
  '6' = @{ class_type='CLIPTextEncode'; inputs=@{ text=$Prompt;   clip=@('4',1) } }
  '7' = @{ class_type='CLIPTextEncode'; inputs=@{ text=$Negative; clip=@('4',1) } }
  '5' = @{ class_type='EmptyLatentImage'; inputs=@{ width=$Width; height=$Height; batch_size=1 } }
  '8' = @{ class_type='VAEDecode'; inputs=@{ samples=@('3',0); vae=@('4',2) } }
  '9' = @{ class_type='SaveImage'; inputs=@{ filename_prefix=$prefix; images=@('8',0) } }
}
# IDEA-9 img2img: if an init image is given, encode it to a latent and denoise from there
$latent = @('5',0)
if ($InitImage) {
  if (-not (Test-Path $InitImage)) { throw "InitImage not found: $InitImage" }
  $inName = "init_" + (Get-Random) + ([IO.Path]::GetExtension($InitImage))
  [IO.Directory]::CreateDirectory("$COMFY\input") | Out-Null
  Copy-Item $InitImage "$COMFY\input\$inName" -Force      # ComfyUI LoadImage reads from its input dir
  $g['10'] = @{ class_type='LoadImage'; inputs=@{ image=$inName } }
  $g['11'] = @{ class_type='VAEEncode'; inputs=@{ pixels=@('10',0); vae=@('4',2) } }
  $latent = @('11',0)
  $denoise = [math]::Min([math]::Max($Denoise,0.0),1.0)
  Write-Host ("img2img from '{0}' (denoise {1})" -f $InitImage, $denoise)
}
$g['3'] = @{ class_type='KSampler'; inputs=@{ seed=$seed; steps=$cfg.steps; cfg=$cfg.cfg; sampler_name=$cfg.sampler; scheduler=$cfg.sched; denoise=$denoise; model=@('4',0); positive=@('6',0); negative=@('7',0); latent_image=$latent } }
$body = @{ prompt=$g; client_id='agent' } | ConvertTo-Json -Depth 12
$sw=[System.Diagnostics.Stopwatch]::StartNew()
$resp = Invoke-RestMethod "$SRV/prompt" -Method Post -Body $body -ContentType application/json
$promptId = $resp.prompt_id
Write-Host "Queued ($Model, seed $seed). Generating..."
# poll history
$done=$false
for($i=0;$i -lt 180;$i++){
  Start-Sleep 1
  try { $h = Invoke-RestMethod "$SRV/history/$promptId" -TimeoutSec 5 } catch { continue }
  if ($h.$promptId) { $done=$true; break }
}
if (-not $done) { throw "generation timed out" }
$img = Get-ChildItem "$COMFY\output\$prefix*.png" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $img) { throw "no output image produced" }
if (-not $Out) { [IO.Directory]::CreateDirectory("C:\AI\agent-workspace\images")|Out-Null; $Out = "C:\AI\agent-workspace\images\image_$((Get-Date -Format 'HHmmss')).png" }
Copy-Item $img.FullName $Out -Force
"Image generated in {0}s -> {1}" -f [math]::Round($sw.Elapsed.TotalSeconds,1), $Out
