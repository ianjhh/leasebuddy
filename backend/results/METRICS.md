# LeaseBuddy — measured metrics

Generated 2026-09-26. Every number below comes from a run in this repository; nothing is estimated.

## Dataset

- **6 synthetic leases**, 96 pages, 36,127 words (`evals/build_dataset.py`, fixed seed)
- **222 questions** with recorded ground truth, gold page(s) and gold clause(s)

| Category | Count | What it tests |
|---|---|---|
| lookup | 120 | a single clause answers it |
| multi_hop | 36 | needs two clauses combined, usually with arithmetic |
| adversarial | 42 | a confusable clause sits nearby (pet rent vs pet deposit, late fee vs NSF fee) |
| unanswerable | 24 | the lease does not contain the answer; refusing is correct |

Each lease also carries two distractor pages (a fee schedule and a maintenance addendum) that repeat similar dollar amounts in a non-authoritative context.

## Results

### Retrieval quality (deterministic gold-clause matching)

198 answerable questions, top-5 retrieval, identical queries across all three arms.

| Method | recall@1 | recall@3 | recall@5 | page@5 | MRR | p50 latency |
|---|---|---|---|---|---|---|
| **hybrid_rrf** | 86.4% (171/198) | 99.5% (197/198) | 100.0% (198/198) | 100.0% (198/198) | 0.974 | 35 ms |
| vector_only | 81.8% (162/198) | 99.5% (197/198) | 100.0% (198/198) | 100.0% (198/198) | 0.946 | 28 ms |
| keyword_only | 21.2% (42/198) | 21.2% (42/198) | 21.2% (42/198) | 21.2% (42/198) | 0.212 | 8 ms |

recall@5 by category:

| Category | hybrid_rrf | vector_only | keyword_only |
|---|---|---|---|
| adversarial | 100.0% (42/42) | 100.0% (42/42) | 14.3% (6/42) |
| lookup | 100.0% (120/120) | 100.0% (120/120) | 30.0% (36/120) |
| multi_hop | 100.0% (36/36) | 100.0% (36/36) | 0.0% (0/36) |

### End-to-end generation (real retrieval + LangGraph agent)

60 questions.

| Metric | Value |
|---|---|
| Exact answer accuracy (answerable) | **77.8% (35/45)** |
| Refusal accuracy (unanswerable) | **100.0% (15/15)** |
| False refusal rate (answerable) | 15.6% (7/45) |
| Citation page accuracy | **64.4% (29/45)** |
| Latency median / p95 | 35.5s / 55.1s |

By category:

| Category | Accuracy |
|---|---|
| adversarial | 66.7% (10/15) |
| lookup | 100.0% (15/15) |
| multi_hop | 66.7% (10/15) |
| unanswerable | 100.0% (15/15) |

Retrieval passes actually taken by the agent:

| Passes | Questions |
|---|---|
| 1 | 37 |
| 2 | 23 |

### Generation with gold context (retrieval isolated out)

222 questions.

| Metric | Value |
|---|---|
| Exact answer accuracy (answerable) | **89.9% (178/198)** |
| Refusal accuracy (unanswerable) | **100.0% (24/24)** |
| False refusal rate (answerable) | 4.5% (9/198) |
| Citation page accuracy | **74.2% (147/198)** |
| LLM-judge faithfulness | 96.8% (215/222) |
| LLM-judge relevancy | 85.6% (190/222) |
| Latency median / p95 | 2.2s / 4.8s |

By category:

| Category | Accuracy |
|---|---|
| adversarial | 78.6% (33/42) |
| lookup | 100.0% (120/120) |
| multi_hop | 69.4% (25/36) |
| unanswerable | 100.0% (24/24) |

### Infrastructure claims

| Check | Claim | Observed | Result |
|---|---|---|---|
| vector_dimension | 768-dim embeddings | `768-dim` | PASS |
| hnsw_index | HNSW index, m=16, ef_construction=64, cosine | `no HNSW index found on lease_chunks` | **FAIL** |
| corpus_indexed | corpus is present for retrieval | `0 documents, 0 chunks` | **FAIL** |
| rrf_k | Reciprocal Rank Fusion k=60 | `k values in shipped SQL: ['60']` | PASS |
| candidate_pool | 50 candidates narrowed to top 5 | `5 x 10 = 50 candidates -> top 5` | PASS |
| cache_ttl | 1-hour response cache TTL | `CACHE_TTL_SECONDS=3600` | PASS |
| cache_wired | response cache is on the request path | `callers of generate_chat_response: none` | **FAIL** |
| api_reachable | API is running | `http://127.0.0.1:8000` | PASS |
| accept_status | upload returns 202 Accepted | `declared success codes for POST /api/leases/: ['202', '422']` | PASS |
| upload_size_limit | rejects uploads over 20 MB | `20.0 MB upload -> HTTP 413` | PASS |
| upload_type_filter | rejects unsupported file types | `'.exe' upload -> HTTP 400` | PASS |
| rate_limit | sliding window at 60 req/min per IP | `first 429 on request #57, 56 allowed through` | PASS |
| ws_token_streaming | token-by-token streaming over WebSocket | `no ingested lease ids; run evals.ingest_corpus first` | skipped |
