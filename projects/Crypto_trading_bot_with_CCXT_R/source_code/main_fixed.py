# Crypto Trading Bot with RSI + Bollinger Bands Strategy
# AI Factory v0.7 Nexus - Auto-generated

import ccxt
import pandas as pd
import numpy as np
import csv
import os
import logging
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


# ═══════════════════════════════════════════════════════════════
#                    📊 CONFIGURATION
# ═══════════════════════════════════════════════════════════════

@dataclass
class TradingConfig:
    """Trading bot configuration."""
    exchange_id: str = "binance"
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    
    # RSI Settings
    rsi_period: int = 14
    rsi_oversold: float = 30.0
    rsi_overbought: float = 70.0
    
    # Bollinger Bands Settings
    bb_period: int = 20
    bb_std: float = 2.0
    
    # Risk Management
    stop_loss_pct: float = 2.0  # 2% stop-loss
    take_profit_pct: float = 4.0  # 4% take-profit
    position_size_pct: float = 10.0  # 10% of balance per trade
    
    # Operational
    paper_trading: bool = True
    check_interval_seconds: int = 60
    log_file: str = "trades.csv"
    
    # API Keys (set via environment variables)
    api_key: str = ""
    api_secret: str = ""


# ═══════════════════════════════════════════════════════════════
#                    📈 TECHNICAL INDICATORS
# ═══════════════════════════════════════════════════════════════

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: Series of closing prices
        period: RSI period (default: 14)
    
    Returns:
        Series with RSI values
    """
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(
    prices: pd.Series, 
    period: int = 20, 
    std_dev: float = 2.0
) -> tuple:
    """
    Calculate Bollinger Bands.
    
    Args:
        prices: Series of closing prices
        period: Moving average period (default: 20)
        std_dev: Number of standard deviations (default: 2)
    
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return prices.rolling(window=period).mean()


# ═══════════════════════════════════════════════════════════════
#                    📝 TRADE LOGGER
# ═══════════════════════════════════════════════════════════════

class TradeLogger:
    """Logs all trades to CSV file."""
    
    def __init__(self, filename: str = "trades.csv"):
        self.filename = filename
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create CSV file with headers if not exists."""
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'symbol', 'side', 'price', 'amount',
                    'rsi', 'bb_position', 'stop_loss', 'take_profit',
                    'pnl', 'status', 'notes'
                ])
    
    def log_trade(
        self,
        symbol: str,
        side: str,
        price: float,
        amount: float,
        rsi: float,
        bb_position: str,
        stop_loss: float,
        take_profit: float,
        pnl: float = 0.0,
        status: str = "OPEN",
        notes: str = ""
    ):
        """Log a trade to CSV."""
        with open(self.filename, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                symbol,
                side,
                f"{price:.8f}",
                f"{amount:.8f}",
                f"{rsi:.2f}",
                bb_position,
                f"{stop_loss:.8f}",
                f"{take_profit:.8f}",
                f"{pnl:.2f}",
                status,
                notes
            ])
        
        logging.info(f"Trade logged: {side} {amount} {symbol} @ {price}")


# ═══════════════════════════════════════════════════════════════
#                    🤖 TRADING BOT
# ═══════════════════════════════════════════════════════════════

class CryptoTradingBot:
    """
    Autonomous Crypto Trading Bot with RSI + Bollinger Bands strategy.
    
    Features:
    - RSI oversold/overbought detection
    - Bollinger Bands breakout signals
    - Stop-loss and take-profit protection
    - CSV trade logging
    - Paper trading mode
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.logger = TradeLogger(config.log_file)
        self.exchange: Optional[ccxt.Exchange] = None
        self.position: Optional[Dict[str, Any]] = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('bot.log', encoding='utf-8')
            ]
        )
        
        self._init_exchange()
    
    def _init_exchange(self):
        """Initialize exchange connection."""
        try:
            exchange_class = getattr(ccxt, self.config.exchange_id)
            
            exchange_config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            # Add API keys if not paper trading
            if not self.config.paper_trading:
                api_key = self.config.api_key or os.getenv('EXCHANGE_API_KEY', '')
                api_secret = self.config.api_secret or os.getenv('EXCHANGE_API_SECRET', '')
                
                if api_key and api_secret:
                    exchange_config['apiKey'] = api_key
                    exchange_config['secret'] = api_secret
            
            self.exchange = exchange_class(exchange_config)
            
            # Test connection
            self.exchange.load_markets()
            logging.info(f"✅ Connected to {self.config.exchange_id}")
            
        except Exception as e:
            logging.error(f"❌ Exchange connection failed: {e}")
            raise
    
    def fetch_ohlcv(self, limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data and return as DataFrame."""
        try:
            ohlcv = self.exchange.fetch_ohlcv(
                self.config.symbol,
                self.config.timeframe,
                limit=limit
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            return df
            
        except Exception as e:
            logging.error(f"❌ Failed to fetch OHLCV: {e}")
            return pd.DataFrame()
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        df = df.copy()
        
        # RSI
        df['rsi'] = calculate_rsi(df['close'], self.config.rsi_period)
        
        # Bollinger Bands
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = calculate_bollinger_bands(
            df['close'],
            self.config.bb_period,
            self.config.bb_std
        )
        
        # SMA for trend
        df['sma_50'] = calculate_sma(df['close'], 50)
        df['sma_200'] = calculate_sma(df['close'], 200)
        
        return df
    
    def generate_signal(self, df: pd.DataFrame) -> str:
        """
        Generate trading signal based on RSI + Bollinger Bands.
        
        Returns:
            'BUY', 'SELL', or 'HOLD'
        """
        if len(df) < 2:
            return 'HOLD'
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        rsi = latest['rsi']
        close = latest['close']
        bb_lower = latest['bb_lower']
        bb_upper = latest['bb_upper']
        
        # BUY Signal: RSI oversold AND price touches lower BB
        buy_rsi = rsi < self.config.rsi_oversold
        buy_bb = close <= bb_lower
        
        # SELL Signal: RSI overbought AND price touches upper BB
        sell_rsi = rsi > self.config.rsi_overbought
        sell_bb = close >= bb_upper
        
        if buy_rsi and buy_bb:
            logging.info(f"📈 BUY Signal: RSI={rsi:.2f}, Close={close:.2f}, BB_Lower={bb_lower:.2f}")
            return 'BUY'
        
        if sell_rsi and sell_bb:
            logging.info(f"📉 SELL Signal: RSI={rsi:.2f}, Close={close:.2f}, BB_Upper={bb_upper:.2f}")
            return 'SELL'
        
        return 'HOLD'
    
    def calculate_position_size(self, price: float) -> float:
        """Calculate position size based on config."""
        if self.config.paper_trading:
            # Simulate 10000 USDT balance for paper trading
            balance = 10000.0
        else:
            try:
                balance_info = self.exchange.fetch_balance()
                balance = balance_info['USDT']['free']
            except:
                balance = 0.0
        
        position_value = balance * (self.config.position_size_pct / 100)
        amount = position_value / price
        
        return amount
    
    def execute_trade(self, signal: str, df: pd.DataFrame):
        """Execute trade based on signal."""
        if signal == 'HOLD':
            return
        
        latest = df.iloc[-1]
        price = latest['close']
        rsi = latest['rsi']
        
        # Determine BB position
        if price <= latest['bb_lower']:
            bb_position = "BELOW_LOWER"
        elif price >= latest['bb_upper']:
            bb_position = "ABOVE_UPPER"
        else:
            bb_position = "MIDDLE"
        
        amount = self.calculate_position_size(price)
        
        # Calculate stop-loss and take-profit
        if signal == 'BUY':
            stop_loss = price * (1 - self.config.stop_loss_pct / 100)
            take_profit = price * (1 + self.config.take_profit_pct / 100)
        else:  # SELL
            stop_loss = price * (1 + self.config.stop_loss_pct / 100)
            take_profit = price * (1 - self.config.take_profit_pct / 100)
        
        # Execute order
        if self.config.paper_trading:
            logging.info(f"📝 [PAPER] {signal} {amount:.6f} {self.config.symbol} @ {price:.2f}")
            logging.info(f"   Stop-Loss: {stop_loss:.2f}, Take-Profit: {take_profit:.2f}")
        else:
            try:
                if signal == 'BUY':
                    order = self.exchange.create_market_buy_order(
                        self.config.symbol,
                        amount
                    )
                else:
                    order = self.exchange.create_market_sell_order(
                        self.config.symbol,
                        amount
                    )
                logging.info(f"✅ Order executed: {order}")
            except Exception as e:
                logging.error(f"❌ Order failed: {e}")
                return
        
        # Log trade
        self.logger.log_trade(
            symbol=self.config.symbol,
            side=signal,
            price=price,
            amount=amount,
            rsi=rsi,
            bb_position=bb_position,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status="OPEN" if not self.config.paper_trading else "PAPER",
            notes=f"RSI={rsi:.2f}, BB={bb_position}"
        )
        
        # Store position
        self.position = {
            'side': signal,
            'entry_price': price,
            'amount': amount,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
    
    def check_stop_loss_take_profit(self, current_price: float):
        """Check if stop-loss or take-profit is triggered."""
        if not self.position:
            return
        
        entry = self.position['entry_price']
        sl = self.position['stop_loss']
        tp = self.position['take_profit']
        side = self.position['side']
        
        triggered = None
        pnl = 0.0
        
        if side == 'BUY':
            if current_price <= sl:
                triggered = 'STOP_LOSS'
                pnl = (current_price - entry) / entry * 100
            elif current_price >= tp:
                triggered = 'TAKE_PROFIT'
                pnl = (current_price - entry) / entry * 100
        else:  # SELL
            if current_price >= sl:
                triggered = 'STOP_LOSS'
                pnl = (entry - current_price) / entry * 100
            elif current_price <= tp:
                triggered = 'TAKE_PROFIT'
                pnl = (entry - current_price) / entry * 100
        
        if triggered:
            logging.info(f"{'🛑' if triggered == 'STOP_LOSS' else '🎯'} {triggered} triggered! PnL: {pnl:.2f}%")
            
            self.logger.log_trade(
                symbol=self.config.symbol,
                side='CLOSE_' + self.position['side'],
                price=current_price,
                amount=self.position['amount'],
                rsi=0,
                bb_position="N/A",
                stop_loss=sl,
                take_profit=tp,
                pnl=pnl,
                status=triggered,
                notes=f"Entry: {entry:.2f}"
            )
            
            self.position = None
    
    def run_once(self):
        """Run one iteration of the bot."""
        logging.info(f"🔄 Checking {self.config.symbol}...")
        
        # Fetch data
        df = self.fetch_ohlcv()
        if df.empty:
            logging.warning("No data received")
            return
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        latest = df.iloc[-1]
        logging.info(
            f"📊 Price: {latest['close']:.2f} | "
            f"RSI: {latest['rsi']:.2f} | "
            f"BB: [{latest['bb_lower']:.2f} - {latest['bb_upper']:.2f}]"
        )
        
        # Check stop-loss/take-profit for existing position
        self.check_stop_loss_take_profit(latest['close'])
        
        # Generate and execute signal (only if no position)
        if not self.position:
            signal = self.generate_signal(df)
            self.execute_trade(signal, df)
    
    def run(self):
        """Run the bot continuously."""
        self.running = True
        logging.info(f"""
╔══════════════════════════════════════════════════════════════════╗
║            🤖 CRYPTO TRADING BOT STARTED                         ║
╠══════════════════════════════════════════════════════════════════╣
║  Exchange: {self.config.exchange_id:<48} ║
║  Symbol: {self.config.symbol:<50} ║
║  Strategy: RSI + Bollinger Bands{' '*27}║
║  Paper Trading: {str(self.config.paper_trading):<43} ║
║  Stop-Loss: {self.config.stop_loss_pct}%{' '*46}║
║  Take-Profit: {self.config.take_profit_pct}%{' '*44}║
╚══════════════════════════════════════════════════════════════════╝
        """)
        
        while self.running:
            try:
                self.run_once()
                time.sleep(self.config.check_interval_seconds)
            except KeyboardInterrupt:
                logging.info("⏹️ Bot stopped by user")
                self.running = False
            except Exception as e:
                logging.error(f"❌ Error: {e}")
                time.sleep(10)
    
    def stop(self):
        """Stop the bot."""
        self.running = False
        logging.info("🛑 Bot stopping...")


# ═══════════════════════════════════════════════════════════════
#                    🚀 MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Default configuration for demo
    config = TradingConfig(
        exchange_id="binance",
        symbol="BTC/USDT",
        timeframe="1h",
        paper_trading=True,  # ВАЖНО: Используем paper trading для безопасности!
        stop_loss_pct=2.0,
        take_profit_pct=4.0,
        check_interval_seconds=60
    )
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║         🤖 CRYPTO TRADING BOT - RSI + Bollinger Bands            ║
║                  AI Factory v0.7 Nexus                           ║
╠══════════════════════════════════════════════════════════════════╣
║  ⚠️  PAPER TRADING MODE - No real trades will be executed        ║
║  📊 Strategy: RSI Oversold/Overbought + BB Breakout              ║
║  🛡️  Risk Management: Stop-Loss + Take-Profit                    ║
║  📝 Trade logging: trades.csv                                    ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Create and run bot
    bot = CryptoTradingBot(config)
    
    try:
        # Run single iteration for demo
        bot.run_once()
        
        print("\n✅ Demo complete! Check trades.csv for logged trades.")
        print("\nTo run continuously, call: bot.run()")
        
    except Exception as e:
        print(f"❌ Error: {e}")
