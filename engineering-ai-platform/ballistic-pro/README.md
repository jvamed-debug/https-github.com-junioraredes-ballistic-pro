# 🎯 Ballistic Pro - Sistema Avançado de Gestão de Recarga

Bem-vindo ao **Ballistic Pro**, sua suíte completa para gestão de recarga de munições, controle de acervo e análise de performance com visão computacional.

## 🚀 Funcionalidades Principais

*   **Gestão de Acervo**: Controle completo de armas, com alertas de vencimento de CRAF e manutenção.
*   **Diário de Recarga Inteligente**: Registre suas cargas e o sistema dá baixa automática no estoque de insumos.
*   **Controle de Estoque**: Monitore sua quantidade de pólvora, espoletas, projéteis e estojos, com cálculo automático de custo por munição.
*   **Visão Computacional (Ballistic CV)**: Tire uma foto do seu alvo e o sistema calcula automaticamente o agrupamento (Group Size) e o Raio Médio.
*   **Banco de Dados Integrado**: Já vem com cargas de referência para pólvoras CBC (216, 219, etc.) e calibres populares.

---

## 🛠️ Instalação e Execução

### Pré-requisitos
*   Python 3.10 ou superior

### Passo 1: Acesse a pasta do projeto
No seu terminal, execute:
```bash
cd /Users/junioraredes/.gemini/antigravity/scratch/ballistic-pro/
```

### Passo 2: Instale as dependências
```bash
pip install -r requirements.txt
```

### Passo 3: Execute o App
```bash
python3 -m streamlit run app.py
```
*(Ou apenas execute `./run_app.sh` se preferir)*

---

## 👤 Login de Demonstração
Para acessar todas as funcionalidades (incluindo Premium):
*   **Usuário**: `atirador_pro`
*   **Senha**: `senha123`

---

## 📂 Estrutura do Projeto
*   `app.py`: Aplicação principal (Interface Gráfica).
*   `cv_utils.py`: Módulo de Visão Computacional (OpenCV).
*   `models.py`: Definição do Banco de Dados (SQLAlchemy).
*   `ballistics.db`: Banco de Dados SQLite (Armazena usuários, armas e insumos).
*   `database.json`: Catálogo de Cargas (Dados de referência de fábrica).

## ⚠️ Aviso de Segurança
A recarga de munições envolve riscos. Sempre cruze as informações deste software com os manuais oficiais dos fabricantes de pólvora. Inicie sempre com a carga mínima.
