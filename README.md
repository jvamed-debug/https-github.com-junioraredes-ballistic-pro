# Assistente de Recarga Balística

Esta aplicação foi desenvolvida com o Google Antigravity para auxiliar no processo de recarga de munição, fornecendo dados verificados de manuais técnicos e um modo manual seguro para cargas personalizadas.

## Funcionalidades
- **Base de Dados Verificada**: Dados extraídos automaticamente do Manual de Recarga CBC.
- **Seleção Hierárquica**: Filtra opções por Calibre -> Projétil -> Pólvora.
- **Modo Manual ("Outro")**: Permite entrada de dados personalizada com avisos de segurança quando a combinação não está no banco de dados.
- **Resumo de Carga**: Exibe claramente as cargas Mínima e Máxima para referência rápida.

## Como Executar

1. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Execute a aplicação**:
   ```bash
   streamlit run app.py
   ```

## Estrutura de Arquivos
- `app.py`: Código fonte da interface Streamlit.
- `database.json`: Banco de dados JSON extraído dos PDFs.
- `extract_cbc.py`: Script utilizado para extrair dados do manual CBC.
- `requirements.txt`: Lista de bibliotecas Python necessárias.

## Aviso Legal
Esta ferramenta é apenas para fins informativos. A recarga de munição envolve riscos de explosão e ferimentos graves. Sempre consulte os manuais oficiais do fabricante da pólvora.
