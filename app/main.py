"""
Aplicação principal FastAPI para BGP Monitor.
"""

import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.core.config import settings
from app.api import bgp, interfaces, events
from app.scheduler.jobs import setup_scheduler, start_scheduler, stop_scheduler

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/bgp_monitor.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Criar instância FastAPI
app = FastAPI(
    title="BGP Monitor - Huawei NE8000",
    description="Sistema de monitoramento BGP para Huawei NE8000",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Montar diretório de arquivos estáticos
static_path = Path(__file__).parent.parent / "frontend" / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
    logger.info(f"Arquivos estáticos montados em: {static_path}")
else:
    logger.warning(f"Diretório de arquivos estáticos não encontrado: {static_path}")

# Registrar routers da API
app.include_router(bgp.router)
app.include_router(interfaces.router)
app.include_router(events.router)


@app.on_event("startup")
async def startup_event():
    """Evento executado ao iniciar a aplicação."""
    logger.info("Iniciando BGP Monitor...")
    logger.info(f"Configurações carregadas: SSH Host={settings.SSH_HOST}")
    logger.info(f"Banco de dados: {settings.DB_PATH}")

    # Configurar e iniciar scheduler
    setup_scheduler()
    start_scheduler()
    logger.info("Sistema de coleta automática iniciado")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado ao desligar a aplicação."""
    logger.info("Encerrando BGP Monitor...")

    # Parar scheduler
    stop_scheduler()
    logger.info("Sistema de coleta automática encerrado")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Rota raiz - retorna página HTML do dashboard."""
    html_file = Path(__file__).parent.parent / "frontend" / "index.html"

    if html_file.exists():
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()

    return """
    <html>
        <head>
            <title>BGP Monitor</title>
        </head>
        <body>
            <h1>BGP Monitor - Huawei NE8000</h1>
            <p>Dashboard em construção...</p>
            <p><a href="/docs">Documentação da API</a></p>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy", "service": "bgp-monitor", "version": "1.0.0"}
