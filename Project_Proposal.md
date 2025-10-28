# Project Proposal

## Objective
KEPLER addresses these gaps through a real-time, multimodal pipeline that couples robust evidence retrieval with logical, multi-hop reasoning and confidence-rated verdicts for end users (journalists, researchers, platforms).

## Key points
- Real-time processing with low latency.
- Multimodal inputs (text, images, audio).
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

## Experiments
- Benchmark performance on standard datasets: FEVER (Thorne et al., 2018), HOVER (Jiang et al., 2020), A VeriTeC (Schlichtkrull et al., 2023), MOCHEG (Yao et al., 2023), VERITE (Papadopoulos et al., 2024), PUBHEALTH (Kotonya and Toni, 2020). Measure claim-level accuracy, precision, recall, F1, and explanation quality (BLEU, METEOR, ROUGE).
- Metrics: assess calibration using Brier Score and Expected Calibration Error. Measure retrieval metrics (Recall@K, MRR), explanation faithfulness (sufficiency, comprehensiveness), and system latency/throughput for real-time constraints.
- Ablations and baselines: compare against representative FEVER/HOVER systems, multimodal LLMs (LLaVA, GPT-4o), and DEFAME where applicable; ablate iterative retrieval, multimodal inputs, and calibration.
- Protocols: use held-out test splits and cross-validation where applicable; include human evaluation for explanation quality on a sampled subset; release code, data splits, seeds, and a containerized demo for reproducibility.

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



