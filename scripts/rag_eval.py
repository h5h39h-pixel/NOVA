# -*- coding: utf-8 -*-
"""OUT-5 — RAG retrieval quality. Seed an isolated KB with distinct documents, run queries whose
answer lives in exactly one document, and measure retrieval quality (precision@1 + MRR). Writes a
dated baseline to docs/rag-baseline.md.

Outcome verification, not a unit test (needs Ollama + nomic-embed-text). Uses a temp DB so the real
control.db is untouched.

Usage:  python scripts/rag_eval.py [--write-doc]
"""
import argparse
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import nova.core.db as dbm  # noqa: E402

# A larger, deliberately OVERLAPPING corpus (many docs mention the same entities — GPU, ports, models,
# the control center — so retrieval must distinguish them, not just keyword-match). Harder than the toy set.
DOCS = {
    "gpu.txt": "The workstation has an NVIDIA RTX 5090 with 32 GB of VRAM dedicated to local AI inference and model training.",
    "backup.txt": "Database snapshots are taken automatically every day and the most recent 14 are kept in the backups folder; generated media is mirrored too.",
    "auth.txt": "Login tokens are hashed with SHA-256 and the cloud API key is encrypted at rest using Fernet; localhost is trusted.",
    "training.txt": "LoRA fine-tuning on the RTX 5090 harvests the user's chat logs and produces a personalized model named nova-local.",
    "ports.txt": "The control center dashboard listens on port 8900 while Open WebUI runs on port 3000 and Ollama on 11434.",
    "stt.txt": "Speech-to-text uses faster-whisper on the GPU; the default model is 'small' and Arabic is supported.",
    "tts.txt": "Text-to-speech uses Piper with an Arabic voice (kareem) and an English voice (lessac); speed is adjustable.",
    "vision.txt": "AI Screen Vision streams the screen as throttled JPEG frames and describes it with qwen2.5-VL; everything is opt-in.",
    "control.txt": "Precise control moves the mouse to exact coordinates and types text; a panic stop pauses all control instantly.",
    "rag.txt": "The knowledge base embeds documents with nomic-embed-text into SQLite and retrieves by cosine similarity.",
    "agent.txt": "The autonomous agent plans step by step, uses tools, and can be stopped at any time; web results are treated as untrusted data.",
    "comfy.txt": "Image and video generation run locally through ComfyUI using SDXL, Flux, and LTX-Video models.",
}
# query -> the single document that BEST answers it (paraphrased, minimal lexical overlap)
QUERIES = [
    ("How much video memory does the graphics card have?", "gpu.txt"),
    ("How many days of database backups are kept?", "backup.txt"),
    ("How are passwords and secrets protected?", "auth.txt"),
    ("What is the name of the personalized fine-tuned model?", "training.txt"),
    ("Which network port serves the main dashboard?", "ports.txt"),
    ("What does the system use to transcribe speech?", "stt.txt"),
    ("How is text read aloud, and can the speed change?", "tts.txt"),
    ("How does the AI watch my screen in real time?", "vision.txt"),
    ("How do I immediately stop the AI from controlling the mouse?", "control.txt"),
    ("How are documents searched semantically?", "rag.txt"),
    ("How does the assistant handle untrusted information from the internet?", "agent.txt"),
    ("What runs picture and movie generation?", "comfy.txt"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-doc", action="store_true")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="nova-rag-"))
    dbm.DB_PATH = tmp / "rag.db"
    dbm.init_db()

    from nova.services.kb import kb_ingest_file, kb_search, kb_status
    st = kb_status()
    if not st.get("available"):
        print("ERROR: embedding model not available (is Ollama running with nomic-embed-text?)")
        return 1

    for name, text in DOCS.items():
        (tmp / name).write_text(text, encoding="utf-8")
        n = kb_ingest_file(tmp / name)
        print(f"ingested {name}: {n} chunk(s)")
    print()

    hits1 = 0
    rr_sum = 0.0
    rows = []
    for q, expected in QUERIES:
        res = kb_search(q, k=4)
        ranked = [r["doc"] for r in res]
        top = ranked[0] if ranked else "(none)"
        rank = (ranked.index(expected) + 1) if expected in ranked else 0
        rr = (1.0 / rank) if rank else 0.0
        ok = (top == expected)
        hits1 += 1 if ok else 0
        rr_sum += rr
        topscore = res[0]["score"] if res else 0.0
        rows.append((q, expected, top, ok, rank, round(topscore, 3)))
        print(f"[{'P@1' if ok else 'miss'}] {q}\n        -> top={top} (score {topscore:.3f}), expected={expected}, rank={rank or '-'}")

    n = len(QUERIES)
    p1 = round(100 * hits1 / n)
    mrr = round(rr_sum / n, 3)
    print(f"\n=== RAG BASELINE: precision@1 = {hits1}/{n} ({p1}%), MRR = {mrr} ===")

    if args.write_doc:
        ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
        lines = [
            "# RAG retrieval quality baseline (OUT-5)", "",
            f"_Generated by `scripts/rag_eval.py` on {ts} — embed model **{st.get('embed_model')}**._", "",
            "Seeds an isolated KB with single-topic documents and checks that each query retrieves the "
            "one document that answers it. Outcome verification, not a unit test.", "",
            f"**precision@1 = {hits1}/{n} ({p1}%) · MRR = {mrr}**", "",
            "| Query | Expected | Top hit | Hit? | Rank | Top score |",
            "|---|---|---|---|---|---|",
        ]
        for q, exp, top, ok, rank, sc in rows:
            lines.append(f"| {q} | {exp} | {top} | {'✅' if ok else '❌'} | {rank or '-'} | {sc} |")
        lines += ["", "Re-run: `python scripts/rag_eval.py --write-doc`.", ""]
        (ROOT / "docs" / "rag-baseline.md").write_text("\n".join(lines), encoding="utf-8")
        print("wrote docs/rag-baseline.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
