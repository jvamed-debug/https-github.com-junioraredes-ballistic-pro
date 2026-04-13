---
name: internal-audit
description: Auditoria interna completa de aplicações — segurança, qualidade, funcionalidade, UX e prontidão para produção.
allowed-tools: Read, Write, Edit, run_command
version: 1.0
priority: HIGH
---

# Skill: /internal-audit

## O que é
Comando Antigravity que realiza auditoria interna completa de aplicações — segurança, qualidade, funcionalidade, UX, edge cases e prontidão para produção. Atua como engenheiro sênior + arquiteto + QA + especialista em segurança.

## Como usar

```
/internal-audit
```
Audita o projeto atual completo.

```
/internal-audit segurança
```
Foca a auditoria em segurança (ainda executa todas as etapas, mas prioriza esse eixo).

## Etapas executadas
1. Mapeamento do sistema (rotas, entidades, fluxos, integrações)
2. Segurança ofensiva e defensiva (auth, autorização, injeção, PII, RLS)
3. Validação funcional (Server Actions, formulários, fluxos críticos)
4. Revisão técnica (código, banco, performance, APIs externas)
5. UX e acessibilidade (feedbacks, responsividade, mensagens de erro)
6. Edge cases e resiliência (dados inválidos, falhas, sessões)
7. Plano de testes automatizados (5 testes críticos priorizados)

## Output
Relatório estruturado com:
- Resumo executivo
- Problemas por severidade (SEV 1 a SEV 4) com correção prática
- Plano de correção priorizado com estimativa de esforço
- Veredito: PRONTO / NÃO PRONTO para produção

## Severidades
| Nível | Significado |
|-------|-------------|
| SEV 1 | Bloqueador — impede ida a produção |
| SEV 2 | Risco operacional sério |
| SEV 3 | Melhoria importante |
| SEV 4 | Nice-to-have / futuro |

## Comportamento
- Baseado em evidências: lê código real, não assume funcionalidade
- Diferencia fato observado de hipótese
- Inclui código/SQL de correção, não apenas descrição do problema
