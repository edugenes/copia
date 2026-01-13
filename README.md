# 📁 FileCopy Verifier

Software completo para cópia massiva de arquivos com verificação de integridade, contagem de arquivos e análise de tamanho.

## 🎯 Características Principais

- ✅ Cópia massiva de arquivos com preservação de estrutura
- ✅ Verificação de integridade usando hash (SHA-256)
- ✅ Contagem de arquivos e análise de tamanho
- ✅ Interface gráfica intuitiva
- ✅ Logs detalhados de operações
- ✅ Relatórios de cópia e verificação

## 🚀 Instalação

### Requisitos
- Python 3.10 ou superior
- Windows, Linux ou macOS

### Passos

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd FileCopy-Verifier
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
```

3. Ative o ambiente virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/macOS:
```bash
source venv/bin/activate
```

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

## 📖 Uso

### Interface Gráfica

1. Execute a aplicação:
```bash
python src/main.py
```

2. Na interface:
   - **Origem:** Clique em "Selecionar" e escolha:
     - Um arquivo único
     - Múltiplos arquivos (Ctrl+Click ou Shift+Click)
     - Um diretório (clique em Cancelar no diálogo de arquivos e selecione pasta)
   - **Destino:** Clique em "Selecionar" e escolha:
     - Um arquivo (para cópia de arquivo único com novo nome)
     - Um diretório (clique em Cancelar no diálogo de arquivos e selecione pasta)
   - Clique em "Escanear Origem" para ver estatísticas dos arquivos
   - Clique em "Iniciar Cópia" para copiar os arquivos
   - Clique em "Verificar Integridade" para verificar se os arquivos foram copiados corretamente

### Funcionalidades

- **Suporte Flexível:**
  - ✅ Copiar arquivo único
  - ✅ Copiar múltiplos arquivos selecionados
  - ✅ Copiar diretório completo com todas as subpastas
  
- **Escanear Origem:** Analisa o arquivo(s) ou diretório de origem e exibe estatísticas (número de arquivos, tamanho total, etc.)
- **Iniciar Cópia:** Copia os arquivos selecionados ou todo o diretório para o destino, preservando a estrutura de pastas quando aplicável
- **Verificar Integridade:** Compara os arquivos origem e destino usando hash SHA-256 para garantir que foram copiados corretamente
- **Interface Moderna:** Animações fluidas, progresso em tempo real, tabela de arquivos sendo copiados com porcentagem individual

### Logs

Os logs são salvos automaticamente em `logs/filecopy_YYYYMMDD.log` e também exibidos na interface.

## 📁 Estrutura do Projeto

```
FileCopy-Verifier/
├── src/
│   ├── core/           # Lógica de negócio
│   ├── ui/             # Interface gráfica
│   ├── utils/          # Utilitários
│   └── database/       # Banco de dados
├── tests/              # Testes
├── docs/               # Documentação
├── logs/               # Logs de execução
└── reports/            # Relatórios gerados
```

## 🛠️ Desenvolvimento

### Executar Testes
```bash
pytest tests/
```

### Formatação de Código
```bash
black src/
```

### Linting
```bash
pylint src/
```

## 📝 Roadmap

Veja o arquivo [ROADMAP.md](ROADMAP.md) para o plano completo de desenvolvimento.

## 📄 Licença

[Definir licença]

## 👥 Contribuidores

[Seus nomes]

---

**Status:** 🚧 Em Desenvolvimento - Fase 0 (Setup)

