.PHONY: help setup-local start-local stop-local populate test clean

help:
	@echo "Comandos disponibles:"
	@echo "  make setup-local    - Configurar entorno local"
	@echo "  make start-local     - Iniciar todos los servicios localmente"
	@echo "  make stop-local      - Detener todos los servicios"
	@echo "  make populate        - Poblar base de datos con datos de prueba"
	@echo "  make sync            - Sincronizar productos a MongoDB"
	@echo "  make test            - Ejecutar tests"
	@echo "  make clean           - Limpiar contenedores y volúmenes"

setup-local:
	@echo "Configurando entorno local..."
	@cd microservices/auth-service && npm install
	@cd microservices/inventory-service && pip install -r requirements.txt
	@cd microservices/orders-service && pip install -r requirements.txt
	@cd scripts && pip install -r requirements.txt
	@echo "✓ Entorno configurado"

start-local:
	@echo "Iniciando servicios..."
	docker-compose -f docker-compose.local.yml up -d
	@echo "Esperando a que los servicios estén listos..."
	@sleep 10
	@echo "✓ Servicios iniciados"
	@echo "Auth Service: http://localhost:3000"
	@echo "Inventory Service: http://localhost:8000"
	@echo "Orders Service: http://localhost:8001"

stop-local:
	@echo "Deteniendo servicios..."
	docker-compose -f docker-compose.local.yml down
	@echo "✓ Servicios detenidos"

populate:
	@echo "Poblando base de datos..."
	@cd scripts && python populate_inventory.py
	@echo "✓ Base de datos poblada"

sync:
	@echo "Sincronizando productos a MongoDB..."
	@cd scripts && python sync_inventory.py
	@echo "✓ Sincronización completada"

test:
	@echo "Ejecutando tests..."
	@echo "TODO: Implementar tests"

clean:
	@echo "Limpiando contenedores y volúmenes..."
	docker-compose -f docker-compose.local.yml down -v
	@echo "✓ Limpieza completada"

