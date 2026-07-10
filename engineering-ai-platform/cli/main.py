"""CLI principal da Engineering AI Platform."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="eap", help="Engineering AI Platform CLI")
console = Console()


@app.command()
def init(
    project: str = typer.Option(..., "--project", "-p", help="Nome do projeto"),
    language: str = typer.Option("python", "--language", "-l", help="Linguagem principal"),
    framework: str = typer.Option("", "--framework", "-f", help="Framework principal"),
) -> None:
    """Inicializa um novo projeto com Engineering DNA."""
    console.print(f"[bold green]Inicializando projeto:[/] {project}")
    console.print(f"  Linguagem: {language}")
    console.print(f"  Framework: {framework}")
    console.print("[bold green]Projeto inicializado com sucesso.[/]")


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
        ("Knowledge", "Memória organizacional", "planned"),
        ("Documentation", "Documentação técnica", "planned"),
    ]

    for name, role, status in agent_list:
        table.add_row(name, role, status)

    console.print(table)


@app.command()
def status() -> None:
    """Mostra o status da plataforma."""
    console.print("[bold]Engineering AI Platform v0.1.0[/]")
    console.print("[bold]Release:[/] 0.1 — Foundation")
    console.print("[bold]Status:[/] Em desenvolvimento")


if __name__ == "__main__":
    app()
