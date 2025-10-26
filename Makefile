.PHONY: help install run test quality format clean

help:
	@echo "BGP Monitor - Comandos disponíveis:"
	@echo ""
	@echo "  make install    - Instala dependências no venv"
	@echo "  make run        - Inicia o servidor FastAPI"
	@echo "  make quality    - Verifica qualidade (Black + Flake8)"
	@echo "  make format     - Formata código com Black"
	@echo "  make clean      - Remove arquivos temporários"
	@echo ""

install:
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Dependências instaladas! Execute 'source venv/bin/activate' para ativar o ambiente."

run:
	. venv/bin/activate && python3 run.py

quality:
	. venv/bin/activate && python3 setup.py --quality

format:
	. venv/bin/activate && python3 setup.py --format

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Arquivos temporários removidos!"
