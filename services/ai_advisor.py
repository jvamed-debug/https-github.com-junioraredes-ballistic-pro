"""AI Ballistic Advisor — consultor inteligente de recarga.

Integra a camada de abstração LLM do Engineering-AI-Platform para fornecer
análises e recomendações baseadas em IA para recarga de munições.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AdvisorResponse:
    content: str
    provider: str
    confidence: str = "medium"
    metadata: dict[str, Any] = field(default_factory=dict)


class LLMProviderInterface(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str: ...

    @abstractmethod
    def health_check(self) -> bool: ...


class AnthropicAdvisor(LLMProviderInterface):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self._api_key)
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=1024,
                temperature=0.3,
            )
            return response.content[0].text if response.content else ""
        except Exception as e:
            return f"[Erro Anthropic] {e}"

    def health_check(self) -> bool:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=self._api_key)
            client.messages.create(
                model="claude-haiku-4-5-20251001",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False


class OpenAIAdvisor(LLMProviderInterface):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    @property
    def provider_name(self) -> str:
        return "openai"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1024,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[Erro OpenAI] {e}"

    def health_check(self) -> bool:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self._api_key)
            client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False


BALLISTIC_SYSTEM_PROMPT = """Você é um engenheiro balístico especializado em recarga de munições.
Responda SEMPRE em português brasileiro. Seja técnico, preciso e direto.

REGRAS DE SEGURANÇA (OBRIGATÓRIAS):
1. NUNCA sugira cargas acima do máximo publicado pelos fabricantes (SAAMI/CIP)
2. SEMPRE recomende começar pela carga mínima
3. SEMPRE inclua avisos de segurança quando apropriado
4. Reforce a importância de usar cronógrafo e verificar sinais de pressão

Suas áreas de conhecimento:
- Balística interna (pressão de câmara, queima de pólvora)
- Balística externa (trajetória, vento, drop)
- Balística terminal (energia de impacto, expansão)
- Componentes de recarga (pólvoras, projéteis, espoletas, estojos)
- Análise de agrupamento e precisão
- Calibres brasileiros e internacionais
- Normas SAAMI e CIP"""


class BallisticAdvisor:
    def __init__(self) -> None:
        self._provider: LLMProviderInterface | None = None

    def configure(self, provider_name: str, api_key: str) -> bool:
        if provider_name == "anthropic":
            self._provider = AnthropicAdvisor(api_key)
        elif provider_name == "openai":
            self._provider = OpenAIAdvisor(api_key)
        else:
            return False
        return self._provider.health_check()

    @property
    def is_configured(self) -> bool:
        return self._provider is not None

    def analyze_grouping(self, groups_data: list[dict]) -> AdvisorResponse:
        if not self._provider:
            return self._offline_grouping_analysis(groups_data)

        prompt = f"""Analise os seguintes dados de agrupamento de tiro:

{json.dumps(groups_data, indent=2, ensure_ascii=False)}

Forneça:
1. Avaliação da precisão (excelente/bom/regular/ruim)
2. Possíveis causas para a dispersão observada
3. Sugestões para melhorar o agrupamento
4. Se o POI precisa de ajuste de mira"""

        content = self._provider.complete(BALLISTIC_SYSTEM_PROMPT, prompt)
        return AdvisorResponse(content=content, provider=self._provider.provider_name)

    def suggest_load(self, caliber: str, projectile: str, powder: str, current_data: dict) -> AdvisorResponse:
        if not self._provider:
            return self._offline_load_suggestion(caliber, projectile, current_data)

        prompt = f"""Dados de recarga atual:
- Calibre: {caliber}
- Projétil: {projectile}
- Pólvora: {powder}
- Carga atual: {current_data.get('charge', 'N/A')} grains
- Velocidade atual: {current_data.get('velocity', 'N/A')} fps
- SD atual: {current_data.get('sd', 'N/A')} fps
- Agrupamento: {current_data.get('grouping', 'N/A')} mm

Com base nesses dados, forneça:
1. Avaliação da carga atual
2. Sugestões de ajuste (sempre dentro dos limites SAAMI/CIP)
3. Se o SD está aceitável
4. Próximos passos recomendados"""

        content = self._provider.complete(BALLISTIC_SYSTEM_PROMPT, prompt)
        return AdvisorResponse(content=content, provider=self._provider.provider_name)

    def analyze_performance_trend(self, sessions_summary: list[dict]) -> AdvisorResponse:
        if not self._provider:
            return self._offline_trend_analysis(sessions_summary)

        prompt = f"""Analise a tendência de performance do atirador ao longo destas sessões:

{json.dumps(sessions_summary, indent=2, ensure_ascii=False)}

Forneça:
1. Tendência geral (melhorando/estável/piorando)
2. Padrões identificados
3. Recomendações de treino
4. Ajustes de equipamento sugeridos"""

        content = self._provider.complete(BALLISTIC_SYSTEM_PROMPT, prompt)
        return AdvisorResponse(content=content, provider=self._provider.provider_name)

    def _offline_grouping_analysis(self, groups_data: list[dict]) -> AdvisorResponse:
        analysis_parts = []
        for g in groups_data:
            size_mm = g.get("group_size_mm", 0)
            shots = g.get("shot_count", len(g.get("shots", [])))
            if size_mm < 25:
                rating = "EXCELENTE"
            elif size_mm < 50:
                rating = "BOM"
            elif size_mm < 80:
                rating = "REGULAR"
            else:
                rating = "NECESSITA MELHORIA"
            analysis_parts.append(
                f"Grupo {g.get('id', '?')}: {size_mm:.1f}mm com {shots} impactos - {rating}"
            )

        content = "**Analise Offline (sem IA)**\n\n"
        content += "\n".join(analysis_parts)
        content += "\n\n*Para analise detalhada com IA, configure uma API key nas configuracoes.*"
        return AdvisorResponse(content=content, provider="offline", confidence="low")

    def _offline_load_suggestion(self, caliber: str, projectile: str, current_data: dict) -> AdvisorResponse:
        content = f"**Analise Offline para {caliber}**\n\n"
        vel = current_data.get("velocity", 0)
        sd = current_data.get("sd", 0)
        charge = current_data.get("charge", 0)
        grouping = current_data.get("grouping", 0)

        if charge and charge > 0:
            content += f"- Carga atual: {charge} grains\n"

        if vel and vel > 0:
            content += f"- Velocidade: {vel} fps\n"

        if sd and sd > 0:
            if sd < 10:
                content += f"- SD de {sd} fps: EXCELENTE consistencia\n"
                content += "  - Carga bem ajustada, manter configuracao atual\n"
            elif sd < 20:
                content += f"- SD de {sd} fps: BOM, aceitavel para uso geral\n"
                content += "  - Para competicao, tente ajustes de +/- 0.2gr na carga\n"
            elif sd < 30:
                content += f"- SD de {sd} fps: REGULAR, considere ajustes\n"
                content += "  - Verifique uniformidade do assentamento do projetil\n"
                content += "  - Experimente trocar o lote de espoleta\n"
            else:
                content += f"- SD de {sd} fps: ELEVADO, requer atencao\n"
                content += "  - Verifique o peso dos estojos (uniformidade)\n"
                content += "  - Considere trocar a polvora ou ajustar a carga significativamente\n"
                content += "  - Inspecione o estojo apos o tiro para sinais de pressao\n"

        if grouping and grouping > 0:
            if grouping < 25:
                content += f"- Agrupamento de {grouping}mm: EXCELENTE\n"
            elif grouping < 50:
                content += f"- Agrupamento de {grouping}mm: BOM para uso tatico\n"
            else:
                content += f"- Agrupamento de {grouping}mm: considere revisar tecnica e equipamento\n"

        if not vel and not sd and not grouping:
            content += "- Dados insuficientes para analise. Registre velocidade e SD com cronografo.\n"

        content += "\n**Seguranca:** Sempre comece pela carga minima e suba gradualmente.\n"
        content += "\n*Para sugestoes detalhadas com IA, configure uma API key.*"
        return AdvisorResponse(content=content, provider="offline", confidence="low")

    def _offline_trend_analysis(self, sessions: list[dict]) -> AdvisorResponse:
        content = "**Analise de Tendencia Offline**\n\n"
        content += f"- Total de sessoes analisadas: {len(sessions)}\n"

        if len(sessions) >= 2:
            velocities = [s.get("velocity_avg") or s.get("velocity", 0) for s in sessions if s.get("velocity_avg") or s.get("velocity")]
            sds = [s.get("velocity_sd") or s.get("sd", 0) for s in sessions if s.get("velocity_sd") or s.get("sd")]
            groupings = [s.get("grouping_mm") or s.get("grouping", 0) for s in sessions if s.get("grouping_mm") or s.get("grouping")]

            if velocities:
                avg_vel = sum(velocities) / len(velocities)
                content += f"- Velocidade media: {avg_vel:.0f} fps\n"
                if len(velocities) >= 3:
                    recent = sum(velocities[-3:]) / 3
                    early = sum(velocities[:3]) / 3
                    diff = recent - early
                    if abs(diff) < 10:
                        content += "  - Tendencia: ESTAVEL\n"
                    elif diff > 0:
                        content += f"  - Tendencia: SUBINDO (+{diff:.0f} fps)\n"
                    else:
                        content += f"  - Tendencia: DESCENDO ({diff:.0f} fps)\n"

            if sds:
                avg_sd = sum(sds) / len(sds)
                content += f"- SD medio: {avg_sd:.1f} fps\n"
                if avg_sd < 15:
                    content += "  - Consistencia: BOA\n"
                else:
                    content += "  - Consistencia: IRREGULAR, revise componentes\n"

            if groupings:
                avg_grp = sum(groupings) / len(groupings)
                content += f"- Agrupamento medio: {avg_grp:.1f}mm\n"
                if len(groupings) >= 3:
                    recent_g = sum(groupings[-3:]) / 3
                    early_g = sum(groupings[:3]) / 3
                    if recent_g < early_g * 0.9:
                        content += "  - Precisao: MELHORANDO\n"
                    elif recent_g > early_g * 1.1:
                        content += "  - Precisao: PIORANDO — verifique desgaste do cano\n"
                    else:
                        content += "  - Precisao: ESTAVEL\n"
        else:
            content += "- Registre mais sessoes para analise de tendencia.\n"

        content += "\n*Para analise preditiva com IA, configure uma API key.*"
        return AdvisorResponse(content=content, provider="offline", confidence="low")


advisor = BallisticAdvisor()
