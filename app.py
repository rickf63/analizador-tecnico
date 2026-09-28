# -*- coding: utf-8 -*-
"""
Analizador Técnico Universal
=============================
Metes cualquier ticker y te da análisis técnico completo:
EMAs, RSI, MACD, Bandas de Bollinger, Volumen y señales.

Requisitos:
  pip install flask yfinance pandas numpy

Uso:
  python app.py
  Abre http://localhost:5001
"""

import numpy as np
import pandas as pd
import yfinance as yf
from flask import Flask, render_template_string, jsonify, request
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# ----------------------------------------------------------------------
# INDICADORES
# ----------------------------------------------------------------------
def calcular_indicadores(ticker, periodo="1y"):
    df = yf.download(ticker, period=periodo, interval="1d",
                     auto_adjust=True, progress=False)
    if df.empty:
        return None, "Ticker no encontrado o sin datos."
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()

    df["EMA9"]  = df["Close"].ewm(span=9,  adjust=False).mean()
    df["EMA21"] = df["Close"].ewm(span=21, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))

    ema12        = df["Close"].ewm(span=12, adjust=False).mean()
    ema26        = df["Close"].ewm(span=26, adjust=False).mean()
    df["MACD"]   = ema12 - ema26
    df["SIGNAL"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["HIST"]   = df["MACD"] - df["SIGNAL"]

    sma20         = df["Close"].rolling(20).mean()
    std20         = df["Close"].rolling(20).std()
    df["BB_MID"]  = sma20
    df["BB_UP"]   = sma20 + 2 * std20
    df["BB_DOWN"] = sma20 - 2 * std20

    hl = df["High"] - df["Low"]
    hc = (df["High"] - df["Close"].shift()).abs()
    lc = (df["Low"]  - df["Close"].shift()).abs()
    df["ATR"] = pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(14).mean()

    return df.dropna(), None


def senal_actual(df):
    ult     = df.iloc[-1]
    precio  = float(ult["Close"])
    ema9    = float(ult["EMA9"])
    ema21   = float(ult["EMA21"])
    ema50   = float(ult["EMA50"])
    rsi     = float(ult["RSI"])
    macd    = float(ult["MACD"])
    signal  = float(ult["SIGNAL"])
    bb_up   = float(ult["BB_UP"])
    bb_down = float(ult["BB_DOWN"])

    puntos = 0
    razones = []

    if ema9 > ema21 > ema50:
        puntos += 2
        razones.append("✅ EMA9 > EMA21 > EMA50 — tendencia alcista fuerte")
    elif ema9 > ema21:
        puntos += 1
        razones.append("🟡 EMA9 > EMA21 — tendencia alcista moderada")
    else:
        puntos -= 1
        razones.append("❌ EMA9 < EMA21 — tendencia bajista")

    if rsi < 30:
        puntos += 2
        razones.append(f"✅ RSI {rsi:.1f} — sobrevendido, posible rebote")
    elif rsi > 70:
        puntos -= 2
        razones.append(f"❌ RSI {rsi:.1f} — sobrecomprado, posible caída")
    else:
        razones.append(f"🟡 RSI {rsi:.1f} — zona neutral")

    if macd > signal:
        puntos += 1
        razones.append("✅ MACD > Signal — momentum alcista")
    else:
        puntos -= 1
        razones.append("❌ MACD < Signal — momentum bajista")

    if precio < bb_down:
        puntos += 1
        razones.append("✅ Precio bajo banda inferior Bollinger — posible rebote")
    elif precio > bb_up:
        puntos -= 1
        razones.append("❌ Precio sobre banda superior Bollinger — posible corrección")

    if puntos >= 3:
        veredicto, color = "COMPRA", "#00d4aa"
    elif puntos <= -2:
        veredicto, color = "VENTA", "#ff4444"
    else:
        veredicto, color = "NEUTRAL", "#ffaa00"

    return {
        "veredicto": veredicto, "color": color, "puntos": puntos,
        "razones": razones, "rsi": round(rsi, 1),
        "macd": round(macd, 4), "signal": round(signal, 4),
        "ema9": round(ema9, 2), "ema21": round(ema21, 2), "ema50": round(ema50, 2),
        "bb_up": round(bb_up, 2), "bb_down": round(bb_down, 2),
        "atr": round(float(ult["ATR"]), 2),
    }


# ----------------------------------------------------------------------
# HTML
# ----------------------------------------------------------------------
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Analizador Técnico</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{background:#0f0f0f;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;padding:16px}
    h1{color:#00d4aa;font-size:1.4rem;margin-bottom:4px}
    .sub{color:#666;font-size:.8rem;margin-bottom:16px}
    .buscador{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap}
    input{flex:1;min-width:150px;background:#1a1a1a;border:1px solid #333;color:#fff;padding:10px 14px;border-radius:8px;font-size:1rem;outline:none}
    input:focus{border-color:#00d4aa}
    select{background:#1a1a1a;border:1px solid #333;color:#fff;padding:10px 14px;border-radius:8px;font-size:.9rem;outline:none;cursor:pointer}
    button{background:#00d4aa;color:#000;border:none;padding:10px 20px;border-radius:8px;font-size:.95rem;font-weight:700;cursor:pointer}
    button:hover{background:#00b894}
    .ejemplos{color:#555;font-size:.75rem;margin-bottom:20px}
    .ejemplos span{color:#00d4aa;cursor:pointer;margin-right:8px}
    .card{background:#1a1a1a;border-radius:10px;padding:16px;margin-bottom:16px;border:1px solid #2a2a2a}
    .card h2{color:#888;font-size:.8rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px}
    .precio-header{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin-bottom:16px}
    .precio{font-size:2rem;font-weight:700}
    .cp{color:#00d4aa;font-size:1rem}
    .cn{color:#ff4444;font-size:1rem}
    .vbox{border-radius:10px;padding:14px 18px;margin-bottom:16px;border:1px solid}
    .vlbl{font-size:1.4rem;font-weight:700}
    .razones p{font-size:.85rem;color:#ccc;margin-top:4px}
    .grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:16px}
    .met{background:#111;border-radius:8px;padding:10px;border:1px solid #222}
    .met .lbl{color:#666;font-size:.7rem;text-transform:uppercase}
    .met .val{font-size:1.1rem;font-weight:600;margin-top:2px}
    canvas{max-height:220px}
    .loading{color:#555;text-align:center;padding:40px;display:none}
    .err{color:#ff4444;background:#1a0000;border:1px solid #ff444433;border-radius:8px;padding:12px;margin-bottom:16px;display:none}
    #resultado{display:none}
  </style>
</head>
<body>
  <h1>📈 Analizador Técnico Universal</h1>
  <p class="sub">EMAs · RSI · MACD · Bollinger · Señales — cualquier activo</p>
  <div class="buscador">
    <input id="ticker" type="text" placeholder="AAPL, BTC-USD, GC=F, AMXL.MX..."
           onkeydown="if(event.key==='Enter')analizar()">
    <select id="periodo">
      <option value="3mo">3 meses</option>
      <option value="6mo">6 meses</option>
      <option value="1y" selected>1 año</option>
      <option value="2y">2 años</option>
    </select>
    <button onclick="analizar()">Analizar</button>
  </div>
  <p class="ejemplos">Ejemplos:
    <span onclick="setTicker('AAPL')">AAPL</span>
    <span onclick="setTicker('NVDA')">NVDA</span>
    <span onclick="setTicker('TSLA')">TSLA</span>
    <span onclick="setTicker('BTC-USD')">BTC-USD</span>
    <span onclick="setTicker('ETH-USD')">ETH-USD</span>
    <span onclick="setTicker('GC=F')">GC=F (Oro)</span>
    <span onclick="setTicker('AMXL.MX')">AMXL.MX</span>
    <span onclick="setTicker('^MXX')">^MXX (IPC)</span>
  </p>
  <div class="loading" id="loading">⏳ Descargando datos...</div>
  <div class="err" id="error"></div>
  <div id="resultado">
    <div class="card">
      <div class="precio-header">
        <span class="precio" id="precio"></span>
        <span id="cambio"></span>
        <span style="color:#555;font-size:.85rem" id="nombre"></span>
      </div>
      <div class="vbox" id="vbox">
        <div class="vlbl" id="vlbl"></div>
        <div class="razones" id="razones"></div>
      </div>
    </div>
    <div class="grid3" id="metricas"></div>
    <div class="card"><h2>Precio + EMAs + Bandas de Bollinger</h2><canvas id="cPrecio"></canvas></div>
    <div class="card"><h2>RSI (14)</h2><canvas id="cRSI"></canvas></div>
    <div class="card"><h2>MACD</h2><canvas id="cMACD"></canvas></div>
    <div class="card"><h2>Volumen</h2><canvas id="cVol"></canvas></div>
  </div>
<script>
let C={};
function setTicker(t){document.getElementById('ticker').value=t;analizar()}
function kill(id){if(C[id]){C[id].destroy();delete C[id]}}
function opts(extra){return{responsive:true,plugins:{legend:{labels:{color:'#888',font:{size:10}}}},scales:{x:{ticks:{color:'#555',maxTicksLimit:8},grid:{color:'#1f1f1f'}},y:{ticks:{color:'#555'},grid:{color:'#1f1f1f'},...(extra||{})}}}}

async function analizar(){
  const t=document.getElementById('ticker').value.trim().toUpperCase();
  const p=document.getElementById('periodo').value;
  if(!t)return;
  document.getElementById('loading').style.display='block';
  document.getElementById('resultado').style.display='none';
  document.getElementById('error').style.display='none';
  try{
    const r=await fetch(`/api/analizar?ticker=${t}&periodo=${p}`);
    const d=await r.json();
    document.getElementById('loading').style.display='none';
    if(d.error){document.getElementById('error').textContent=d.error;document.getElementById('error').style.display='block';return}
    document.getElementById('resultado').style.display='block';
    const pr=d.precio;
    const ch=d.cambio_pct;
    document.getElementById('precio').textContent='$'+pr.toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
    document.getElementById('cambio').innerHTML=ch>=0?`<span class="cp">▲ +${ch.toFixed(2)}%</span>`:`<span class="cn">▼ ${ch.toFixed(2)}%</span>`;
    document.getElementById('nombre').textContent=t+' | '+d.fecha;
    const vb=document.getElementById('vbox');
    vb.style.borderColor=d.senal.color+'44';vb.style.background=d.senal.color+'11';
    document.getElementById('vlbl').style.color=d.senal.color;
    document.getElementById('vlbl').textContent=(d.senal.veredicto==='COMPRA'?'🟢':d.senal.veredicto==='VENTA'?'🔴':'🟡')+' '+d.senal.veredicto;
    document.getElementById('razones').innerHTML=d.senal.razones.map(r=>`<p>${r}</p>`).join('');
    document.getElementById('metricas').innerHTML=`
      <div class="met"><div class="lbl">RSI</div><div class="val" style="color:${d.senal.rsi<30?'#00d4aa':d.senal.rsi>70?'#ff4444':'#fff'}">${d.senal.rsi}</div></div>
      <div class="met"><div class="lbl">EMA 9</div><div class="val">$${d.senal.ema9.toLocaleString('en-US',{minimumFractionDigits:2})}</div></div>
      <div class="met"><div class="lbl">EMA 21</div><div class="val">$${d.senal.ema21.toLocaleString('en-US',{minimumFractionDigits:2})}</div></div>
      <div class="met"><div class="lbl">EMA 50</div><div class="val">$${d.senal.ema50.toLocaleString('en-US',{minimumFractionDigits:2})}</div></div>
      <div class="met"><div class="lbl">MACD</div><div class="val" style="color:${d.senal.macd>d.senal.signal?'#00d4aa':'#ff4444'}">${d.senal.macd}</div></div>
      <div class="met"><div class="lbl">ATR</div><div class="val">$${d.senal.atr.toLocaleString('en-US',{minimumFractionDigits:2})}</div></div>
      <div class="met"><div class="lbl">BB Superior</div><div class="val">$${d.senal.bb_up.toLocaleString('en-US',{minimumFractionDigits:2})}</div></div>
      <div class="met"><div class="lbl">BB Inferior</div><div class="val">$${d.senal.bb_down.toLocaleString('en-US',{minimumFractionDigits:2})}</div></div>`;
    const f=d.fechas;
    kill('precio');
    C['precio']=new Chart(document.getElementById('cPrecio').getContext('2d'),{type:'line',data:{labels:f,datasets:[
      {label:'Precio',data:d.close,borderColor:'#fff',borderWidth:1.5,pointRadius:0,fill:false,tension:.3},
      {label:'EMA9',data:d.ema9,borderColor:'#00d4aa',borderWidth:1.5,pointRadius:0,fill:false,tension:.3},
      {label:'EMA21',data:d.ema21,borderColor:'#ffaa00',borderWidth:1.5,pointRadius:0,fill:false,tension:.3},
      {label:'EMA50',data:d.ema50,borderColor:'#ff6b6b',borderWidth:1.5,pointRadius:0,fill:false,tension:.3},
      {label:'BB Sup',data:d.bb_up,borderColor:'#4444ff',borderWidth:1,borderDash:[3,3],pointRadius:0,fill:false},
      {label:'BB Inf',data:d.bb_down,borderColor:'#4444ff',borderWidth:1,borderDash:[3,3],pointRadius:0,fill:'-1',backgroundColor:'rgba(68,68,255,.05)'},
    ]},options:opts()});
    kill('rsi');
    C['rsi']=new Chart(document.getElementById('cRSI').getContext('2d'),{type:'line',data:{labels:f,datasets:[
      {label:'RSI',data:d.rsi,borderColor:'#a78bfa',borderWidth:1.5,pointRadius:0,fill:false,tension:.3}
    ]},options:{responsive:true,plugins:{legend:{labels:{color:'#888',font:{size:10}}}},scales:{x:{ticks:{color:'#555',maxTicksLimit:8},grid:{color:'#1f1f1f'}},y:{min:0,max:100,ticks:{color:'#555',callback:v=>v===30||v===70||v===50?v:''},grid:{color:ctx=>ctx.tick.value===30||ctx.tick.value===70?'#ff444444':'#1f1f1f'}}}}});
    kill('macd');
    C['macd']=new Chart(document.getElementById('cMACD').getContext('2d'),{type:'bar',data:{labels:f,datasets:[
      {label:'Histograma',data:d.hist,backgroundColor:d.hist.map(v=>v>=0?'rgba(0,212,170,.5)':'rgba(255,68,68,.5)'),order:2},
      {label:'MACD',data:d.macd,type:'line',borderColor:'#00d4aa',borderWidth:1.5,pointRadius:0,fill:false,order:1},
      {label:'Signal',data:d.signal,type:'line',borderColor:'#ffaa00',borderWidth:1.5,pointRadius:0,fill:false,order:1},
    ]},options:opts()});
    kill('vol');
    C['vol']=new Chart(document.getElementById('cVol').getContext('2d'),{type:'bar',data:{labels:f,datasets:[
      {label:'Volumen',data:d.volumen,backgroundColor:'rgba(0,212,170,.3)',borderColor:'rgba(0,212,170,.6)',borderWidth:0}
    ]},options:{responsive:true,plugins:{legend:{labels:{color:'#888',font:{size:10}}}},scales:{x:{ticks:{color:'#555',maxTicksLimit:8},grid:{color:'#1f1f1f'}},y:{ticks:{color:'#555',callback:v=>v>=1e9?(v/1e9).toFixed(1)+'B':v>=1e6?(v/1e6).toFixed(1)+'M':v},grid:{color:'#1f1f1f'}}}}});
  }catch(e){
    document.getElementById('loading').style.display='none';
    document.getElementById('error').textContent='Error al conectar con el servidor.';
    document.getElementById('error').style.display='block';
  }
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/analizar")
def analizar():
    ticker  = request.args.get("ticker", "").upper().strip()
    periodo = request.args.get("periodo", "1y")
    if not ticker:
        return jsonify({"error": "Ingresa un ticker válido."})
    df, err = calcular_indicadores(ticker, periodo)
    if err:
        return jsonify({"error": err})
    ult    = df.iloc[-1]
    prev   = df.iloc[-2]
    cambio = (float(ult["Close"]) - float(prev["Close"])) / float(prev["Close"]) * 100
    senal  = senal_actual(df)
    N      = min(len(df), 252)
    df_p   = df.tail(N)
    def s(col): return [round(x,4) if pd.notna(x) else None for x in df_p[col].tolist()]
    return jsonify({
        "ticker": ticker, "precio": round(float(ult["Close"]),2),
        "cambio_pct": round(cambio,2), "fecha": str(df_p.index[-1].date()),
        "senal": senal, "fechas": df_p.index.strftime("%d/%m").tolist(),
        "close": s("Close"), "ema9": s("EMA9"), "ema21": s("EMA21"), "ema50": s("EMA50"),
        "rsi": s("RSI"), "macd": s("MACD"), "signal": s("SIGNAL"), "hist": s("HIST"),
        "bb_up": s("BB_UP"), "bb_down": s("BB_DOWN"), "volumen": s("Volume"),
    })

if __name__ == "__main__":
    import socket
    try: ip = socket.gethostbyname(socket.gethostname())
    except: ip = "127.0.0.1"
    print("="*55)
    print("  ANALIZADOR TÉCNICO UNIVERSAL")
    print("="*55)
    print(f"\n  PC:  http://localhost:5001")
    print(f"  CEL: http://{ip}:5001")
    print("\n  Ctrl+C para detener")
    print("="*55)
    app.run(host="0.0.0.0", port=5001, debug=False)