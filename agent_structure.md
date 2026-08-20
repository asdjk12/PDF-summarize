PDF Knowledge Agent — System Structure

pdf-knowledge-agent/
│
├─ apps/
│  ├─ web/
│  │  ├─ frontend/
│  │  │  ├─ pages/
│  │  │  ├─ components/
│  │  │  ├─ document-library/
│  │  │  ├─ summary-view/
│  │  │  ├─ chat/
│  │  │  ├─ citation-viewer/
│  │  │  ├─ artifact-viewer/
│  │  │  └─ source-selector/
│  │  │
│  │  └─ backend/
│  │     ├─ auth/
│  │     ├─ upload/
│  │     ├─ processing-status/
│  │     ├─ documents/
│  │     ├─ summaries/
│  │     ├─ queries/
│  │     ├─ citations/
│  │     └─ artifacts/
│  │
│  ├─ local/
│  │  ├─ ui/
│  │  ├─ folder-authorization/
│  │  ├─ folder-watcher/
│  │  ├─ local-api/
│  │  └─ local-runtime/
│  │
│  └─ cli/
│
├─ harness/
│  ├─ profile/
│  ├─ bundle/
│  ├─ session/
│  ├─ prompts/
│  ├─ sandbox/
│  └─ knowledge-plugin/
│     ├─ tools/
│     │  ├─ list_sources/
│     │  ├─ inspect_source/
│     │  ├─ summarize_sources/
│     │  ├─ search_evidence/
│     │  ├─ compare_sources/
│     │  └─ get_artifact/
│     │
│     ├─ schemas/
│     ├─ guards/
│     ├─ transport/
│     ├─ errors/
│     └─ results/
│
├─ domain/
│  ├─ knowledge/
│  │  ├─ models/
│  │  │  ├─ knowledge_source/
│  │  │  ├─ document/
│  │  │  ├─ page/
│  │  │  ├─ source_locator/
│  │  │  ├─ evidence/
│  │  │  ├─ artifact/
│  │  │  └─ processing_state/
│  │  │
│  │  ├─ repository/
│  │  ├─ source_scope/
│  │  ├─ permissions/
│  │  ├─ versioning/
│  │  └─ lifecycle/
│  │
│  ├─ ingestion/
│  │  ├─ pipeline/
│  │  ├─ validation/
│  │  ├─ identity/
│  │  ├─ rendering/
│  │  │  ├─ pdf/
│  │  │  ├─ web/
│  │  │  └─ image/
│  │  │
│  │  ├─ parsing/
│  │  │  ├─ native-text/
│  │  │  ├─ structure/
│  │  │  └─ metadata/
│  │  │
│  │  ├─ ocr/
│  │  ├─ normalization/
│  │  └─ processing-state/
│  │
│  ├─ visual-retrieval/
│  │  ├─ adapters/
│  │  │  └─ pixelrag/
│  │  │
│  │  ├─ embeddings/
│  │  │  ├─ page-embedding/
│  │  │  └─ query-embedding/
│  │  │
│  │  ├─ index/
│  │  │  ├─ faiss/
│  │  │  └─ qdrant/
│  │  │
│  │  ├─ search/
│  │  ├─ filtering/
│  │  └─ metadata/
│  │
│  ├─ text-retrieval/
│  │  ├─ keyword/
│  │  ├─ embeddings/
│  │  ├─ index/
│  │  └─ search/
│  │
│  ├─ retrieval/
│  │  ├─ query-preparation/
│  │  ├─ visual/
│  │  ├─ text/
│  │  ├─ fusion/
│  │  ├─ rerank/
│  │  ├─ evidence-builder/
│  │  └─ diagnostics/
│  │
│  ├─ summary/
│  │  ├─ page-reader/
│  │  ├─ page-grouping/
│  │  ├─ local-summary/
│  │  ├─ section-summary/
│  │  ├─ document-summary/
│  │  ├─ multi-document-summary/
│  │  ├─ hierarchical-merge/
│  │  ├─ citation-mapping/
│  │  ├─ validation/
│  │  └─ artifacts/
│  │
│  ├─ grounded-answer/
│  │  ├─ evidence-sufficiency/
│  │  ├─ reader/
│  │  ├─ answer-generation/
│  │  ├─ citation-mapping/
│  │  └─ validation/
│  │
│  ├─ comparison/
│  │  ├─ evidence-grouping/
│  │  ├─ document-extraction/
│  │  ├─ cross-document-analysis/
│  │  └─ artifact/
│  │
│  └─ memory/
│     ├─ session-projection/
│     └─ long-term/
│
├─ infrastructure/
│  ├─ storage/
│  │  ├─ original-files/
│  │  ├─ rendered-pages/
│  │  ├─ metadata-db/
│  │  ├─ artifact-store/
│  │  └─ user-memory-store/
│  │
│  ├─ vector-store/
│  │  ├─ faiss/
│  │  └─ qdrant/
│  │
│  ├─ model-adapters/
│  │  ├─ agent-model/
│  │  ├─ visual-embedding-model/
│  │  ├─ reader-model/
│  │  ├─ text-embedding-model/
│  │  └─ reranker/
│  │
│  ├─ workers/
│  │  ├─ render-worker/
│  │  ├─ parse-worker/
│  │  ├─ ocr-worker/
│  │  ├─ embedding-worker/
│  │  ├─ index-worker/
│  │  └─ summary-worker/
│  │
│  ├─ queue/
│  ├─ cache/
│  ├─ observability/
│  │  ├─ logs/
│  │  ├─ metrics/
│  │  └─ tracing/
│  │
│  └─ security/
│     ├─ sandbox/
│     ├─ worker-isolation/
│     ├─ resource-limits/
│     └─ credential-boundary/
│
├─ pipelines/
│  ├─ pdf-ingestion/
│  │  ├─ validate/
│  │  ├─ identify/
│  │  ├─ render/
│  │  ├─ optional-parse/
│  │  ├─ optional-ocr/
│  │  ├─ embed/
│  │  ├─ index/
│  │  └─ ready/
│  │
│  ├─ static-summary/
│  │  ├─ traverse-pages/
│  │  ├─ group-pages/
│  │  ├─ read/
│  │  ├─ local-summary/
│  │  ├─ hierarchical-merge/
│  │  ├─ citation-map/
│  │  ├─ validate/
│  │  └─ save-artifact/
│  │
│  ├─ dynamic-query/
│  │  ├─ resolve-scope/
│  │  ├─ prepare-query/
│  │  ├─ visual-search/
│  │  ├─ optional-text-search/
│  │  ├─ fuse/
│  │  ├─ rerank/
│  │  ├─ build-evidence/
│  │  ├─ read-evidence/
│  │  ├─ generate-answer/
│  │  ├─ validate-grounding/
│  │  └─ return-citations/
│  │
│  ├─ compare-documents/
│  ├─ incremental-update/
│  └─ artifact-regeneration/
│
├─ contracts/
│  ├─ tool-schemas/
│  ├─ domain-requests/
│  ├─ domain-results/
│  ├─ evidence-schema/
│  ├─ artifact-schema/
│  ├─ source-locator-schema/
│  └─ processing-state-schema/
│
├─ evaluation/
│  ├─ retrieval/
│  │  ├─ recall-at-k/
│  │  ├─ mrr/
│  │  ├─ ndcg/
│  │  └─ page-hit-rate/
│  │
│  ├─ summary/
│  │  ├─ coverage/
│  │  ├─ faithfulness/
│  │  ├─ citation-correctness/
│  │  └─ consistency/
│  │
│  └─ grounded-answer/
│     ├─ evidence-relevance/
│     ├─ answer-faithfulness/
│     ├─ citation-precision/
│     ├─ citation-recall/
│     └─ insufficient-evidence/
│
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ retrieval/
│  ├─ summary/
│  ├─ grounded-answer/
│  ├─ harness-plugin/
│  ├─ permissions/
│  └─ end-to-end/
│
├─ configs/
│  ├─ development/
│  ├─ local/
│  ├─ production/
│  ├─ models/
│  ├─ retrieval/
│  └─ security/
│
├─ scripts/
│  ├─ build-index/
│  ├─ migrate-index/
│  ├─ rebuild-artifacts/
│  ├─ benchmark/
│  └─ maintenance/
│
├─ docs/
│  ├─ VISION.md
│  ├─ STRUCTURE.md
│  ├─ API.md
│  ├─ DATA_MODEL.md
│  ├─ SECURITY.md
│  └─ DEPLOYMENT.md
│
└─ README.md