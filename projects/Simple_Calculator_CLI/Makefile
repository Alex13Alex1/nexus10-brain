.PHONY: help install run test docker-build docker-run docker-stop clean

help:           ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:        ## Установить зависимости
	pip install -r requirements.txt

run:            ## Запустить приложение
	python calculator.py

test:           ## Запустить тесты
	pytest

docker-build:   ## Собрать Docker образ
	docker build -t myapp:latest .

docker-run:     ## Запустить в Docker
	docker-compose up -d

docker-stop:    ## Остановить контейнеры
	docker-compose down

clean:          ## Очистить кэш
	find . -type d -name '__pycache__' -exec rm -r {} +