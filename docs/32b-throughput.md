# 32B model throughput — tracking note (T-034)

**Status: Monitoring (upstream-gated — no code changes needed).**

## Baseline (measured on this machine)
- Hardware: RTX 5090 (32 GB VRAM, Blackwell), Ultra 9 285K, 95 GB RAM.
- `qwen2.5:14b` → **~120 tok/s** → **the default** (fast, fits comfortably, agent-JSON-safe).
- `qwen2.5:32b` → **~5 tok/s when the GPU is shared** (ComfyUI online + other models resident),
  ~11 tok/s isolated. 24 GB of weights leaves little headroom on 32 GB.

## Why 32B underperforms here
- VRAM contention when other models/ComfyUI are resident.
- Likely a not-yet-Blackwell-optimal llama.cpp build under the current Ollama.

## What to watch (re-benchmark when any of these ship)
- **Ollama** updates that bump the bundled **llama.cpp** (Blackwell/CUDA 12.x kernels, flash-attn).
- New **quantizations** of 32B (e.g., improved Q4_K_M / IQ4_XS) that cut VRAM + raise tok/s.
- NVIDIA driver / CUDA updates affecting Blackwell throughput.

## How to re-benchmark (when an update lands)
1. Close ComfyUI and unload other models so 32B has the whole GPU:
   `ollama stop <other-models>` (or restart Ollama).
2. `ollama pull qwen2.5:32b` (refresh) and run a fixed prompt with `num_predict=512`.
3. Record tok/s here. If isolated 32B reaches **≳25–30 tok/s**, consider promoting it to the
   "max-intelligence" default for non-agent chat; keep 14B for agent/tool JSON.

## Decision
No action now. This is gated by upstream (Ollama/llama.cpp/NVIDIA). Revisit on the next major
Ollama release; update this note + `ROADMAP.md` with new numbers when measured.

_Last reviewed: 2026-06-30._
