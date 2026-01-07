graph TD  
    A[AppController] --> B[DataCollector]  
    B -->|Fetches Data| C[StrategyEngine]  
    C -->|Sends Trade Decisions| D[TradeLogger]  
    C -->|Sends Positions| E[RiskManager]  
    E -->|Checks Stop-Loss| C  
    A --> F[Configuration]  
    A --> G[Docker]  
    A --> H[Testing]  
    B -->|Uses| I[CCXT Library]  
    G -->|Containerizes| A