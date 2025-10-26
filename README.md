# BGP Monitor - Huawei NE8000

Sistema de monitoramento em tempo real para roteador **Huawei NE8000** utilizado como BGP Edge Router, onde chegam os links de operadoras.

## 🎯 Objetivo

Monitorar e visualizar métricas críticas do roteador NE8000:
- Status de sessões BGP
- Tráfego e utilização de links
- Qualidade de conexão
- Eventos e alertas em tempo real
- Histórico de mudanças de estado

## ⚠️ Modo de Operação

**Este sistema opera em modo READ-ONLY**:
- ✅ Apenas coleta informações do equipamento
- ✅ Executa somente comandos `display` (leitura)
- ❌ **NUNCA** altera configurações do NE8000
- ❌ **NUNCA** executa comandos de configuração

## 🛠️ Stack Tecnológica

### Backend
- **FastAPI** - Framework web moderno e rápido
- **Python 3.12+** - Linguagem principal
- **Paramiko** - Conexão SSH com o equipamento
- **APScheduler** - Agendamento de coletas periódicas
- **SQLite** - Banco de dados para histórico e eventos

### Frontend
- **HTML5 + CSS3** - Interface web
- **JavaScript puro** - Lógica do frontend (sem frameworks)
- **Chart.js** (ou similar) - Gráficos e visualizações

### Conexão com NE8000
- **SSH** - Conexão segura
- **CLI Parsing** - Análise de comandos `display`

## 📊 Métricas Monitoradas

### 1. BGP (Border Gateway Protocol)
- Status das sessões BGP (Established/Down/Idle)
- Uptime de cada peer
- Número de prefixos recebidos e anunciados
- ASN (Autonomous System Number) dos peers
- Descrição dos peers
- Detecção de flapping (mudanças frequentes de estado)
- Logs de eventos BGP

### 2. Links e Interfaces
- Status operacional (up/down)
- Utilização de banda (input/output em bps)
- Pacotes por segundo (pps)
- Erros (CRC, input errors, output errors)
- Descartes (input discards, output discards)
- Percentual de utilização da capacidade

### 3. Qualidade de Conexão
- Latência (RTT - Round Trip Time)
- Packet loss (perda de pacotes)
- Jitter (variação de latência)

### 4. Roteamento
- Total de rotas na tabela BGP
- Rotas por peer
- AS-PATH information
- Next-hop alcançável

### 5. Sistema (NE8000)
- Uso de CPU
- Memória utilizada
- Temperatura
- Status de hardware (ventiladores, fontes de alimentação)

## 🚀 Instalação

### Pré-requisitos
- Python 3.12 ou superior
- Acesso SSH ao Huawei NE8000
- Sistema operacional: Linux, macOS ou Windows (WSL)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd bgp-monitor
```

2. **Crie o ambiente virtual**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure o arquivo .env**
```bash
cp .env.example .env
nano .env  # ou use seu editor preferido
```

5. **Configure as variáveis de ambiente**

Edite o arquivo `.env` com suas configurações:

```env
# Configurações SSH do Huawei NE8000
SSH_HOST=192.168.1.1
SSH_PORT=22
SSH_USER=admin
SSH_PASSWORD=sua_senha_segura

# Configurações do Banco de Dados SQLite
DB_PATH=./data/bgp_monitor.db

# Configurações da API
API_HOST=0.0.0.0
API_PORT=8000

# Configurações de Coleta
COLLECTION_INTERVAL_SECONDS=30

# Configurações de Alertas
ALERT_BGP_DOWN_ENABLED=true
ALERT_INTERFACE_DOWN_ENABLED=true
ALERT_ERROR_THRESHOLD=100
```

6. **Execute o servidor**
```bash
python3 run.py
```

7. **Acesse o dashboard**
```
http://localhost:8000
```

## 📁 Estrutura do Projeto

```
bgp-monitor/
├── app/
│   ├── core/
│   │   ├── config.py          # Configurações (.env)
│   │   ├── database.py        # Gerenciamento SQLite
│   │   └── ssh_client.py      # Cliente SSH (READ-ONLY)
│   ├── models/
│   │   ├── bgp.py             # Dataclasses BGP
│   │   ├── interface.py       # Dataclasses interfaces
│   │   └── event.py           # Dataclasses eventos
│   ├── services/
│   │   ├── bgp_collector.py   # Coleta dados BGP
│   │   ├── interface_collector.py
│   │   ├── parser.py          # Parse saída CLI
│   │   └── alert_manager.py   # Sistema de alertas
│   ├── api/
│   │   ├── bgp.py             # Endpoints BGP
│   │   ├── interfaces.py      # Endpoints interfaces
│   │   └── events.py          # Endpoints eventos
│   └── scheduler/
│       └── jobs.py            # Jobs periódicos
├── frontend/
│   ├── index.html             # Dashboard principal
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           ├── main.js
│           ├── bgp.js
│           └── charts.js
├── data/                      # Banco de dados SQLite
├── logs/                      # Logs da aplicação
├── run.py                     # Entry point
├── setup.py                   # Script de qualidade
├── requirements.txt           # Dependências Python
├── .env.example               # Exemplo de configuração
├── pyproject.toml             # Config Black
├── .flake8                    # Config Flake8
├── CLAUDE.md                  # Instruções para Claude Code
└── README.md                  # Este arquivo
```

## 🔌 API REST

A aplicação expõe uma API REST completa:

### Endpoints Principais

#### BGP
- `GET /api/bgp/sessions` - Lista todas as sessões BGP
- `GET /api/bgp/sessions/{peer_ip}` - Detalhes de um peer específico
- `GET /api/bgp/stats` - Estatísticas gerais BGP

#### Interfaces
- `GET /api/interfaces` - Lista todas as interfaces
- `GET /api/interfaces/{name}` - Detalhes de uma interface
- `GET /api/interfaces/{name}/stats` - Estatísticas de tráfego

#### Eventos
- `GET /api/events` - Histórico de eventos
- `GET /api/events?severity=critical` - Filtrar por severidade
- `GET /api/events?type=bgp_down` - Filtrar por tipo

#### Documentação Interativa
- `GET /docs` - Swagger UI (documentação interativa)
- `GET /redoc` - ReDoc (documentação alternativa)

## 🎨 Dashboard

O dashboard web oferece:

1. **Visão Geral**
   - Mapa visual de sessões BGP (verde/vermelho)
   - Indicadores de status (up/down)
   - Contadores em tempo real

2. **Gráficos de Tráfego**
   - Utilização de banda por interface
   - Pacotes por segundo
   - Histórico temporal

3. **Timeline de Eventos**
   - Eventos recentes
   - Mudanças de estado BGP
   - Alertas ativos

4. **Tabela de Prefixos**
   - Prefixos recebidos por peer
   - AS-PATH information
   - Next-hop details

5. **Alertas Visuais**
   - Notificações de problemas
   - Severidade codificada por cor
   - Histórico de alertas

## 🔐 Segurança

### Autenticação SSH
- Credenciais armazenadas em `.env` (não versionado)
- Suporte a autenticação por senha ou chave SSH
- Timeout de conexão configurável

### Comandos Permitidos
Apenas comandos de leitura são executados:
```bash
display bgp peer
display bgp routing-table peer <IP>
display interface
display interface statistics
display cpu-usage
display memory-usage
```

### Validação
- Whitelist de comandos implementada
- Validação antes da execução
- Log de todos os comandos executados

## 📈 Monitoramento e Logs

### Logs da Aplicação
- Localização: `./logs/`
- Rotação automática
- Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Banco de Dados
- SQLite para persistência
- Histórico de eventos
- Métricas temporais para gráficos
- Backup automático recomendado

### Análise de Dados
```bash
# Acessar banco SQLite diretamente
sqlite3 ./data/bgp_monitor.db

# Exemplos de queries
sqlite> .tables
sqlite> SELECT * FROM bgp_sessions WHERE status = 'Down';
sqlite> SELECT * FROM events ORDER BY timestamp DESC LIMIT 10;
```

## 🧪 Desenvolvimento

### Qualidade de Código

Este projeto utiliza **Black** e **Flake8** para manter qualidade:

```bash
# Verificar qualidade (Black + Flake8)
python3 setup.py --quality

# Formatar código automaticamente
python3 setup.py --format
```

### Padrões
- **Black**: Line length 100 caracteres
- **Flake8**: Max line length 120 caracteres
- **Type Hints**: Obrigatórios
- **Docstrings**: Obrigatórias em funções públicas

### Contribuindo

1. Sempre execute `python3 setup.py --quality` antes de commit
2. Siga as instruções em `CLAUDE.md`
3. Nunca comite valores sensíveis (use `.env`)
4. Mantenha o código READ-ONLY em relação ao NE8000

## 🐛 Troubleshooting

### Erro de Conexão SSH
```bash
# Verifique conectividade
ssh usuario@ip-do-ne8000

# Teste comando manualmente
display bgp peer
```

### Banco de Dados Corrompido
```bash
# Backup do banco
cp data/bgp_monitor.db data/bgp_monitor.db.backup

# Verificar integridade
sqlite3 data/bgp_monitor.db "PRAGMA integrity_check;"
```

### Porta em Uso
```bash
# Verificar processos na porta 8000
lsof -i :8000

# Matar processo específico
kill -9 <PID>
```

## 📝 Comandos Úteis

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar servidor
python3 run.py

# Verificar qualidade
python3 setup.py --quality

# Formatar código
python3 setup.py --format

# Atualizar dependências
pip freeze > requirements.txt

# Acessar banco de dados
sqlite3 data/bgp_monitor.db
```

## 📄 Licença

[Definir licença do projeto]

## 🤝 Contato

[Informações de contato]

---

**⚠️ LEMBRETE IMPORTANTE**: Este sistema é **READ-ONLY**. Nunca execute comandos que possam alterar a configuração do equipamento Huawei NE8000.
