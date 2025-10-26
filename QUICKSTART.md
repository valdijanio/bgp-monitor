# 🚀 Quick Start - BGP Monitor

## 1. Configurar o Ambiente

### Ativar o ambiente virtual (já criado)
```bash
source venv/bin/activate
```

## 2. Configurar o .env

Edite o arquivo `.env` com as credenciais reais do seu NE8000:

```bash
nano .env
```

**Configurações necessárias:**
```env
# SSH do Huawei NE8000
SSH_HOST=192.168.1.1          # IP do seu NE8000
SSH_PORT=22
SSH_USER=admin                 # Seu usuário SSH
SSH_PASSWORD=sua_senha         # Sua senha SSH

# Banco de dados
DB_PATH=./data/bgp_monitor.db

# API
API_HOST=0.0.0.0
API_PORT=8000

# Coleta (intervalo em segundos)
COLLECTION_INTERVAL_SECONDS=30

# Alertas
ALERT_BGP_DOWN_ENABLED=true
ALERT_INTERFACE_DOWN_ENABLED=true
ALERT_ERROR_THRESHOLD=100
```

## 3. Iniciar a API

### Opção 1: Usando o script run.py
```bash
source venv/bin/activate
python3 run.py
```

### Opção 2: Usando Makefile
```bash
make run
```

### Opção 3: Usando uvicorn diretamente
```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 4. Acessar a Aplicação

### Dashboard
```
http://localhost:8000
```

### Documentação da API (Swagger)
```
http://localhost:8000/docs
```

### Documentação Alternativa (ReDoc)
```
http://localhost:8000/redoc
```

### Health Check
```
http://localhost:8000/health
```

## 5. Testar Conexão SSH

Você pode testar a conexão SSH com o NE8000 usando Python:

```python
from app.core.ssh_client import ssh_client

# Tentar conectar
try:
    with ssh_client as client:
        output = client.execute_command("display version")
        print(output)
    print("✅ Conexão SSH funcionando!")
except Exception as e:
    print(f"❌ Erro na conexão SSH: {e}")
```

## 6. Verificar o Banco de Dados

```bash
# Acessar o SQLite
sqlite3 ./data/bgp_monitor.db

# Ver tabelas
sqlite> .tables

# Ver schema de uma tabela
sqlite> .schema bgp_sessions

# Sair
sqlite> .quit
```

## 7. Comandos Úteis

### Verificar qualidade do código
```bash
make quality
# ou
python3 setup.py --quality
```

### Formatar código
```bash
make format
# ou
python3 setup.py --format
```

### Limpar arquivos temporários
```bash
make clean
```

### Ver ajuda do Makefile
```bash
make help
```

## 8. Parar o Servidor

Pressione `Ctrl + C` no terminal onde o servidor está rodando.

## 9. Logs

Os logs da aplicação ficam em:
```
logs/bgp_monitor.log
```

Para acompanhar em tempo real:
```bash
tail -f logs/bgp_monitor.log
```

## ⚠️ Troubleshooting

### Erro: "No module named 'app'"
**Solução:** Certifique-se de estar no diretório raiz do projeto e com o venv ativado.

### Erro: Porta 8000 em uso
**Solução:**
```bash
# Encontrar processo
lsof -i :8000

# Matar processo
kill -9 <PID>
```

### Erro: Não conecta no NE8000
**Solução:**
1. Verifique se o `.env` está configurado corretamente
2. Teste a conexão SSH manualmente: `ssh usuario@ip-do-ne8000`
3. Verifique firewall/rede

### Erro: Banco de dados não inicializa
**Solução:**
```bash
# Recriar banco
rm -f data/bgp_monitor.db
python3 run.py  # Vai recriar automaticamente
```

## 📚 Próximos Passos

Agora que a aplicação está rodando, você precisa implementar:

1. **Services** - Parsers e collectors para coletar dados do NE8000
2. **API Endpoints** - Endpoints REST para expor os dados
3. **Scheduler** - Jobs periódicos para coleta automática
4. **Frontend** - Integrar o frontend com a API

Consulte o `README.md` para mais detalhes!
