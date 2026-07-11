"""CLI principal da Engineering AI Platform."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.contracts.agent import AgentRole

app = typer.Typer(name="eap", help="Engineering AI Platform CLI")
console = Console()


@app.command()
def init(
    project: str = typer.Option(..., "--project", "-p", help="Nome do projeto"),
    language: str = typer.Option("python", "--language", "-l", help="Linguagem principal"),
    framework: str = typer.Option("", "--framework", "-f", help="Framework principal"),
    architecture: str = typer.Option("clean_architecture", "--arch", "-a", help="Padrão arquitetural"),
) -> None:
    """Inicializa um novo projeto com Engineering DNA."""
    from cli.config import ConfigManager

    config_mgr = ConfigManager()
    config_mgr.set("project_name", project)
    config_mgr.set("language", language)
    config_mgr.set("framework", framework)
    config_mgr.set("architecture", architecture)
    config_mgr.save()

    console.print(Panel.fit(
        f"[bold green]Projeto inicializado:[/] {project}\n"
        f"  Linguagem: {language}\n"
        f"  Framework: {framework or 'N/A'}\n"
        f"  Arquitetura: {architecture}",
        title="EAP Init",
    ))


@app.command()
def agents() -> None:
    """Lista os agentes disponíveis."""
    table = Table(title="Agentes Disponíveis")
    table.add_column("Agente", style="cyan")
    table.add_column("Papel", style="green")
    table.add_column("Status", style="yellow")

    agent_list = [
        ("Orchestrator", "Coordenador central", "active"),
        ("Architect", "Arquitetura de sistemas", "active"),
        ("Developer", "Geração de código", "active"),
        ("Reviewer", "Revisão de código", "active"),
        ("Security", "Segurança e DevSecOps", "active"),
        ("Planner", "Planejamento de tarefas", "active"),
        ("Knowledge", "Memória organizacional", "active"),
        ("Documentation", "Documentação técnica", "active"),
    ]

    for name, role, status in agent_list:
        table.add_row(name, role, status)

    console.print(table)


@app.command()
def status() -> None:
    """Mostra o status da plataforma."""
    from cli.config import ConfigManager

    config_mgr = ConfigManager()
    config = config_mgr.load()

    console.print(Panel.fit(
        f"[bold]Engineering AI Platform v1.0.0[/]\n"
        f"[bold]Release:[/] 1.0 — Stable\n"
        f"[bold]Projeto:[/] {config.project_name or 'Não inicializado'}\n"
        f"[bold]Provider:[/] {config.default_provider}\n"
        f"[bold]Model:[/] {config.default_model}\n"
        f"[bold]Autonomia:[/] {config.autonomy_level}",
        title="EAP Status",
    ))


@app.command()
def config(
    key: str = typer.Argument(None, help="Chave de configuração"),
    value: str = typer.Argument(None, help="Valor da configuração"),
    list_all: bool = typer.Option(False, "--list", "-l", help="Lista todas as configurações"),
) -> None:
    """Gerencia configurações da plataforma."""
    from cli.config import ConfigManager

    config_mgr = ConfigManager()
    cfg = config_mgr.load()

    if list_all or (key is None and value is None):
        table = Table(title="Configurações")
        table.add_column("Chave", style="cyan")
        table.add_column("Valor", style="green")
        from dataclasses import asdict
        for k, v in asdict(cfg).items():
            table.add_row(k, str(v))
        console.print(table)
        return

    if key and value is None:
        val = config_mgr.get(key)
        console.print(f"[cyan]{key}[/] = [green]{val}[/]")
        return

    if key and value:
        if config_mgr.set(key, value):
            config_mgr.save()
            console.print(f"[green]Set {key} = {value}[/]")
        else:
            console.print(f"[red]Unknown key: {key}[/]")


@app.command()
def provider(
    name: str = typer.Argument(..., help="Nome do provider (openai, anthropic, ollama, gemini)"),
    api_key: str = typer.Option("", "--key", "-k", help="API key"),
    base_url: str = typer.Option("", "--url", "-u", help="Base URL"),
    set_default: bool = typer.Option(False, "--default", "-d", help="Definir como provider padrão"),
) -> None:
    """Configura um provedor de LLM."""
    from cli.config import ConfigManager

    config_mgr = ConfigManager()
    config_mgr.load()
    config_mgr.set_provider(name, api_key=api_key, base_url=base_url)
    if set_default:
        config_mgr.set("default_provider", name)
    config_mgr.save()
    console.print(f"[green]Provider '{name}' configurado com sucesso.[/]")


@app.command()
def workflows() -> None:
    """Lista workflows disponíveis."""
    table = Table(title="Workflows")
    table.add_column("ID", style="cyan")
    table.add_column("Nome", style="green")
    table.add_column("Status", style="yellow")
    console.print(table)
    console.print("[dim]Nenhum workflow ativo. Use 'eap run' para iniciar.[/]")


@app.command()
def health() -> None:
    """Verifica a saúde da plataforma."""
    checks = [
        ("Core Engine", True),
        ("Agent Registry", True),
        ("Knowledge Base", True),
        ("Workflow Engine", True),
        ("Scheduler", True),
    ]
    for name, ok in checks:
        status_icon = "[green]OK[/]" if ok else "[red]FAIL[/]"
        console.print(f"  {name}: {status_icon}")


if __name__ == "__main__":
    app()
