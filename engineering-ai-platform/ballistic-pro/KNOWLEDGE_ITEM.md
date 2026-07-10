# Knowledge Item: Ballistic Pro Architecture & Logic (Refactored v2.0)

## 🎯 Overview
Ballistic Pro is an advanced ammunition reloading management system and performance analysis tool. It serves as a reference for precision shooting logic, inventory deduction patterns, and computer vision (CV) integration.

## 📁 Repository Location
- **Path**: `/Users/junioraredes/n8n urgent/ballistic-pro`
- **Structure**:
  - `app.py`: Hub Central (Roteamento e Auth).
  - `core/`: Modelos de dados e Autenticação centralizada.
  - `services/`: Lógica de negócio (Cálculos Balísticos, Gestão de Inventário).
  - `modules/`: Componentes visuais das abas (Performance, Perfil, Dados).
  - `ui/`: Design System e Estilos Premium (CSS).

## 🧠 Key Logic Modules
### 1. Inventory & Costing (`services/reloading_service.py`)
- **Deduction Pattern**: Subtração automática de insumos por Lote (Batch).
- **Batch Tracking**: Suporte para nº de lote e data de validade.
- **Cost Calculation**: Cálculo de custo médio ponderado por munição.

### 2. Ballistic CV 2.0 (`cv_utils.py`)
- **Multi-Group Detection**: Identifica múltiplos grupos de disparos no mesmo alvo via clustering.
- **Auto-Calibration**: Calibração de escala mm/pixel automática usando moedas de 1 Real.
- **POI Calculation**: Cálculo do desvio do ponto de impacto em relação ao centro do alvo.

### 3. Verification & Safety (`database.json`)
- Dados SAAMI e imagens técnicas deblueprint para dimensões de cartuchos.
- **Modo Verificado**: Garante que cargas estejam dentro da zona de segurança do fabricante.

## 🛠️ Usage for Other Projects
- **n8n Integration**: Conecte ao MCP Server para alertas de estoque e dashboards externos.
- **Design Pattern**: Referência para interfaces Streamlit de alta fidelidade (Premium UI/UX).

## 🔗 Connections
- **Antigravity Kit**: Orquestração via agentes especialistas.
- **MCP Server**: Exposição das APIs de cálculo para integração corporativa.
