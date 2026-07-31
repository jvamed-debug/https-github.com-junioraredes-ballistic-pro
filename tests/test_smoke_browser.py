"""Smoke test que abre o app num navegador de verdade.

Existe porque a suite unitaria nao alcanca o que quebra na tela. Tres bugs
desta classe passaram por ela sem serem notados:

  - a tela de login morria antes de desenhar o formulario, porque consultar
    st.secrets sem arquivo de secrets levanta excecao — o estado normal de um
    deploy que usa variaveis de ambiente;
  - a aba de performance levantava KeyError em toda renderizacao, por um
    .format() sobre um template que carregava expressao de f-string;
  - os avisos de seguranca do diario eram desenhados e imediatamente
    descartados pelo st.rerun() que fechava a gravacao.

Nenhum deles aparecia com a suite verde e o endpoint de health respondendo,
porque nenhum dos dois executa codigo de renderizacao.

Nao roda por padrao: precisa de navegador e leva dezenas de segundos.

    pytest -m browser

O Chromium do ambiente e localizado por PLAYWRIGHT_BROWSERS_PATH ou pelo
caminho padrao do contêiner.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

pytestmark = pytest.mark.browser

REPO_ROOT = Path(__file__).resolve().parent.parent
ADMIN_PASSWORD = "SmokeTest123!"
STARTUP_TIMEOUT_S = 90


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _chromium_path() -> str | None:
    """Caminho explicito do Chromium, ou None para deixar o Playwright achar.

    O contêiner deste projeto traz o navegador em /opt/pw-browsers e aponta
    PLAYWRIGHT_BROWSERS_PATH para la. Um `playwright install` comum instala em
    ~/.cache/ms-playwright, que o proprio Playwright resolve sozinho — por isso
    None nao significa ausencia, significa "use o padrao".
    """
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    candidates = []
    if base:
        candidates += sorted(Path(base).glob("chromium-*/chrome-linux/chrome"))
        candidates.append(Path(base) / "chromium")
    candidates += sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"))
    for path in candidates:
        if Path(path).exists():
            return str(path)
    return None


def _unavailable(reason: str):
    """Pula na maquina de quem nao tem navegador; falha no CI.

    Um skip aparece como job verde. A primeira versao deste arquivo procurava
    o Chromium so em /opt/pw-browsers, entao no GitHub Actions ela pulava os
    dois testes e o job passava depois de instalar um navegador que nunca
    abriu — verde sem exercitar nada. No CI isso tem que doer.
    """
    if os.environ.get("CI") == "true":
        pytest.fail(f"navegador indisponivel no CI: {reason}")
    pytest.skip(reason)


def _launch_chromium(playwright):
    """Abre o Chromium, pelo caminho explicito ou pela resolucao do Playwright.

    O contêiner deste projeto traz o navegador num caminho proprio; um
    `playwright install` comum deixa o Playwright resolver sozinho.
    """
    explicit = _chromium_path()
    if explicit:
        return playwright.chromium.launch(executable_path=explicit)
    try:
        return playwright.chromium.launch()
    except Exception as exc:
        _unavailable(f"nenhum Chromium utilizavel: {exc}")


def _wait_for_health(port: int, process: subprocess.Popen) -> None:
    url = f"http://127.0.0.1:{port}/_stcore/health"
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(f"streamlit saiu com codigo {process.returncode} antes de subir")
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    pytest.fail(f"app nao respondeu em {STARTUP_TIMEOUT_S}s")


@pytest.fixture(scope="module")
def running_app():
    """Sobe o app com um banco descartavel e o derruba ao final."""
    try:
        import playwright.sync_api  # noqa: F401
    except ImportError:
        _unavailable("playwright nao instalado")

    port = _free_port()
    with tempfile.TemporaryDirectory() as tmp:
        env = {
            **os.environ,
            "DATABASE_URL": f"sqlite:///{Path(tmp) / 'smoke.db'}",
            #  Sem isto o app se recusa a criar o usuario inicial, que e
            #  exatamente o comportamento de producao verificado em #28.
            "ADMIN_PASSWORD": ADMIN_PASSWORD,
        }
        process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app.py",
             f"--server.port={port}", "--server.headless=true"],
            cwd=REPO_ROOT, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            _wait_for_health(port, process)
            yield f"http://127.0.0.1:{port}"
        finally:
            process.terminate()
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()


@pytest.fixture(scope="module")
def logged_in_page(running_app):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = _launch_chromium(pw)
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.goto(running_app, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(4_000)

        body = page.inner_text("body")
        assert "Traceback" not in body, f"tela de login quebrada:\n{body[:800]}"

        page.get_by_label("Usuário").fill("atirador_pro")
        page.get_by_label("Senha").fill(ADMIN_PASSWORD)
        page.get_by_role("button", name="ENTRAR").click()
        page.wait_for_timeout(8_000)

        assert "OPERADOR" in page.inner_text("body"), "login nao completou"
        yield page
        browser.close()


def test_login_screen_renders_without_a_secrets_file(running_app):
    """O deploy alvo nao tem secrets.toml — ler st.secrets ali levantava."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = _launch_chromium(pw)
        page = browser.new_page()
        page.goto(running_app, wait_until="networkidle", timeout=60_000)
        page.wait_for_timeout(4_000)
        body = page.inner_text("body")
        browser.close()

    assert "Traceback" not in body
    assert "StreamlitSecretNotFound" not in body
    assert "ENTRAR" in body


def test_every_tab_renders(logged_in_page):
    """A aba de performance levantava KeyError em toda abertura."""
    tabs = logged_in_page.get_by_role("tab")
    count = tabs.count()
    assert count >= 8, f"esperava as oito abas, encontrei {count}"

    failures = []
    for index in range(count):
        name = tabs.nth(index).inner_text().strip()
        logged_in_page.get_by_role("tab").nth(index).click()
        logged_in_page.wait_for_timeout(4_000)
        body = logged_in_page.inner_text("body")
        if "Traceback" in body:
            excerpt = body[body.find("Traceback"):][:300].replace("\n", " ")
            failures.append(f"{name}: {excerpt}")

    assert not failures, "abas com erro:\n" + "\n".join(failures)
