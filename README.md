# Quant IBKR – SMA Crossover Strategy

Proyecto cuantitativo serio para **backtesting** y **paper trading** de una estrategia clásica de cruce de medias móviles (SMA 50 / SMA 200) usando la API oficial de **Interactive Brokers**.

---

## Objetivo del proyecto

Este repositorio nace con el siguiente propósito:

1. Aprender a construir modelos cuantitativos de forma estructurada.
2. Implementar una estrategia simple pero robusta (SMA Crossover).
3. Realizar un **backtest** limpio con métricas estándar (Sharpe, Max Drawdown, etc.).
4. Ejecutar la misma estrategia en **paper trading** real de Interactive Brokers.
5. Tener una base de código limpia, modular y profesional que se pueda extender.

---

## Estructura del repositorio

```
quant-ibkr-sma-crossover/
├── config/
│   └── config.yaml              # Parámetros de estrategia, backtest e IBKR
├── src/
│   ├── strategy.py              # Lógica de la estrategia SMA
│   ├── backtest.py              # Motor de backtesting
│   ├── data.py                  # Descarga de datos (yfinance)
│   ├── paper_trader.py          # Cliente de paper trading IBKR
│   └── utils.py                 # Logging y utilidades
├── scripts/
│   ├── run_backtest.py          # Ejecutar backtest
│   └── run_paper_trading.py     # Ejecutar paper trading
├── tests/
│   └── test_strategy.py         # Tests unitarios básicos
├── data/                        # Resultados (equity curves, etc.)
├── notebooks/                   # Análisis exploratorio (opcional)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Requisitos previos

### 1. Python
- Python 3.10 o superior recomendado.

### 2. Dependencias
```bash
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 3. Interactive Brokers API
La librería oficial `ibapi` **no siempre está disponible** vía PyPI de forma estable.  
La forma recomendada es:

1. Descargar el API de IB desde:  
   https://interactivebrokers.github.io/
2. Extraer el archivo.
3. Ir a la carpeta `source/pythonclient` y ejecutar:
   ```bash
   python setup.py install
   ```

### 4. Trader Workstation (TWS) o IB Gateway
- Tener TWS o IB Gateway instalado.
- Iniciar sesión con una **cuenta Paper Trading**.
- En TWS → `Edit` → `Global Configuration` → `API` → `Settings`:
  - Activar **Enable ActiveX and Socket Clients**
  - Puerto por defecto para paper: **7497**
  - Desmarcar **Read-Only API** si quieres enviar órdenes.

---

## Cómo usar

### 1. Configuración
Edita `config/config.yaml` según tus preferencias:

```yaml
strategy:
  symbol: "AAPL"
  short_window: 50
  long_window: 200
  quantity: 100

backtest:
  start_date: "2020-01-01"
  initial_capital: 100000
  commission: 0.001
  slippage: 0.0005

ibkr:
  host: "127.0.0.1"
  port: 7497          # 7497 = paper | 7496 = live
  client_id: 1
```

### 2. Ejecutar Backtest
```bash
python scripts/run_backtest.py
```

Salida esperada:
- Métricas de rendimiento (Return, Sharpe, Max Drawdown, Win Rate…)
- Gráfico de la equity curve
- Archivo `data/equity_curve.csv`

### 3. Ejecutar Paper Trading
1. Abre TWS / IB Gateway con tu cuenta **Paper**.
2. Ejecuta:
   ```bash
   python scripts/run_paper_trading.py
   ```
3. El script:
   - Se conecta a IBKR
   - Descarga datos históricos
   - Calcula la señal actual
   - Envía una orden de mercado si hay cruce

> **Recomendación**: programa este script para que se ejecute una vez al día después del cierre de mercado (cron, Task Scheduler, etc.).

---

## Métricas que calcula el backtester

| Métrica              | Descripción                              |
|----------------------|------------------------------------------|
| Total Return         | Retorno total del periodo                |
| Annualized Return    | Retorno anualizado                       |
| Volatility           | Volatilidad anualizada                   |
| Sharpe Ratio         | Ratio de Sharpe (sin risk-free rate)     |
| Max Drawdown         | Peor caída desde un máximo               |
| Number of Trades     | Cantidad de operaciones                  |
| Win Rate             | % de operaciones ganadoras               |

---

## Gestión de riesgo incluida

- Position sizing configurable (`quantity` y `max_position_pct`)
- Comisión y slippage simulados en el backtest
- Stop-loss y take-profit listos para implementar (ver `config.yaml`)

---

## Próximos pasos recomendados (roadmap)

- [ ] Añadir más indicadores (RSI, MACD, ATR)
- [ ] Multi-asset / portfolio backtester
- [ ] Position sizing dinámico (Kelly, volatility targeting)
- [ ] Integración de datos fundamentales
- [ ] Dashboard con Streamlit o Dash
- [ ] Logging de trades en base de datos (SQLite / PostgreSQL)
- [ ] Tests de integración con IBKR (mock)
- [ ] CI/CD con GitHub Actions

---

## Advertencias importantes

> **Esto no es consejo financiero.**  
> El trading conlleva un riesgo significativo de pérdida de capital.  
> El paper trading no garantiza los mismos resultados que el trading real (slippage, liquidez, latencia, etc.).  
> Usa este código bajo tu propia responsabilidad.

---

## Licencia

MIT License – Siéntete libre de usarlo, modificarlo y mejorarlo.

---

**Creado con el objetivo de aprender quant trading de forma seria y estructurada.**
