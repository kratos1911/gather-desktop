# Model strategy — researched 26 September 2026

Status: researched shortlist, not measured winners. The original 26 September
research did not download models. See [CPU_BENCHMARK.md](CPU_BENCHMARK.md) for
the separate 10 October measurement task and its current evidence.

12 October: [fresh text challenge](TEXT_V2_RESULTS.md) passes the predeclared gate
for the 512-dimensional Qwen candidate. Carry it into bounded serving-container
measurement; no final model/dimension/fusion choice is made. The 1,024-dimensional
variant has higher MRR on v2, while 512 retrieves more labelled passage evidence.
Fixed RRF lowers MRR. Exact-code, temporal and multi-part retrieval issues remain.

27 September update: ADR-009 changes the deployment target to cloud-hosted AI.
The hardware/on-device sections below document the previous selection rationale,
not the current distribution plan. Re-evaluate candidates for cloud cost,
quality, startup time and throughput; end users will not download these weights.
Latest user choices: Google Cloud Run, self-hosted CPU inference first, Supabase
Free vectors and R2 originals. Paid deployment is not authorized by permission to
run local tests. On 10 October the user authorized D:-only model downloads and
testing, then chose Qwen first because EmbeddingGemma terms are not yet accepted.
The production runtime and winning model/dimensions remain unselected. Chat stays
deferred; SigLIP/OCR require their own visual corpus and cannot be scored using text-v1.

## Product requirement

The user clarified that the inspiration is Samsung Gallery-style natural-language retrieval across many content types: documents, slides, PDFs, Word files, photos and eventually videos. This describes the desired experience; it is not a claim about Samsung's internal architecture. Photos and scanned pages are part of the planned product, not an optional unrelated extension. Deliver native-text search first, then visual/OCR retrieval before calling the broader search objective complete.

Examples: "photo of a red car", "slide showing falling sales", "receipt for my laptop", and "document explaining database normalization". Search returns source files and specific matching pages/slides/images; chat operates on the selected source.

## Hardware observed

Development laptop: AMD Ryzen 7 4800H, 16,556,478,464 bytes reported physical RAM (about 15.4 GiB usable), NVIDIA RTX 3050 Laptop GPU reporting about 4 GiB graphics memory, plus integrated AMD graphics. WMI values are an inventory, not a measured inference memory budget. Other users' hardware may differ.

Prefer compressed 2–4B-class chat candidates, bounded context and sequential model loading. Four-bit weight storage is not total runtime memory: KV cache, vision encoder, temporary buffers and runtime add overhead. Do not promise full GPU fit or tokens/sec without testing.

## Recommended starting stack

| Role | First candidate | Alternative / comparison | Decision rationale |
| --- | --- | --- | --- |
| Text embeddings | google/embeddinggemma-300m | Qwen/Qwen3-Embedding-0.6B | Small on-device candidate; benchmark quality against Qwen |
| Photo-to-text retrieval | google/siglip2-base-patch16-224 | Larger visual encoders only if evaluation warrants them | Dedicated aligned image/text encoder for visual search |
| Document chat and optional visual questions | Qwen/Qwen3.5-4B, supported 4-bit runtime | google/gemma-4-E2B-it; NVIDIA-Nemotron-3-Nano-4B-GGUF for text-only chat | Qwen supports vision and text; compare grounding and resource usage |
| Scans and screenshot text | PaddleOCR PP-OCRv5 mobile pipeline | Language-specific OCR models as needed | Dedicated detection and recognition; do not rely solely on generated captions |

EmbeddingGemma is about 300M parameters, supports over 100 languages, has a 2K-token input limit and supports reduced embedding dimensions from 768 down to 128. Compare 256 and 768 dimensions; only choose 256 if retrieval quality remains acceptable. Use the documented query/document prompts and normalization. Its Gemma terms differ from Apache licensing and must be respected when distributing models.

Qwen3-Embedding-0.6B supports a 32K context and output dimensions from 32 to 1024. Its long context is not a reason to embed an entire document as one passage. Benchmark using its documented instruction format, not the same prompt template as EmbeddingGemma.

SigLIP 2 is explicitly intended for image-text retrieval. Use its own text tower to encode a photo search query and its vision tower to encode the image. An EmbeddingGemma query vector cannot be compared with a SigLIP image vector, even if dimensions happen to match.

Qwen3.5-4B is the first chat/vision candidate, not a proven best model for this app. Gemma 4 E2B is another current multimodal candidate; E2B means effective parameters, while its card lists 5.1B total including embeddings. Do not assume the name guarantees lower memory consumption.

NVIDIA publishes an official Nemotron 3 Nano 4B Q4_K_M GGUF model suitable for testing text chat. Keep the exact checkpoint name: the larger Nemotron 3 Nano 30B-A3B is a different model; 3B active parameters do not mean only 3B weights must be stored. The 30B-class model is not our default on this laptop.

PP-OCRv5_mobile_rec is a recognizer, not a complete OCR pipeline. Pair it with detection/preprocessing. The cited checkpoint lists Chinese, English and Japanese; do not claim it covers every language. Evaluate rotated text, small text and handwriting separately; retain confidence and bounding boxes.

## Retrieval architecture

Native PDF/Word/PowerPoint text -> parser -> text passages -> text embeddings.
Scanned pages/screenshots -> OCR -> text passages -> text embeddings.
Photos -> image embeddings; OCR text, when present, also follows the text path.
Visual pages/slides -> image embeddings or on-demand visual understanding after rendering support is validated.

Store distinct, versioned vector spaces in Supabase. Search text passages, keyword indexes and visual embeddings through separate queries with the same owner filter, then merge ranks and group by original file. Do not compare raw similarity scores across models. Preserve source locations and distinguish extracted text from generated descriptions. Captions may help retrieval but can omit or invent details, so they are not authoritative evidence.

For visual chat, pass selected source images to a supported vision runtime. Text OCR alone cannot answer questions about a chart's shape or a photograph's contents. For video later, use sampled keyframes and timestamped transcription, acknowledging events between sampled frames can be missed.

## Efficient operation and Supabase capacity

- Run image/OCR processing only when appropriate; use existing text extraction first.
- Generate/store vectors once per version. Do not run a chat model over the whole library for every search.
- Keep chat unloaded during ordinary search and avoid holding all models in GPU memory.
- Start chat with a modest tested context budget rather than advertised maximum context.
- Download optional visual/chat components on demand with version pins and checksums; no silent multi-gigabyte downloads.
- A 256-dimensional float32 vector has 1,024 bytes of numeric payload; 768 dimensions uses 3,072 bytes. Actual database usage is higher because rows, text, metadata and indexes also consume storage. Visual vectors add separate cost. Measure quota usage using representative documents.
- Record model/version/dimensions in the schema. A model change requires reindexing or parallel versioned indexes.

## Benchmark before locking defaults

27 September checkpoint: text-v1 now contains 14 fictional documents, 35
answerable text queries and 5 absent queries. Evidence is mapped through the
real processor, with integrity checks and separate exported labels. See
../tests/evaluation/README.md for commands and the planned scoring protocol.
No models have been evaluated. This small English development set does not
satisfy the later visual/OCR, realistic-scale or independently reviewed gates.

Use synthetic or user-approved fixtures: native and scanned PDFs, DOCX tables, text-heavy and visual slides, screenshots and photos. Keep video evaluation for its delivery phase.

Evaluate at least 30 text queries and 20 visual/OCR queries covering paraphrases, exact identifiers, objects/colors, late-document passages, mixed-format results and absent answers. Measure Recall@5 by category, ranking quality and search p50/p95. Do not average away poor photo performance with easy text queries.

Compare chat candidates on the same retrieved evidence: supported answers, citation correctness, refusal when evidence is missing, follow-ups, and wrong-document isolation. Measure first-token latency, output rate, peak RAM/VRAM and download size using actual pinned quantized artifacts. Test CPU fallback as well as the development GPU. Re-rankers remain optional until an end-to-end gain justifies their latency.

Keep the existing Mistral setup as a baseline where runnable. No claim that any candidate outperforms it on our task is established yet.

## Primary references

- EmbeddingGemma: https://ai.google.dev/gemma/docs/embeddinggemma
- Qwen embeddings: https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- SigLIP 2: https://huggingface.co/google/siglip2-base-patch16-224
- Qwen chat/vision: https://huggingface.co/Qwen/Qwen3.5-4B
- Gemma 4: https://ai.google.dev/gemma/docs/core/model_card_4
- Nemotron 4B: https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-4B-GGUF
- Nemotron 30B: https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Nano-Technical-Report.pdf
- OCR: https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_rec
