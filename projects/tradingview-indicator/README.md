# Pardeep Trade Helper — TradingView Indicator

Ek hi indicator mein:
- **BUY / SELL signals**: sirf tab aata hai jab EMA 9/21, 200 EMA trend, Supertrend, RSI aur ADX sab ek hi direction mein hon. Candle close hone ke baad hi aata hai, repaint nahi karta.
- **Stop Loss + Target 1 + Target 2** lines, ATR ke hisaab se apne aap
- **Support / Resistance** lines (pivot se)
- **Dashboard**: Trend, Supertrend, RSI, ADX aur ek Bias score (Strong Buy ... Strong Sell)
- **Alerts**: phone/email pe BUY/SELL, entry, SL aur TP ke saath

## TradingView mein kaise lagaye
1. https://www.tradingview.com pe chart kholo
2. Neeche **Pine Editor** tab kholo
3. Jo code pehle se hai use hata do, phir `pardeep_trade_helper.pine` ka poora code paste karo
4. **Save**, phir **Add to chart**
5. Settings (⚙️) se EMA lengths, SL multiplier, filters wagera badal sakte ho

## Alert lagana
Chart pe **Alert (⏰)** kholo. Condition mein **Pardeep Trade Helper** chuno, phir inme se ek:
- **Any alert() function call**: message mein Entry, SL, TP1 aur TP2 sab aata hai (recommended)
- ya **PTH BUY** / **PTH SELL**

## Tips
- 15m / 1H / 4H timeframe pe best kaam karta hai. 1m pe signals noisy hote hain.
- Sideways market mein ADX filter on rakho, ye fake signals kaafi kam karta hai.
- Pehle **paper trading / backtest** karo, phir asli paisa lagao.

> ⚠️ Ye sirf educational tool hai, financial advice nahi. Koi bhi indicator 100% sahi nahi hota. Hamesha stop loss lagao aur utna hi risk lo jitna kho sakte ho.
