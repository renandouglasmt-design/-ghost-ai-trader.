"""GHOST AI Trader - paper trading with public Binance candles only."""
import datetime as dt
import json
import os
import pathlib
import statistics
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
STATE = ROOT / 'data' / 'state.json'
LOG = ROOT / 'data' / 'operations.jsonl'
SYMBOL = os.environ.get('SYMBOL', 'BTCUSDT')
URL = f'https://data-api.binance.vision/api/v3/klines?symbol={SYMBOL}&interval=5m&limit=120'


def sma(v, n):
    return statistics.mean(v[-n:])


def rsi(v, n=14):
    changes = [v[i] - v[i-1] for i in range(len(v)-n, len(v))]
    gains = sum(max(0, x) for x in changes) / n
    losses = sum(max(0, -x) for x in changes) / n
    return 100 if losses == 0 else 100 - (100 / (1 + gains / losses))


def votes(closes, volumes):
    """Four distinct, reproducible signals. Not trained ML models."""
    last = closes[-1]
    # 1: trend
    trend = 'BUY' if sma(closes, 10) > sma(closes, 30) else 'SELL'
    # 2: momentum confirmation
    mom = 'BUY' if rsi(closes) > 55 else 'SELL' if rsi(closes) < 45 else 'WAIT'
    # 3: relative price breakout (prior 20 bars)
    ceiling, floor = max(closes[-21:-1]), min(closes[-21:-1])
    breakout = 'BUY' if last > ceiling else 'SELL' if last < floor else 'WAIT'
    # 4: volume + direction confirmation
    active = volumes[-1] > 1.1 * sma(volumes[:-1], 20)
    vol = ('BUY' if last > closes[-2] else 'SELL') if active else 'WAIT'
    return {'trend': trend, 'momentum': mom, 'breakout': breakout, 'volume': vol}


def decide(ballots):
    return next(iter(ballots.values())) if len(set(ballots.values())) == 1 else 'WAIT'


def fetch():
    req = urllib.request.Request(URL, headers={'User-Agent': 'ghost-ai-trader-paper/1.0'})
    with urllib.request.urlopen(req, timeout=15) as response:
        arr = json.load(response)
    # Ignore unfinished candle to avoid look-ahead behavior.
    closed = arr[:-1]
    return [float(x[4]) for x in closed], [float(x[5]) for x in closed], int(closed[-1][6])


def main():
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        prices, volumes, candle_id = fetch()
        if len(prices) < 40:
            raise RuntimeError('Insufficient candle history')
    except Exception as ex:
        print(f'Data unavailable; no trade: {ex}')
        return
    state = json.loads(STATE.read_text()) if STATE.exists() else {'cash': 1000.0, 'asset': 0.0, 'last_candle': 0, 'entry': None, 'peak_equity': 1000.0}
    if state['last_candle'] == candle_id:
        print('Candle already processed; nothing to do')
        return
    price = prices[-1]
    ballots = votes(prices, volumes)
    signal = decide(ballots)
    equity = state['cash'] + state['asset'] * price
    state['peak_equity'] = max(state.get('peak_equity', equity), equity)
    # Hard stop if paper account is 2% down from maximum equity (conservative).
    halted = equity < state['peak_equity'] * 0.98
    action = 'HOLD'
    if state['asset'] > 0 and (signal == 'SELL' or (state.get('entry') and price <= state['entry'] * 0.99)):
        state['cash'] += state['asset'] * price * (1 - 0.001)
        state['asset'] = 0.0
        state['entry'] = None
        action = 'SELL_PAPER'
    elif not halted and signal == 'BUY' and state['asset'] == 0 and state['cash'] >= 20:
        stake = min(state['cash'] * 0.10, 100.0)  # max 10% of remaining cash
        state['cash'] -= stake
        state['asset'] += (stake / price) * (1 - 0.001)
        state['entry'] = price
        action = 'BUY_PAPER'
    state['last_candle'] = candle_id
    state['last_run'] = now
    state['last_price'] = price
    state['equity'] = round(state['cash'] + state['asset'] * price, 6)
    STATE.parent.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2) + '\n')
    event = {'at': now, 'symbol': SYMBOL, 'candle_id': candle_id, 'price': price, 'votes': ballots, 'consensus': signal, 'action': action, 'equity': state['equity'], 'halted': halted}
    with LOG.open('a') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    print(json.dumps(event, ensure_ascii=False))


if __name__ == '__main__':
    main()
