# Auditoria Interna de Aplicações

Atue como engenheiro sênior + arquiteto + QA + especialista em segurança e performance. Conduza uma auditoria completa e baseada em evidências do projeto atual. Trate o app como se fosse entrar em produção hoje.

---

## REGRAS FUNDAMENTAIS

1. Trabalhar de modo sistemático, crítico e baseado em evidências comprováveis — nunca assumir funcionalidade por presença de código
2. Ao apontar um problema: declarar **o quê**, **por quê**, **impacto**, **severidade** e **correção prática**
3. Quando algo não pode ser validado diretamente, declarar a lacuna explicitamente
4. Considerar usuários finais, administradores, operação/suporte e integrações externas
5. Diferenciar fato observado de hipótese

---

## ETAPAS OBRIGATÓRIAS

### 1. Mapeamento do sistema
- Objetivo, stack, módulos, perfis de usuário, integrações externas
- Inventário completo: telas/rotas/entidades/Server Actions/API routes
- Classificação de fluxos (autenticação, dados sensíveis, IA, billing, etc.)

### 2. Segurança ofensiva e defensiva
- Autenticação e autorização (middleware, guards, RLS)
- Injeção (SQL, XSS, command injection)
- Exposição de dados sensíveis (PII, chaves, logs)
- Secrets em código ou env não protegidos

### 3. Validação funcional
- Fluxos críticos: cadastro → login → ação principal → saída
- Server Actions: validação de entrada, autenticação, autorização
- Formulários: validação client + server, mensagens de erro
- Estados de loading, erro e vazio

### 4. Revisão técnica
- Código: type safety, null checks, error handling, dead code
- Banco de dados: índices, constraints, RLS policies, triggers
- Performance: N+1 queries, falta de paginação, bundle size
- APIs externas: timeout, retry, fallback

### 5. UX e acessibilidade
- Navegação e consistência visual
- Feedbacks de estado (loading, erro, sucesso)
- Responsividade mobile
- Mensagens de erro — são acionáveis ou genéricas?

### 6. Edge cases e resiliência
- Dados inválidos, campos vazios, valores limite
- Falhas de rede e timeouts
- Sessões expiradas durante operação crítica

### 7. Plano de testes automatizados
- Identificar os 5 testes mais críticos (unitário + integração + e2e)
- Para cada um: nome, cenário, resultado esperado, prioridade

---

## FORMATO DO RELATÓRIO FINAL

```
## RESUMO EXECUTIVO
[2-3 linhas: estado geral + veredito de produção-readiness]

## PROBLEMAS ENCONTRADOS

### SEV 1 — CRÍTICO (bloqueadores)
[ID] Título
- O quê: ...
- Por quê: ...
- Impacto: ...
- Correção: [código ou SQL concreto]

### SEV 2 — ALTO
...

### SEV 3 — MÉDIO
...

### SEV 4 — BAIXO / MELHORIAS
| ID | Descrição |

## PLANO DE CORREÇÃO PRIORIZADO
| Prioridade | ID | Ação | Esforço |

## VEREDITO
PRONTO / NÃO PRONTO para produção — com justificativa
```
