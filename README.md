# 📈 Analizador Técnico Universal

Herramienta web para análisis técnico en tiempo real de cualquier activo financiero — acciones, criptomonedas, materias primas, índices y ETFs. Construida con Flask y Chart.js.

---

## ✨ ¿Qué hace?

Introduces cualquier ticker y obtienes al instante:

- **Veredicto automático** — 🟢 COMPRA / 🔴 VENTA / 🟡 NEUTRAL con las razones
- **4 gráficas interactivas** en tema oscuro: Precio + EMAs + Bollinger, RSI, MACD, Volumen
- **8 métricas en tiempo real**: RSI, EMA9/21/50, MACD, ATR, Bandas de Bollinger

---

## 📊 Indicadores incluidos

| Indicador | Descripción |
|---|---|
| EMA 9 / 21 / 50 | Medias móviles exponenciales para detectar tendencia |
| RSI (14) | Fuerza relativa — sobrecomprado (>70) / sobrevendido (<30) |
| MACD + Signal + Histograma | Momentum y cambios de tendencia |
| Bandas de Bollinger (20, 2σ) | Volatilidad y niveles extremos de precio |
| ATR (14) | Volatilidad promedio — útil para stop loss |
| Volumen | Confirmación de movimientos de precio |

---

## 🔍 Activos soportados

Cualquier ticker de Yahoo Finance:

| Tipo | Ejemplos |
|---|---|
| Acciones USA | AAPL, NVDA, TSLA, AMZN, MSFT |
| Acciones MX | AMXL.MX, CEMEXCPO.MX, WALMEX.MX |
| Criptomonedas | BTC-USD, ETH-USD, SOL-USD |
| Materias primas | GC=F (Oro), SI=F (Plata), CL=F (Petróleo) |
| Índices | ^GSPC (S&P500), ^IXIC (Nasdaq), ^MXX (IPC) |
| ETFs | SPY, QQQ, GLD |

---

## 🚀 Instalación y uso

```bash
# Clonar el repositorio
git clone https://github.com/rickf63/analizador-tecnico.git
cd analizador-tecnico

# Instalar dependencias
pip install flask yfinance pandas numpy

# Correr
python app.py
```

Abre **http://localhost:5001** en tu navegador.

---

## 🧠 Lógica del veredicto

El sistema evalúa 4 condiciones y asigna puntos:

| Condición | Puntos |
|---|---|
| EMA9 > EMA21 > EMA50 | +2 |
| EMA9 > EMA21 (moderado) | +1 |
| RSI < 30 (sobrevendido) | +2 |
| RSI > 70 (sobrecomprado) | -2 |
| MACD > Signal | +1 |
| Precio < Banda inferior BB | +1 |
| Precio > Banda superior BB | -1 |

- **≥ 3 puntos** → 🟢 COMPRA
- **≤ -2 puntos** → 🔴 VENTA  
- **Entre -1 y 2** → 🟡 NEUTRAL

> ⚠️ Este análisis es informativo. No constituye asesoría financiera.

---

## 🛠 Stack

- **Backend:** Python 3.13+, Flask, yfinance, pandas, numpy
- **Frontend:** HTML/CSS, JavaScript, Chart.js 4.4
- **Datos:** Yahoo Finance (tiempo real con yfinance)

---

## 📄 Licencia

MIT — libre para usar y modificar.
