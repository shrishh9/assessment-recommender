# Approach

## Problem Understanding

The task is to build a conversational API that recommends SHL assessments based on hiring context. The system must understand incomplete requests, ask clarifying questions when needed, retrieve real SHL catalog assessments, and return a strict JSON response suitable for automated evaluation.

## Overall Architecture

The application is a stateless FastAPI service. Each request sends the full conversation history to `POST /chat`. The workflow is:

```text
FastAPI -> Planner -> Orchestrator -> Retriever -> Groq -> Formatter -> JSON response
```

The API exposes `GET /health` for deployment checks and `POST /chat` for conversation turns.

## Catalog Ingestion

The ingestion layer fetches the official SHL JSON catalog, normalizes product records, validates SHL product URLs, deduplicates records, and stores the cleaned data in `data/assessments.json`. Important fields such as name, URL, description, job levels, duration, languages, and keywords are preserved for retrieval.

## Retrieval Strategy

The retrieval pipeline builds text representations from each assessment and embeds them with Sentence Transformers. FAISS stores normalized embeddings for fast semantic search. At query time, the retriever returns the top catalog matches. Recommendation identity fields such as `name`, `url`, and `test_type` are always taken from catalog metadata.

## Prompt Engineering

Separate prompt templates are used for clarification, recommendation, comparison, refinement, and refusal. Prompts instruct the model to rely only on retrieved catalog evidence and not invent assessment names, URLs, or test types. Clarification and refusal prompts are intentionally short and constrained.

## Planner And Orchestrator Design

The planner is deterministic and rule-based. It reads the complete conversation history and decides whether to clarify, recommend, compare, refine, or refuse. This makes behavior explainable and stable for evaluation. The custom orchestrator in `agent/graph.py` routes planner actions to node handlers and invokes retrieval only when catalog evidence is required.

## LLM Choice

Groq is used for low-latency response generation. The LLM is responsible for wording the final response, while the recommendation objects are produced from retrieved SHL catalog metadata to keep the API contract reliable.

## Evaluation Approach

The project is evaluated with API tests, planner behavior checks, schema validation, and representative conversation flows for clarification, recommendation, comparison, refinement, and refusal. The final review verifies stateless behavior, health check output, recommendation shape, recommendation count, empty arrays for clarification/refusal, and the 8-message conversation limit.

## Challenges Encountered

Some SHL catalog records have blank `test_type` values, so the formatter falls back to catalog keywords when needed. Another issue was a false off-topic match where `skills` contained the substring `kill`; this was fixed by matching off-topic terms as complete words or phrases.

## Improvements Made During Development

The final integration connected FastAPI to the existing planner, orchestrator, retriever, Groq client, and response formatter. The API boundary now enforces the 8-message limit, caps recommendations at 10, preserves empty recommendations for clarification/refusal, loads `.env` configuration, and includes Render deployment configuration.

## AI Tools Used

AI assistance was used to review code, identify evaluator-facing gaps, generate documentation, and validate representative flows. The core architecture remained the project’s existing FastAPI, planner, retrieval, orchestration, and Groq design.

## Future Improvements

Future work could add a browser chat UI, expanded evaluation traces, richer planner extraction rules, retrieval score diagnostics, and deployment-time caching for faster cold starts.
