import sys, time, random
sys.path.insert(0, r'E:\Projects\AeroProjects\quant-sim-aero')
import aero_quant

def gen_bars(n, seed=42):
    random.seed(seed)
    lines = ["date,sym,open,high,low,close,volume"]
    price = 100.0
    for i in range(n):
        o = price
        c = price + random.uniform(-5, 5)
        h = max(o, c) + random.uniform(0, 3)
        l = min(o, c) - random.uniform(0, 3)
        v = random.randint(100000, 1000000)
        lines.append(f"2025-01-{i+1:02d},600519,{o:.2f},{h:.2f},{l:.2f},{c:.2f},{v}")
        price = c
    return "\n".join(lines) + "\n"

def py_ma(values, period):
    if len(values) < period:
        return sum(values) / len(values) if values else 0.0
    return sum(values[-period:]) / period

def py_rsi(values, period=14):
    if len(values) <= period: return 50.0
    gains = []; losses = []
    for i in range(1, len(values)):
        diff = values[i] - values[i-1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period-1) + gains[i]) / period
        avg_loss = (avg_loss * (period-1) + losses[i]) / period
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)

def py_ema(values, period):
    if not values: return []
    k = 2 / (period + 1)
    ema = values[0]
    out = [ema]
    for v in values[1:]:
        ema = v * k + ema * (1 - k)
        out.append(ema)
    return out

def py_indicators(closes, highs, lows, volumes):
    last = closes[-1]
    ma5 = py_ma(closes, 5)
    ma10 = py_ma(closes, 10)
    ma20 = py_ma(closes, 20)
    ma60 = py_ma(closes, 60)
    rsi14 = py_rsi(closes, 14)
    ema_fast = py_ema(closes, 12)
    ema_slow = py_ema(closes, 26)
    difs = [a - b for a, b in zip(ema_fast, ema_slow)]
    deas = py_ema(difs, 9)
    dif = difs[-1]; dea = deas[-1]; hist = dif - dea
    # ATR
    trs = []
    for i in range(1, len(closes)):
        trs.append(max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])))
    atr = sum(trs[-14:]) / 14 if len(trs) >= 14 else 0.0
    # volume ratio
    if len(volumes) >= 6:
        base = sum(volumes[-6:-1]) / 5
        vr = max(0.01, volumes[-1] / base) if base > 0 else 1.0
    else: vr = 1.0
    return (last, ma5, ma10, ma20, rsi14, dif, dea, hist, atr, vr)

print("=" * 60)
print("quant-sim 技术指标 Benchmark")
print("=" * 60)

for N_BARS, N_ITER in [(120, 50000), (1000, 10000), (10000, 2000)]:
    bars_csv = gen_bars(N_BARS)
    closes = [float(line.split(',')[5]) for line in bars_csv.strip().split('\n')[1:]]
    highs  = [float(line.split(',')[3]) for line in bars_csv.strip().split('\n')[1:]]
    lows   = [float(line.split(',')[4]) for line in bars_csv.strip().split('\n')[1:]]
    vols   = [float(line.split(',')[6]) for line in bars_csv.strip().split('\n')[1:]]
    
    print(f"\n--- {N_BARS} 根 K 线 × {N_ITER} 次迭代 ---")
    
    # Python 原生
    t0 = time.perf_counter()
    for _ in range(N_ITER):
        py_indicators(closes, highs, lows, vols)
    t_py = (time.perf_counter() - t0) * 1000
    
    # Aero 1.2.5
    t0 = time.perf_counter()
    for _ in range(N_ITER):
        aero_quant.indicators(bars_csv, 5, 4, 3, 6)
    t_aero = (time.perf_counter() - t0) * 1000
    
    speedup = t_py / t_aero
    print(f"  Python 原生:  {t_py:8.1f} ms")
    print(f"  Aero 1.2.5:   {t_aero:8.1f} ms   →  {speedup:.1f}x 更快")
