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
- [x] Knowledge Agent (busca, indexação, recomendação de padrões, gestão de ADRs)
- [x] Documentation Agent (geração de docs, API docs, runbooks, READMEs)
- [x] Agent autonomy levels (supervised/semi/autonomous/full, aprovações, cost limits)
- [x] Agent communication protocol (MessageBus, broadcast, request/response, delegation)

## Release 0.7 — API
- [x] REST API (EAPApplication com rotas para agents, projects, workflows)
- [x] WebSocket streaming (WebSocketManager, canais, eventos em tempo real)
- [x] Auth / Rate limiting (API keys, scopes, rate limiting por janela)
- [x] Middleware (RequestLogger, CORS, ErrorHandler)

## Release 0.8 — CLI
- [x] CLI completo (init, agents, status, config, provider, workflows, health)
- [x] Interactive mode (REPL com comandos built-in, histórico, contexto)
- [x] Config management (PlatformConfig, persistência JSON, providers)

## Release 0.9 — Enterprise
- [x] Multi-tenant (TenantManager, planos Free/Starter/Pro/Enterprise, limites)
- [x] Audit log (AuditLog imutável, queries por actor/action/tenant, security events)
- [x] RBAC (RBACManager, 5 system roles, 10 permissions, resource policies)

## Release 1.0 — Stable
- [x] Primeira versão funcional completa
- [x] Todos os agentes operacionais (8 agentes especializados)
- [x] API REST com auth e WebSocket
- [x] CLI completo com modo interativo
- [x] Enterprise: multi-tenant, audit, RBAC
- [x] 100+ testes unitários
