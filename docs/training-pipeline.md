# Training pipeline (the `nova-local` continuous‑learning loop)

The LoRA fine‑tuning pipeline lives **outside this repo** in `C:\AI\training`. The Control Center
**orchestrates and monitors** it (Training Studio + the `/learn/*` and `/training/*` routes) but does
**not own** these scripts. This doc captures what they do so the integration is understandable and the
external dependency is no longer a black box (DOC‑3; addresses OUT‑2's "pipeline external" caveat).

> **Boundary:** treat `C:\AI\training\*` as an external dependency. We parse its progress/logs and
> trigger it; we don't modify it from here without the owner's intent.

## Files (`C:\AI\training`)

| File | Role |
|---|---|
| `learn.ps1` | **Entry point for continuous learning.** Harvests new chats, then retrains. `-HarvestOnly` collects data without training. |
| `harvest_chats.py` | Collects real conversations from the Control Center DB (`data/control.db` → `chat`) and Open WebUI (`webui.db` in the `open-webui` container, best‑effort), converts them to SFT examples, de‑dupes, appends to `dataset_learned.jsonl`, and rebuilds `dataset_combined.jsonl`. |
| `make_dataset.py` | (Re)builds the curated base dataset. |
| `train_lora.py` | **The actual fine‑tune.** LoRA on the base model (bf16, RTX 5090, no bitsandbytes), then merges the adapter to safetensors so Ollama can import it. Emits `[PROGRESS] step=… total=… loss=… eta=…` lines. |
| `run_all.ps1` | **Unattended pipeline.** Installs PyTorch (CUDA 12.8 / Blackwell) + training libs, rebuilds the dataset, trains+merges, registers the model in Ollama, smoke‑tests it. Logs → `C:\AI\overnight_training.log`, report → `C:\AI\training_report.txt`. |
| `Modelfile` | Ollama model definition: `FROM C:\AI\training\merged` + the Nova system prompt + `temperature 0.4`, `num_ctx 4096`. |
| `dataset.jsonl` | The curated base examples (chat format: `{messages:[…]}`). |
| `dataset_learned.jsonl` | Grows from real harvested chats. |
| `dataset_combined.jsonl` | `base + learned` — the file actually trained on. |
| `adapter/`, `merged/`, `checkpoints/` | LoRA adapter, merged model, training checkpoints. |

## Data flow

```
Control Center chats ─┐
Open WebUI chats ─────┼─> harvest_chats.py ─> dataset_learned.jsonl ─┐
curated base ─ make_dataset.py ─> dataset.jsonl ────────────────────┼─> dataset_combined.jsonl
                                                                     │
dataset_combined.jsonl ─> train_lora.py ─(LoRA + merge)─> merged/ ──> ollama create nova-local
                                                                              │
                                                              appears in Ollama + Open WebUI
```

- **Base model:** `Qwen/Qwen2.5-7B-Instruct` (overridable via `$env:BASE_MODEL`). First train downloads
  ~15 GB.
- **Output model:** Ollama tag **`nova-local`** (15.2 GB locally; see the memory note). Auto‑appears in
  Open WebUI.

## How the Control Center integrates

- **Training Studio** (`#/training`) + `nova/services/training.py` + `nova/api/training.py`.
- `_parse_train_sub()` parses the `[PROGRESS]` lines into `{step,total,percent,loss,eta}` for the live
  progress UI.
- `learning_stats()` / `training_history()` read the datasets + the `training_runs` table.
- `append_learned()` / `rebuild_combined()` manage the learned/combined datasets from the app side.
- The dataset paths are configured in `config.py` (`TRAIN_DIR`, `DS_BASE`, `DS_LEARNED`, `DS_COMBINED`).
- Backup (`make_backup`) includes the base + learned dataset text; restore writes them back and calls
  `rebuild_combined()`.

## Running it

```
# from anywhere (uses absolute paths):
powershell -ExecutionPolicy Bypass -File C:\AI\training\learn.ps1              # harvest + retrain
powershell -ExecutionPolicy Bypass -File C:\AI\training\learn.ps1 -HarvestOnly # collect data only
powershell -ExecutionPolicy Bypass -File C:\AI\training\run_all.ps1           # full pipeline only
```

Or trigger from the dashboard (Training Studio / the command‑palette "Harvest & Retrain"), which runs
the same scripts and streams progress.

## Requirements
- NVIDIA GPU with CUDA (the script installs the CUDA 12.8 PyTorch build for Blackwell/RTX 5090). Training
  a 7B model on CPU is refused by `train_lora.py`.
- `transformers`, `peft`, `trl`, `accelerate`, `datasets`, `safetensors`, `sentencepiece` (installed by
  `run_all.ps1` step 2). These are **not** in the Control Center's `requirements.txt` — they belong to
  the external pipeline's own environment.
- Ollama running (for `ollama create` + the smoke test).

## Verification status (OUT‑2)
- **Verified:** the orchestration + `[PROGRESS]` parsing (`_parse_train_sub` unit‑tested) and that
  `nova-local` exists in Ollama.
- **Not independently verified here:** that a fresh end‑to‑end run produces a *good* model (quality of
  the fine‑tune). That's the open part of OUT‑2 and is owner‑run on the external box.
```
