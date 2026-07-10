# Arquitetura — Engineering AI Platform

## Visão Geral

```
┌─────────────────────────────────────────────────────┐
│                      CLI / API                       │
├─────────────────────────────────────────────────────┤
│                   Orchestrator Agent                 │
│  ┌─────────┬──────────┬──────────┬────────────────┐ │
│  │Architect│Developer │ Reviewer │   Security     │ │
│  │ Agent   │  Agent   │  Agent   │    Agent       │ │
│  └─────────┴──────────┴──────────┴────────────────┘ │
│  ┌─────────┬──────────┐                             │
│  │ Planner │Knowledge │                             │
│  │ Agent   │  Agent   │                             │
│  └─────────┴──────────┘                             │
├─────────────────────────────────────────────────────┤
│                  Engineering Kernel                   │
│  ┌────────────┬───────────┬──────────┬────────────┐ │
│  │   Engine   │  Planner  │Validator │  Executor  │ │
│  └────────────┴───────────┴──────────┴────────────┘ │
├─────────────────────────────────────────────────────┤
│                  Runtime Layer                        │
│  ┌──────────────┬─────────────┬──────────────────┐  │
│  │Task Engine   │Workflow Eng.│   Scheduler      │  │
│  └──────────────┴─────────────┴──────────────────┘  │
├─────────────────────────────────────────────────────┤
│                  Memory Layer                        │
│  ┌──────────────┬─────────────┬──────────────────┐  │
│  │     RAG      │  Knowledge  │  Asset Store     │  │
│  │  Retriever   │    Graph    │                  │  │
│  └──────────────┴─────────────┴──────────────────┘  │
├─────────────────────────────────────────────────────┤
│               LLM Provider Interface                 │
│  ┌──────────────┬─────────────┬──────────────────┐  │
│  │   OpenAI     │  Anthropic  │   Ollama (local) │  │
│  └──────────────┴─────────────┴──────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Princípio Fundamental

> Nenhum componente pode depender diretamente de um modelo de IA específico.

## Pipeline de Engenharia

```
Entrada → Classificação → Contextualização → Recuperação →
Planejamento → Arquitetura → Implementação → Validação →
Documentação → Knowledge Capture → Entrega
```

## Domínios

Architecture, Backend, Frontend, Infrastructure, Security, Database,
Data Engineering, AI/ML, DevOps, Cloud, Testing, Documentation,
Governance, Knowledge, Automation.

## Engenharia Baseada em Evidências

| Nível | Origem |
|-------|--------|
| E0 | Hipótese |
| E1 | Experiência prática documentada |
| E2 | Documentação oficial |
| E3 | Norma técnica |
| E4 | Benchmark reproduzível |
| E5 | Evidência validada no projeto |
