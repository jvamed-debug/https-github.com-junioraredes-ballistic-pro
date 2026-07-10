# Roadmap — Engineering AI Platform

## Release 0.1 — Foundation
- [x] Estrutura do repositório
- [x] README, LICENSE, Roadmap
- [x] Arquitetura
- [x] Contratos (LLM Provider, Agent, Asset)
- [x] Engineering Engine
- [x] Project DNA
- [x] CLI básico
- [x] Testes unitários

## Release 0.2 — Kernel
- [x] Core Workflow (WorkflowDefinition, WorkflowBuilder)
- [x] Models registry (ModelsRegistry)
- [x] Planner avançado (ExecutionPlanner com fases e priorização)
- [x] Validator (regras configuráveis, validação de código e arquitetura)
- [x] Executor (execução coordenada de planos)
- [x] Review Engine (checklists, findings, scoring)

## Release 0.3 — Knowledge Engine
- [x] RAG com vetores (InMemoryVectorStore, similaridade cosseno)
- [x] Text Chunker (divisão com overlap inteligente)
- [x] Asset Store (EAM com IDs únicos, busca e filtros)
- [x] ADR manager (create/accept/deprecate/supersede, markdown export)
- [x] Pattern Library (5 padrões default: Repository, CQRS, Circuit Breaker, Strangler Fig, Event Sourcing)
- [x] Templates engine ({{variable}} substitution, 4 templates default)
- [x] Snippet Store (busca por nome, tags e linguagem)

## Release 0.4 — Integrations
- [x] GitHub Client (repos, PRs, commits, branches, file content)
- [x] GitLab Client (projects, merge requests, branches)
- [x] Ollama Provider (modelos locais, streaming, health check)
- [x] Gemini Provider (Google Gemini API)
- [x] Provider Factory (fábrica unificada de provedores LLM)
- [x] Docker Client (containers, images, logs)
- [x] Kubernetes Client (pods, deployments, services, scaling)
- [x] PostgreSQL Client (queries, pgvector, vector search)
- [x] Redis Client (cache, filas, pub/sub)
- [x] Qdrant Client (vector database, collections, search)

## Release 0.5 — Runtime
- [x] Workflow Engine completo (execução de workflows, gates, handlers)
- [x] Scheduler (jobs únicos, periódicos, tick-based execution)
- [x] Agent Coordinator (estratégias sequential/parallel/pipeline, auto-assign)

## Release 0.6 — Agents
- [ ] Knowledge Agent
- [ ] Documentation Agent
- [ ] Agent autonomy levels
- [ ] Agent communication protocol

## Release 0.7 — API
- [ ] REST API (FastAPI)
- [ ] WebSocket streaming
- [ ] Auth / Rate limiting

## Release 0.8 — CLI
- [ ] CLI completo
- [ ] Interactive mode
- [ ] Config management

## Release 0.9 — Enterprise
- [ ] Multi-tenant
- [ ] Audit log
- [ ] RBAC

## Release 1.0 — Stable
- [ ] Primeira versão funcional completa
