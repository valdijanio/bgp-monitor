# Instruções para Claude Code - BGP Monitor NE8000

## 📋 Visão Geral do Projeto

Sistema de monitoramento para roteador **Huawei NE8000** (BGP Edge Router).
- **Objetivo**: Monitorar sessões BGP, interfaces, tráfego e gerar alertas
- **Modo de Operação**: **READ-ONLY** - NUNCA alterar configurações do equipamento
- **Stack**: FastAPI + SQLite + SSH/CLI Parsing + HTML/CSS/JS puro

---

## 🔧 Configuração das Ferramentas

### Black
- Configurado em `pyproject.toml`
- Line length: **100 caracteres**
- Target: Python 3.12+

### Flake8
- Configurado em `.flake8`
- Max line length: **120 caracteres**
- Focado em erros críticos
- Ignora problemas cosméticos

---

## ⚠️ REGRAS CRÍTICAS - HUAWEI NE8000

### 🚨 EQUIPAMENTO - READ-ONLY (CRÍTICO!)

1. **NUNCA** alterar configurações do equipamento NE8000
2. **APENAS** comandos de leitura são permitidos (família `display`)
3. **PROIBIDO** comandos: `config`, `set`, `delete`, `save`, `reset`, etc.
4. **SEMPRE** validar comandos contra whitelist antes de executar
5. **OBRIGATÓRIO** logar todos os comandos executados no equipamento

#### Comandos Permitidos (Whitelist)
```bash
display bgp peer
display bgp routing-table peer <IP>
display interface
display interface <name>
display interface statistics
display cpu-usage
display memory-usage
display version
display current-configuration interface <name>  # Apenas leitura de config
```

#### Comandos PROIBIDOS (Exemplos)
```bash
❌ system-view
❌ interface <name>
❌ undo <qualquer coisa>
❌ shutdown
❌ reset
❌ save
❌ commit
❌ quit (dentro de modo config)
```

---

## 🗄️ Banco de Dados - SQLite

### Regras de Uso
1. **NUNCA** usar SQLAlchemy ou ORMs - apenas SQL puro
2. **SEMPRE** usar `with db.get_connection()` para transações
3. **NUNCA** chamar métodos `db.execute_*` dentro de `with db.get_connection()` - use o cursor!
4. **SEMPRE** propagar exceções em métodos com transação
5. **EVITAR** transações muito longas (podem causar locks)
6. **PERMITIDO** usar `sqlite3` CLI para testes e análises do banco

### Exemplo de Uso Correto
```python
# ✅ CORRETO
with db.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bgp_sessions (...) VALUES (...)")
    cursor.execute("INSERT INTO events (...) VALUES (...)")
    conn.commit()  # Explícito

# ❌ ERRADO
with db.get_connection() as conn:
    db.execute_query(...)  # NÃO fazer isso!
```

### Ferramentas de Teste/Análise
```bash
# Permitido para debug e análise
sqlite3 /caminho/do/banco.db

# Exemplos de queries úteis
sqlite> .tables
sqlite> .schema bgp_sessions
sqlite> SELECT * FROM bgp_sessions WHERE status = 'Down';
```

---

## 📝 Qualidade de Código

### Regras Obrigatórias
1. **SEMPRE** executar `python3 setup.py --quality` antes de finalizar qualquer tarefa
2. **NUNCA** ignorar erros do Flake8 sem justificativa
3. **SEMPRE** manter código formatado com Black
4. **OBRIGATÓRIO** o código passar em ambas verificações (Black + Flake8)
5. **NUNCA** fazer código de fallback/provisório sem autorização expressa

### Comandos
```bash
# Verificar qualidade (Black + Flake8)
python3 setup.py --quality

# Formatar código automaticamente
python3 setup.py --format

# Ou diretamente
black . --config pyproject.toml
flake8 . --config .flake8
```

---

## 🚀 Ambiente de Desenvolvimento

### Execução do Projeto
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar servidor
python3 run.py
```

### Configuração (.env)
- **PROIBIDO** valores padrão na classe Settings
- **OBRIGATÓRIO** usar arquivo `.env` para todas as configurações
- **NUNCA** commitar arquivo `.env` (apenas `.env.example`)

---

## 🔒 Regras Gerais de Segurança

1. **PROIBIDO** alterar pasta `venv/` (não commitar)
2. **PROIBIDO** criar soluções provisórias ou temporárias
3. **NUNCA** usar valores hardcoded - usar `.env` ou banco
4. **SEMPRE** executar dentro do ambiente virtual
5. **OBRIGATÓRIO** matar servidor após testes (liberar porta)
6. **SEMPRE** atualizar `requirements.txt` ao instalar novos pacotes
7. **SEMPRE** responder em português

---

## 📊 Arquitetura de Dados

### Models (Dataclasses)
- Usar **dataclasses** Python para tipagem
- Não usar ORMs (sem SQLAlchemy models)
- Type hints obrigatórios

### Coleta de Dados
- Intervalo configurável via `.env` (ex: 30 segundos)
- APScheduler para jobs periódicos
- Detecção de mudanças de estado (flapping)
- Gravação de eventos no banco

### API REST
- FastAPI com documentação automática (Swagger)
- Endpoints RESTful
- Validação com Pydantic
- CORS habilitado para frontend

---

## 📈 Métricas Monitoradas

### BGP
- Status das sessões (Established/Down/Idle)
- Uptime de cada peer
- Número de prefixos recebidos/anunciados
- ASN e descrição dos peers
- Detecção de flapping

### Interfaces
- Status operacional (up/down)
- Utilização de banda (input/output bps)
- Pacotes por segundo
- Erros e descartes

### Eventos
- Log de mudanças de estado
- Alertas configuráveis
- Histórico temporal

---

## 🎯 Prioridades de Implementação

1. **Status BGP Sessions** (alta prioridade)
2. **Tráfego de Links** (alta prioridade)
3. **Histórico/Logs** (média prioridade)
4. **Alertas/Notificações** (média prioridade)

---

## ⚠️ Avisos Importantes

### Transações no Banco
- **SEMPRE** usar context manager para atomicidade
- **NUNCA** misturar métodos diretos com context manager
- **CUIDADO** com deadlocks - manter ordem consistente

### SSH no NE8000
- **TIMEOUT** obrigatório em todas as conexões
- **LOG** de todos os comandos executados
- **VALIDAÇÃO** contra whitelist antes de executar
- **RECONEXÃO** automática em caso de falha

### Frontend
- HTML/CSS/JS puro (sem frameworks)
- Polling ou WebSocket para updates
- Gráficos com Chart.js (ou similar leve)
- Responsivo e mobile-friendly

---

## 📚 Referências

- Documentação Huawei NE8000: VRP Command Reference
- FastAPI: https://fastapi.tiangolo.com/
- Paramiko (SSH): https://www.paramiko.org/
- SQLite: https://www.sqlite.org/docs.html
