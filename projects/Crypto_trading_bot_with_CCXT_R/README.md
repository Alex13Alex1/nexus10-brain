```markdown
# Crypto Trading Bot

![Python](https://img.shields.io/badge/python-3.9-blue.svg)
![Docker](https://img.shields.io/badge/docker-enabled-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Описание проекта

Crypto Trading Bot — это автоматизированный торговый бот для криптовалют, использующий библиотеку CCXT для взаимодействия с различными криптобиржами. Бот реализует торговые стратегии на основе индикаторов RSI и Bollinger Bands, ведет логирование сделок в формате CSV и обеспечивает защиту от убытков с помощью механизма stop-loss. Проект также включает Docker-контейнер для работы 24/7.

## Установка

Для установки необходимых зависимостей выполните следующие шаги:

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/yourusername/crypto-trading-bot.git
   cd crypto-trading-bot
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Использование

1. Настройте файл конфигурации `config.py` с вашими API ключами и параметрами торговли.
2. Запустите бота:
   ```bash
   python trading_bot.py
   ```

### Пример использования

```python
from data_collector import DataCollector

# Инициализация сборщика данных
collector = DataCollector(exchange_name='binance', symbol='BTC/USDT')
ohlcv_data = collector.fetch_ohlcv()
print(ohlcv_data)
```

## Docker инструкции

Для запуска бота в Docker выполните следующие шаги:

1. Соберите Docker-образ:
   ```bash
   docker build -t crypto-trading-bot .
   ```

2. Запустите контейнер:
   ```bash
   docker run -d --name trading-bot crypto-trading-bot
   ```

3. Для остановки контейнера:
   ```bash
   docker stop trading-bot
   ```

4. Для удаления контейнера:
   ```bash
   docker rm trading-bot
   ```

## API документация

Бот использует библиотеку CCXT для взаимодействия с API криптобирж. Подробную документацию по API можно найти [здесь](https://docs.ccxt.com/en/latest/index.html).

### Структура модулей

- **DataCollector**: Сбор данных с криптобирж.
- **StrategyEngine**: Реализация торговых стратегий (RSI и Bollinger Bands).
- **TradeLogger**: Логирование сделок в CSV.
- **RiskManager**: Защита от убытков (stop-loss).
- **AppController**: Главный контроллер приложения.

### Потоки данных

1. **Сбор данных**: DataCollector получает данные с биржи через CCXT и передает их в StrategyEngine.
2. **Анализ стратегии**: StrategyEngine анализирует данные и принимает торговые решения.
3. **Логирование**: TradeLogger записывает результаты сделок в CSV файл.
4. **Управление рисками**: RiskManager проверяет условия stop-loss.

### Обработка ошибок

- Реализована обработка ошибок API, валидация входных данных и логирование ошибок.

## Заключение

Crypto Trading Bot — это мощный инструмент для автоматизации торговли криптовалютами. С помощью этого проекта вы можете легко интегрироваться с различными биржами и использовать проверенные торговые стратегии для достижения успеха на рынке.
```