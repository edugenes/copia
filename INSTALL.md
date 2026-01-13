# 📦 Guia de Instalação - FileCopy Verifier

## Requisitos do Sistema

- **Python:** 3.10 ou superior
- **Sistema Operacional:** Windows, Linux ou macOS
- **Espaço em disco:** ~50 MB (sem dependências)

## Instalação Passo a Passo

### 1. Clone ou Baixe o Projeto

```bash
# Se usando Git
git clone <url-do-repositorio>
cd FileCopy-Verifier

# Ou baixe e extraia o ZIP
```

### 2. Crie um Ambiente Virtual (Recomendado)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

Isso instalará:
- PyQt5 (interface gráfica)
- pytest (testes)
- black, pylint, flake8 (ferramentas de desenvolvimento)

### 4. Execute a Aplicação

```bash
python src/main.py
```

## Verificação da Instalação

Execute os testes para verificar se tudo está funcionando:

```bash
pytest tests/
```

## Solução de Problemas

### Erro: "PyQt5 não encontrado"
```bash
pip install PyQt5
```

### Erro: "Python não encontrado"
- Certifique-se de que Python 3.10+ está instalado
- Adicione Python ao PATH do sistema

### Erro de permissões (Linux/macOS)
```bash
chmod +x src/main.py
```

## Desenvolvimento

Para desenvolvimento, instale também as ferramentas de formatação:

```bash
pip install black pylint flake8 pytest-cov
```

## Próximos Passos

Após a instalação, consulte o [README.md](README.md) para instruções de uso.

