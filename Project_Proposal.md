# Project Proposal

## Objective
KEPLER addresses these gaps through a real-time, multimodal pipeline that couples robust evidence retrieval with logical, multi-hop reasoning and confidence-rated verdicts for end users (journalists, researchers, platforms).

## Key points
- Real-time processing with low latency.
- Multimodal inputs (text, images) -> only text and image.
- Robust evidence retrieval and relevance ranking.
- Explainable, multi-step reasoning (traceable steps).
- Confidence scores and short explanations for each verdict.

## Related work
Early pipelines (e.g., FEVER (Thorne et al., 2018)) emphasize text-only verification; multi-hop datasets (e.g., HOVER (Jiang et al., 2020), EX-FEVER) advance reasoning with explainable 2-hop and 3-hop chains (Ma et al., 2024), yet most systems remain limited to fixed text corpora. Recent multimodal LLMs (e.g., GPT-4o, LLaVA) enable image+text comprehension, and DEFAME (Braun et al., 2025) demonstrates dynamic evidence-based processing for multimodal claims. However, these approaches lack systematic integration into end-to-end fact-checking with real-time retrieval, calibrated uncertainty quantification, and structured justifications. KEPLER contributes a cross-modal, model-agnostic backbone with iterative retrieval, explicit confidence estimation, and transparent reasoning chains.

## Deliverables
- Working prototype of the pipeline.
- Evaluation results on representative tasks and datasets.
- Documentation and a reproducible demo.
 
## Proposed work
Pipeline (from PDF):
- (1) Input Handler & Claim Detection Agent — Accepts both text and image inputs. Utilizes user-selected multimodal LLMs, allowing the use of one or multiple models (e.g., GPT-4o, Gemini, Claude) to parse and identify distinct, verifiable factual claims for further verification.
- (2) Retriever Agent — Designs tailored evidence search strategies based on claim modality. Calls APIs (Google Search, GeoClip, Vision) to collect fresh, relevant content from unbiased sources.
- (3) Reranker Agent — Filters and prioritizes retrieved evidence. Orders are sourced by relevance, credibility, and recency to ensure only the strongest and most pertinent facts move forward.
- (4) Aggregator Agent — Synthesizes multimodal evidence by integrating text, images, and metadata. It applies chain-of-thought reasoning and highlights agreements, conflicts, and missing information.
- (5) Verifier Agent — Evaluates the aggregated evidence for each claim. Assigns verdicts (Supported, Refuted, Misleading, Not Enough Information), with iterative evidence expansion for uncertain cases.
- (6) Weighted Multi-Model Output — When multiple LLMs are selected, their individual verdicts, explanations, and confidence scores are aggregated using a dynamic weighting system.
- (7) Confidence Scorer — Rates verdict certainty by considering source reliability, cross-model agreement, and evidence recency. Presents confidence scores and structured, source-linked justifications.

#### Multi-model fusion strategy (practical month‑1)
- Do we run separate pipelines per model? No. To control cost and keep evidence consistent, we share the same retrieval → rerank → aggregate outputs across models, and only run multiple verifiers on the same evidence bundle.
- Per-model verifier output (for the same claim and evidence set):
	- Label probabilities over {Supported, Refuted, NEI} (after per-model calibration on a dev split).
	- Chosen evidence subset from the candidate pool (by sentence ids/URLs) and a short justification.
- Weighted fusion (simple, effective):
	- Learn weights w_i on the dev set (logistic regression or grid search). If no time, use heuristic weights (e.g., premium 0.6, mini 0.4).
	- p_final = normalize(Σ_i w_i · p_i). Pick argmax as the final label.
	- Agreement boost: if two or more models agree on the label AND their evidence overlaps (Jaccard ≥ 0.5 over sentence ids), add a small boost to that class before normalization.
	- Inconsistency penalty: downweight a model if its justification cites evidence not in the provided set (hallucination proxy).
- Escalation rules
	- If max(p_final) < τ_low (e.g., 0.6) or models disagree sharply, trigger the iterative loop: expand retrieval and re-verify.
	- If still low confidence, route a final pass to a premium model only (cost control), then refuse/flag as NEI when evidence remains insufficient.
- Why not per-model retrieval? Shared retrieval ensures fair comparison, reduces cost/latency, and improves evidence agreement signals. A model may propose missing evidence; if that happens, we add it to the retrieval patch list and re-run once.

## System architecture (Mermaid)

```mermaid
flowchart LR
	%% Layout
	classDef step fill:#eef7ff,stroke:#3894ff,stroke-width:1px;
	classDef io fill:#fff7e6,stroke:#ff9900,stroke-width:1px;
	classDef store fill:#f3f4f6,stroke:#94a3b8,stroke-width:1px;
	classDef eval fill:#ecfdf5,stroke:#10b981,stroke-width:1px;

	subgraph Inputs
		T[Text input]:::io
		I[Image input]:::io
	end

	subgraph LLMs[Selectable multimodal LLMs]
		M1[GPT-4o / Claude / Gemini]:::store
		M2[Llama 3.2-V / Qwen2-VL]:::store
	end

	T --> CD[1) Claim Detection]:::step
	I --> CD
	CD -->|claims| RET[2) Retriever]:::step

	subgraph External APIs
		S[Web Search API\n(Google CSE, etc.)]:::store
		V[Vision / Reverse Image\n(GeoCLIP, Vision API, OCR)]:::store
	end

	RET -->|queries| S
	RET -->|image queries| V
	S --> RET
	V --> RET

	RET --> RR[3) Reranker]:::step
	RR --> AGG[4) Aggregator]:::step
	AGG --> VER[5) Verifier]:::step

	%% Optional multi-model fusion
	VER --> FUS[6) Weighted Multi-Model Output]:::step
	FUS --> CAL[7) Confidence Scorer]:::step

	CAL --> OUT[Verdict + Evidence + Confidence + Justification]:::io

	%% Iterative loop for NEI/low confidence
	CAL -. low confidence / NEI .-> RET

	%% Evaluation & datasets
	subgraph Benchmarks
		D1[FEVER/HOVER/EX-FEVER\n(text)]:::store
		D2[VERITE/MOCHEG\n(multimodal subset)]:::store
	end

	D1 -->|claims| CD
	D2 -->|claims| CD
	OUT --> METRICS[(Metrics:\nMacro-F1, FEVER Score,\nRecall@K/MRR, Latency, Calibration)]:::eval
```

### Handling text + image inputs (claiming policy)
- Claim unit: one verifiable statement (subject–predicate–object with optional qualifiers like time/location).
- Modalities:
	- Text-only claim: stated entirely in text. Image may be ignored or used as optional context.
	- Image-only claim: inferred from image content and/or OCR (e.g., location, entity, event, embedded caption).
	- Multimodal claim: text asserts something about the image (e.g., “This photo shows X in Y, 2022”). Requires joint grounding.
- When to combine vs separate
	- Combine (multimodal): text references the image (deictic “this”, “pictured above”, or explicit claims about what the image depicts) or the image is necessary to resolve the claim.
	- Separate: text makes a factual statement independent of the image; image content is unrelated or purely decorative.
	- Additional image claim: if the image itself implies a factual statement (via content or OCR’d text), add it as a distinct image-only claim.
- Retrieval plan per mode
	- Text-only: web/Wikipedia search (BM25 + dense), normalizer for page titles; return sentence-level evidence.
	- Image-only: reverse image/visual search (CLIP/GeoCLIP/vision API), near-duplicate detection, and source/backstory URLs; optional OCR to query text.
	- Multimodal: run both text and image retrieval; aggregate cross-modal evidence and resolve conflicts.
- Evidence format (for outputs)
	- Text evidence: (page_title, sentence_index) with snippet and URL (when available).
	- Image evidence: source URL or hash match; optional bounding box/region notes and OCR snippet used.
	- Verdict per claim: {Supported, Refuted, NEI} (Misleading optionally tracked for analysis), plus confidence and brief justification.
- Benchmark-specific notes
	- FEVER: treat as text-only; output predicted label + Wikipedia sentence evidence to compute FEVER Score.
	- Multimodal subset (e.g., VERITE/MOCHEG): require at least one modality to ground the claim; report label, evidence pointers, and latency.

### Step 1: Input Handler & Claim Detection — details
- Accepted inputs
	- text: free-form text (post, caption, paragraph). We keep character offsets to tag spans for each extracted claim.
	-  image: URL or base64. Optional OCR (Azure Vision/Google Vision) used to extract embedded text that can seed or refine claims.
	- metadata (optional): timestamp, location hint, language code.

- User-selectable model options (examples)
	- OpenAI GPT-4o / GPT-4o mini (or Azure OpenAI): strong multimodal grounding; reliable JSON output.
	- Anthropic Claude 3.5 Sonnet / Haiku: careful reasoning, large context; Haiku for lower latency/cost.
	- Google Gemini 1.5 Pro / Flash: very long context, good vision; schema-enforced outputs.
	- Cost-optimized: Llama 3.2 Vision, Qwen2-VL via hosted providers (Fireworks/Together/etc.).
	- Selection policy: default to a “mini/flash/haiku” tier; route ambiguous/hard cases to a premium model (configurable percentage).

- Output contract (JSON)
	- claims: array of objects with fields:
		- id: string — unique within the request (e.g., c1, c2 …).
		- text: string — the verifiable claim as a single sentence.
		- modality: "text" | "image" | "multimodal" — per claiming policy above.
		- qualifiers: { time?: string, place?: string, entities?: string[] } — optional.
		- spans?: [start, end] — character offsets into input text (if applicable).
		- image_regions?: [{ x, y, w, h }] — 0–1 normalized boxes referencing visual evidence (if applicable).
		- confidence: number in [0,1] — model’s self-reported confidence.
	- notes: we enforce JSON-only responses and validate against this schema; invalid outputs are retried with a repair prompt.

- Quality controls & routing
	- Deduplication: merge near-duplicate claims (text-similarity threshold); keep the highest-confidence version.
	- Budget-aware routing: if confidence < τ or modality == multimodal with ambiguous grounding, send to premium model for a second opinion.
	- Throughput: batch multiple items per request when provider allows; cache OCR and reuse across retries.

- Special cases
	- FEVER runs: skip Step 1 (claims are provided by the dataset); we start at retrieval.
	- Image-only posts with sparse content: run OCR first; if no claims emerge, return empty claims list with a reason tag (e.g., "no verifiable claim").

#### Claim consistency across multiple models (how we keep it reliable)
- Clear claim definition (rubric)
	- A claim is a verifiable factual assertion about entities, events, quantities, or relations, optionally qualified by time/place.
	- Exclude opinions, questions, commands, predictions without evidence, and vague descriptions (e.g., "beautiful", "looks like").
	- Atomicity: split into minimal, self-contained statements; include qualifiers that affect truth (time, location, counts).

- Prompt/spec guardrails
	- System prompt states the rubric and shows 3–5 positive/negative examples for text-only, image-only, and multimodal references (e.g., "this photo shows …").
	- Require JSON-only output conforming to our schema; set temperature=0 and enable schema/JSON mode when available.
	- Canonicalize deictic claims ("this", "pictured above") to explicit references (e.g., "The image shows X at Y in 2022").

- Validation & normalization
	- JSON schema validation; on failure, auto-repair with a short retry prompt.
	- Normalize claim text: lowercase, trim, collapse whitespace, lemmatize (optional), remove non-informative adjectives.
	- Deduplicate with semantic similarity (e.g., cosine on sentence embeddings); threshold ≈ 0.85.

- Cross-model consensus (simple month‑1 policy)
	- Route most items to a mini/flash/haiku model. If (a) confidence < τ_low (≈0.4) or (b) zero claims but heuristic classifier says claim-likely, escalate to a premium model.
	- Merge candidates from main and premium; dedup; assign final confidence as max or a weighted average by model reliability.
	- Accept a claim if confidence ≥ τ_accept (≈0.7); otherwise drop it.

- Quick evaluation checks (small dev set of ~200 examples)
	- Precision/recall/F1 of claim detection against a tiny hand-labeled set (focus on precision to avoid noisy downstream work).
	- Inter-model agreement: Jaccard overlap of normalized claim sets; track claim-count variance per input.
	- Error review loop: update examples in the prompt/rubric where models disagree or over/under-extract.

- Pseudocode sketch
	- detect_claims(text, image):
		1) C_main ← run(main_model, text, image, schema)
		2) if low_conf(C_main) or empty(C_main): C_prem ← run(premium_model, …) else C_prem ← ∅
		3) C ← dedup(normalize(C_main ∪ C_prem))
		4) return {c ∈ C | conf(c) ≥ τ_accept}

## Experiments
- Benchmark performance on standard datasets: FEVER (Thorne et al., 2018), HOVER (Jiang et al., 2020), A VeriTeC (Schlichtkrull et al., 2023), MOCHEG (Yao et al., 2023), VERITE (Papadopoulos et al., 2024), PUBHEALTH (Kotonya and Toni, 2020). Measure claim-level accuracy, precision, recall, F1, and explanation quality (BLEU, METEOR, ROUGE).
- Metrics: assess calibration using Brier Score and Expected Calibration Error. Measure retrieval metrics (Recall@K, MRR), explanation faithfulness (sufficiency, comprehensiveness), and system latency/throughput for real-time constraints.
- Ablations and baselines: compare against representative FEVER/HOVER systems, multimodal LLMs (LLaVA, GPT-4o), and DEFAME where applicable; ablate iterative retrieval, multimodal inputs, and calibration.
- Protocols: use held-out test splits and cross-validation where applicable; include human evaluation for explanation quality on a sampled subset; release code, data splits, seeds, and a containerized demo for reproducibility.

- Experiment setup (expanded):
	- Input modes: evaluate text-only, image-only, and multimodal (text+image) to isolate modality contributions.
	- Retrieval: compare sparse (BM25) vs dense (e.g., Contriever/ColBERT) and hybrid; report top-k values (k∈{10, 20, 50}) and caching policy.
	- Reranking: test cross-encoder vs lightweight bi-encoder rerankers; vary list size and observe Recall@K/MRR sensitivity.
	- Aggregation/verification: fixed prompt templates vs chain-of-thought; enable iterative retrieve→reason→re-retrieve loop for NEI/low-confidence cases.
	- Calibration: temperature scaling vs isotonic regression on a dev split; measure Brier/ECE before vs after calibration.
	- FEVER-style scoring: for FEVER/HOVER/EX-FEVER, also report FEVER Score (label + sufficient evidence) alongside F1.
	- Latency conditions: end-to-end latency measured at P50/P90 with cold- and warm-cache; batch size and concurrency fixed; note hardware (CPU/GPU) and network constraints.

- Baselines to compare against:
	- Classic text verification: representative FEVER/HOVER baselines (e.g., pipeline BM25+ESIM/DeBERTa, DR+verifier).
	- Multimodal LLMs: LLaVA and GPT-4o prompted directly for verdicts/explanations without external retrieval.
	- Multimodal pipeline: DEFAME (where dataset overlap permits) as an external retrieval+reasoning baseline.
	- Simple/ablated variants: retrieval-only majority/heuristics, BM25+linear/SVM, no-reranker, no-iteration, text-only or image-only KEPLER, and KEPLER without calibration.
	- Oracle upper-bound: verifier given gold evidence (when provided) to bound reasoning performance separate from retrieval.

- Metric rationale and selection:
	- Accuracy vs class imbalance: many datasets include a large NEI class; plain accuracy can mask poor minority-class performance. Precision, recall, and F1 (macro) expose false positives/negatives per class.
	- Macro vs micro: macro-averaged F1 treats classes equally (important when NEI dominates); micro can be inflated by majority classes—report both but optimize for macro.
	- FEVER Score: integrates label correctness with evidence sufficiency; directly aligns with fact-checking goals on FEVER-family datasets.
	- Explanation quality: BLEU/METEOR/ROUGE capture surface overlap; we complement them with faithfulness checks (sufficiency/comprehensiveness) and small-scale human judgment.
	- Calibration (Brier/ECE): KEPLER returns confidence scores; well-calibrated probabilities are critical for thresholding, escalation, and risk-coverage curves.
	- Retrieval (Recall@K/MRR): the verifier cannot succeed without evidence; these quantify the ceiling imposed by retrieval.
	- Ops metrics: latency/throughput reflect the "real-time" constraint and guide engineering trade-offs.

- Reporting & significance:
	- Label mapping: normalize dataset-specific labels to {Supported, Refuted, NEI}; track Misleading analysis separately when applicable.
	- Averaging & intervals: report macro-averages with 95% CIs via bootstrap; for paired comparisons use McNemar (classification) and paired bootstrap (text metrics).
	- Pre-registered primaries: FEVER Score (FEVER-family) and macro-F1 (others) as primary; secondary metrics include calibration (ECE/Brier), retrieval (Recall@K/MRR), and latency.
	- Reproducibility: fixed seeds, published prompts/configs, and containerized runner with scripts for exact reproduction.

## References
- Thorne, J., Vlachos, A., Christodoulopoulos, C., & Mittal, A. (2018). FEVER: a large-scale dataset for fact extraction and verification.
- Jiang, Z., et al. (2020). HOVER: [multi-hop verification dataset].
- Ma, X., et al. (2024). EX-FEVER: explainable multi-hop verification (2- and 3-hop chains).
- OpenAI. (2024/2025). GPT-4o — multimodal LLMs.
- LLaVA authors. (2023). LLaVA: Large Language and Vision Assistant.
- Braun, A., et al. (2025). DEFAME: dynamic evidence-based processing for multimodal claims.

## References (from PDF)
- Tobias Braun, Mark Rothermel, Marcus Rohrbach, and Anna Rohrbach. 2025. Defame: Dynamic evidence-based fact-checking with multimodal experts. In Proceedings of the 42nd International Conference on Machine Learning, volume 267, Vancouver, Canada. PMLR.
- Yichen Jiang, Shikha Bordia, Zheng Zhong, Charles Dognin, Maneesh Singh, and Mohit Bansal. 2020. HoVer: A dataset for many-hop fact extraction and claim verification. In Findings of the Conference on Empirical Methods in Natural Language Processing (EMNLP).
- Neema Kotonya and Francesca Toni. 2020. Explainable automated fact-checking for public health claims. arXiv preprint arXiv:2010.09926.
- Huanhuan Ma, Weizhi Xu, Yifan Wei, Liuji Chen, Liang Wang, Qiang Liu, Shu Wu, and Liang Wang. 2024. EX-FEVER: A dataset for multi-hop explainable fact verification. In Findings of the Association for Computational Linguistics: ACL 2024, pages 9340–9353, Bangkok, Thailand. Association for Computational Linguistics.
- Stefanos-Iordanis Papadopoulos, Christos Koutlis, Symeon Papadopoulos, and Panagiotis C Petrantonakis. 2024. Verite: a robust benchmark for multi-modal misinformation detection accounting for unimodal bias. International Journal of Multimedia Information Retrieval, 13(1):4.
- Michael Sejr Schlichtkrull, Zhijiang Guo, and Andreas Vlachos. 2023. Averitec: A dataset for real-world claim verification with evidence from the web. In Thirty-seventh Conference on Neural Information Processing Systems Datasets and Benchmarks Track.
- James Thorne, Andreas Vlachos, Christos Christodoulopoulos, and Arpit Mittal. 2018. FEVER: a large-scale dataset for fact extraction and VERification. In NAACL-HLT.
- Barry Menglong Yao, Aditya Shah, Lichao Sun, Jin-Hee Cho, and Lifu Huang. 2023. End-to-end multimodal fact-checking and explanation generation: A challenging dataset and models. In Proceedings of the 46th International ACM SIGIR Conference on Research and Development in Information Retrieval, SIGIR ’23, page 2733–2743, New York, NY, USA. Association for Computing Machinery.

## At-a-glance summary

- What was available (state of the art)
	- Text/multi-hop verification datasets and systems: FEVER, HOVER, EX-FEVER.
	- Multimodal understanding: GPT-4o, LLaVA.
	- Multimodal fact-checking exemplar: DEFAME.
	- Gaps: reliance on fixed corpora; limited end-to-end integration of retrieval → reasoning → verdicts; weak calibration and structured justifications.

- What we propose to do
	- Build an end-to-end, real-time, multimodal fact-checking pipeline with iterative retrieval, explicit multi-hop reasoning, calibrated confidence, and transparent, source-linked justifications.

- How we will do it
	- Orchestrate seven agents: Claim Detection → Retriever → Reranker → Aggregator → Verifier → Multi-Model Fusion → Confidence Scorer.
	- Use hybrid retrieval (sparse + dense), dynamic weighting across multiple LLMs, and track provenance for explainability.
	- Validate on FEVER/HOVER/AVeriTeC/MOCHEG/VERITE/PUBHEALTH with accuracy/F1, retrieval (Recall@K/MRR), explanation metrics (BLEU/METEOR/ROUGE), and calibration (Brier/ECE), under latency constraints.

	## Structured analysis

	### Objective — what and why
	- Problem to solve
		- Misinformation spreads across text and images; manual fact-checking cannot scale.
		- Many automated systems rely on fixed corpora, single modality, or lack transparent justifications.
	- Proposed outcome (what)
		- A real-time, multimodal pipeline that retrieves evidence, performs multi-hop reasoning, and outputs confidence-rated, justified verdicts for end users.
	- Success criteria (how we’ll recognize success)
		- Low-latency responses, high verification accuracy, calibrated confidence, and traceable reasoning chains with linked evidence.

	### Related work — what’s available and gaps
	- Available
		- Text-only verification: FEVER (2018).
		- Multi-hop reasoning: HOVER (2020), EX-FEVER (2024) with explainable 2–3 hop chains.
		- Multimodal understanding: GPT-4o, LLaVA.
		- Multimodal fact-checking exemplar: DEFAME (2025).
	- Gaps
		- Fixed text corpora rather than live, real-time retrieval.
		- Missing end-to-end integration of retrieval → reasoning → verdicts with calibrated uncertainty.
		- Limited structured justifications and explicit reasoning chains.

	### Proposed work — what we’ll build
	- Cross-modal, model-agnostic backbone for text and images (optionally audio).
	- Iterative retrieval (retrieve → reason → re-retrieve) guided by claim needs.
	- Multi-hop, chain-of-thought style reasoning with provenance tracking.
	- Calibrated confidence per evidence and per verdict; structured, source-linked justifications.
	- Modular components to swap LLMs/encoders and retrieval strategies.

	### How we’ll do it — architecture and method
	- Pipeline agents (aligned with the PDF)
		1. Input Handler & Claim Detection — extract verifiable claims from text/images using selected multimodal LLMs (e.g., GPT-4o, Gemini, Claude).
		2. Retriever — plan searches by modality; call APIs (Google Search, GeoCLIP/Vision) for fresh, credible evidence.
		3. Reranker — prioritize by relevance, credibility, and recency.
		4. Aggregator — fuse multimodal evidence; highlight support/contradictions/gaps with chain-of-thought.
		5. Verifier — assign verdicts (Supported, Refuted, Misleading, NEI) and expand evidence when uncertain.
		6. Weighted Multi-Model Output — aggregate multiple LLMs’ verdicts/explanations/confidences with dynamic weighting.
		7. Confidence Scorer — calibrate using source reliability, cross-model agreement, and recency; return scores with linked justifications.
	- System design choices
		- Hybrid retrieval (sparse + dense) for recall/latency balance; caching and batching for serving.
		- Strict evidence provenance and stepwise reasoning traces for explainability/auditing.
		- Modular LLM layer for easy model swaps without rewiring the pipeline.

	### Experiments — datasets, metrics, baselines, protocols
	- Datasets: FEVER (2018), HOVER (2020), AVeriTeC (2023), MOCHEG (2023), VERITE (2024), PUBHEALTH (2020).
	- Metrics
		- Claim-level: accuracy, precision, recall, F1.
		- Explanations: BLEU, METEOR, ROUGE; faithfulness (sufficiency, comprehensiveness).
		- Retrieval: Recall@K, MRR.
		- Calibration: Brier Score, ECE (+ reliability diagrams).
		- Ops: end-to-end latency and throughput.
	- Baselines & ablations
		- Baselines: FEVER/HOVER systems; multimodal LLMs (LLaVA, GPT-4o); DEFAME where applicable.
		- Ablations: remove iterative retrieval; drop multimodal inputs; disable calibration; vary rerankers.
	- Protocols & reproducibility
		- Standard splits; cross-validation as needed; human eval for explanations on a sampled subset.
		- Release code, seeds, containers, and data splits.

	### Plan and milestones
	- Weeks 1–2: Literature review; datasets/splits; claim extractor.
	- Weeks 3–6: Evidence planner; retrieval API integration (text/image/geo).
	- Weeks 7–10: Summarization; contrastive reasoning; uncertainty.
	- Weeks 11–13: Verdicts; NEI loop; justifications & UI.
	- Week 14: Benchmarks vs baselines; human study; write-up.

	### Deliverables
	- Working prototype of the end-to-end pipeline.
	- Benchmarks vs baselines; ablations; calibration analyses.
	- Documentation and a reproducible, demo-ready container.

	Note: For a concise recap, see the “At-a-glance summary” section just above.



