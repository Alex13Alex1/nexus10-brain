```
install:
	pip install -r requirements.txt

test:
	pytest

run:
	python data_collector.py

docker-build:
	docker build -t crypto_trading_bot .

docker-run:
	docker run --rm -d --name crypto_trading_bot_container crypto_trading_bot

docker-stop:
	docker stop crypto_trading_bot_container

clean:
	rm -rf __pycache__ .pytest_cache
```