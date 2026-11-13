# quant-sim-aero

用 **Aero 1.2.5** 写的 quant-sim 技术指标加速内核 — 编译成 Python C 扩展，替换 quant-sim 里的 TechnicalAnalyzer 原生 Python 实现。

## 结果

| 场景 | Python 原生 | Aero 1.2.5 | Speedup |
|------|-------------|------------|---------|
| 120 根 K 线 × 50000 次全指标 | 2570 ms | 1867 ms | **1.4x** |
| 1000 根 K 线 × 10000 次全指标 | 5247 ms | 3034 ms | **1.7x** |
| 10000 根 K 线 × 2000 次全指标 | 10630 ms | 6060 ms | **1.8x** |

K 线越多，Aero + LLVM O2 相对 Python 的优势越明显。

## 实现

Aero 内核一次调用就返回 quant-sim get_indicators 需要的全部指标：MA5/10/20/60、RSI14、MACD (DIF/DEA/hist)、ATR14、量比、趋势码。

- 输入：CSV 文本，一行一根 K 线（date,sym,open,high,low,close,volume）
- 输出：文本协议 #section ind 11 + 一行逗号分隔值
- 编译：ero build src/kernel.aero --pyext --py-module aero_quant
- 产物：ero_quant.pyd（Windows）/ ero_quant.so（Linux/macOS）

## 导出的函数

| 函数 | 说明 |
|------|------|
| ma(bars, close_col, period) | 简单移动平均 |
| ma(bars, close_col, period) | 指数移动平均 |
| si(bars, close_col, period) | RSI（Wilder 平滑） |
| macd(bars, close_col, fast, slow, signal) | MACD（DIF/DEA/柱） |
| tr(bars, high_col, low_col, close_col, period) | ATR（Wilder 平滑） |
| 	rend(bars, close_col) | 趋势码（0 多头/1 空头/2 短期多/3 短期空/4 震荡） |
| indicators(bars, close_col, high_col, low_col, volume_col) | 一次返回全部 11 个指标值 |
| prescreen(quotes, params) | 全市场预筛选（价格带/手数/费用约束/按涨幅排序） |
| cho_col(bars, col) | 列回显（精度校验） |

## 用法

``python
import aero_quant

bars_csv = "date,sym,open,high,low,close,volume\n" + "\n".join(
    f"2025-01-{i+1:02d},600519,100,101,99,{100+i*0.1:.2f},100000"
    for i in range(120)
) + "\n"

result = aero_quant.indicators(bars_csv, close_col=5, high_col=4, low_col=3, volume_col=6)
# → b'#section ind 11\n82.08,80.21,76.79,74.75,67.10,0.61,-0.64,2.51,3.67,0.53,0\n'
``

解析输出：

``python
def parse_ind(raw: bytes):
    lines = raw.decode().strip().split("\n")
    # lines[0] = "#section ind 11"
    values = [float(x) for x in lines[1].split(",")]
    return {
        "close": values[0], "ma5": values[1], "ma10": values[2], "ma20": values[3],
        "rsi14": values[4], "macd_dif": values[5], "macd_dea": values[6],
        "macd_hist": values[7], "atr14": values[8], "volume_ratio": values[9],
        "trend": int(values[10]),
    }
``

## 构建

需要 **Aero 1.2.5+** 工具链（Rust 1.97+, LLVM 22）。

`ash
aero build src/kernel.aero --pyext --py-module aero_quant
`

输出 ero_quant.pyd / ero_quant.so，直接丢给 Python import aero_quant。

## 兼容性

kernel 精确复现 quant-sim 	echnical.py 的行为（包括它当前版本里 RSI/ATR 用简单平均而不是 Wilder 平滑、MACD DIF 窗口重建等 quirks）。不改变上游逻辑，只替换实现。

## 已知限制

- Windows wheel 已测试；Linux/macOS wheel 需要在对应平台编译（Aero 编译器支持三平台）。
- 当前 wire format 是 CSV 文本 + 固定列号，性能最优方案（裸 f64 数组 FFI）留作后续版本。

## 免责声明 · Disclaimer

**本项目仅用于技术研究与学习目的，不构成任何投资建议。**

quant-sim-aero 是 quant-sim 的技术指标计算加速内核，仅替换数值计算实现，不涉及行情数据获取、交易信号生成、模拟撮合或任何资金操作。作者不对任何人基于本项目做出的交易决策负责，不对因使用本项目导致的直接或间接损失承担任何责任。

量化交易存在极高风险，过往业绩不代表未来表现。请在充分了解风险的前提下独立做出投资决策。

---

**This project is for technical research and educational purposes only. It does not constitute any investment advice.**

quant-sim-aero is a technical-indicator acceleration kernel for quant-sim. It only replaces the numerical computation implementation and does not involve market data acquisition, trading signal generation, order matching, or any capital operations. The author is not responsible for any trading decisions made by anyone based on this project, nor for any direct or indirect losses caused by its use.

Quantitative trading carries extremely high risks. Past performance does not represent future results. Please make independent investment decisions only after fully understanding the risks.

## License

MIT

> **贡献者说明 / Contributor Notice：** 本仓库唯一合法贡献者账号为 **SereinTeam (SereinCin)**。若您看到其他名称，系 Git 客户端身份配置错误导致的显示异常。
