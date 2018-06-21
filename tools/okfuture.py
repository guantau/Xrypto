import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as md
import time
import datetime
import calendar
import pytz
import requests
from matplotlib import gridspec
from matplotlib.finance import candlestick_ohlc
from matplotlib.dates import DateFormatter, WeekdayLocator, HourLocator, DayLocator, MONDAY


def F_contract_type(cp):

    if cp == 1:
        return 'BTC/CNY spot'
    elif cp == 2:
        return 'BTC/USD spot'
    elif cp == 3:
        return 'BTC/this_week'
    elif cp == 4:
        return 'BTC/next_week'
    elif cp == 5:
        return 'BTC/quarter'
    elif cp == 6:
        return 'LTC/CNY spot'
    elif cp == 7:
        return 'LTC/USD spot'
    elif cp == 8:
        return 'LTC/this_week'
    elif cp == 9:
        return 'LTC/next_week'
    elif cp == 0:
        return 'LTC/quarter'
    else:
        return None


def F_type(tp):

    if tp == 1:
        return '1min'
    elif tp == 2:
        return '3min'
    elif tp == 3:
        return '5min'
    elif tp == 4:
        return '15min'
    elif tp == 5:
        return '30min'
    elif tp == 6:
        return '1hour'
    elif tp == 7:
        return '2hour'
    elif tp == 8:
        return '4hour'
    elif tp == 9:
        return '6hour'
    elif tp == 10:
        return '12hour'
    elif tp == 11:
        return '1day'
    elif tp == 12:
        return '3day'
    elif tp == 13:
        return '1week'
    else:
        return None


def get_OHLC_api(CP, **kwargs):

    [cry, ctr] = CP.split('/')
    cry = cry.lower()
    if ctr == 'USD spot':
        return get_spot_api_US(symbol=cry + '_usd', **kwargs)
    elif ctr == 'CNY spot':
        return get_spot_api_CN(symbol=cry + '_cny', **kwargs)
    else:
        return get_future_api(symbol=cry + '_usd', contract_type=ctr, **kwargs)


def get_spot_api_CN(type='5min', symbol='btc_cny', size=None, since=None):

    ok_link = 'https://www.okcoin.cn/api/v1/kline.do?'
    CmdStr = 'symbol=' + symbol + '&type=' + type
    if size is not None:
        CmdStr += ('&size=' + str(size))
    if since is not None:
        CmdStr += ('&since=' + since)

    df = pd.read_json(ok_link + CmdStr)
    df.columns = ['t', 'open', 'high', 'low', 'close', 'v']  # 100x
    fx = get_USDCNY()
    df['open'] /= fx
    df['high'] /= fx
    df['low'] /= fx
    df['close'] /= fx
    print(" - Query at", time.strftime("%X", time.localtime(time.time())),
          ":", df.memory_usage().sum() / 1000, "KB,", len(df.index), "rows.")

    return df


def get_spot_api_US(type='5min', symbol='btc_usd', size=None, since=None):

    ok_link = 'https://www.okex.com/api/v1/kline.do?'
    CmdStr = 'symbol=' + symbol + '&type=' + type
    if size is not None:
        CmdStr += ('&size=' + str(size))
    if since is not None:
        CmdStr += ('&since=' + since)

    df = pd.read_json(ok_link + CmdStr)
    df.columns = ['t', 'open', 'high', 'low', 'close', 'v']  # 100x
    print(" - Query at", time.strftime("%X", time.localtime(time.time())),
          ":", df.memory_usage().sum() / 1000, "KB,", len(df.index), "rows.")

    return df


def get_future_api(contract_type='this_week', type='5min', symbol='btc_usd', size=None, since=None):

    ok_link = 'https://www.okex.com/api/v1/future_kline.do?'
    CmdStr = 'symbol=' + symbol + '&type=' + \
        type + '&contract_type=' + contract_type
    if size is not None:
        CmdStr += ('&size=' + str(size))
    if since is not None:
        CmdStr += ('&since=' + since)

    df = pd.read_json(ok_link + CmdStr)
    df.columns = ['t', 'open', 'high', 'low', 'close', 'v_usd', 'v']  # 100x
    print(" - Query at", time.strftime("%X", time.localtime(time.time())),
          ":", df.memory_usage().sum() / 1000, "KB,", len(df.index), "rows.")

    return df


def get_USDCNY():
    return requests.get('https://www.okex.com/api/v1/exchange_rate.do').json()['rate']


def get_Findex():
    return requests.get('https://www.okex.com/api/v1/future_index.do?symbol=btc_usd').json()['future_index']


def plot_candle(df):

    quotes = []
    for i in df.index:
        tp = (md.date2num(datetime.datetime.fromtimestamp(
            df['t'][i] / 1000)), df['open'][i], df['high'][i], df['low'][i], df['close'][i], df['v'][i])
        quotes.append(tp)

    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)

    candlestick_ohlc(ax, quotes, width=0.01, colorup='r', colordown='g')

    ax.xaxis_date()
    ax.autoscale_view()
    plt.setp(plt.gca().get_xticklabels(),
             rotation=45, horizontalalignment='right')

    plt.show()


def graph_compare(df1, df2, freq, name1, name2, DFs=None):

    t1 = []
    for d in df1['t']:
        t1.append(md.date2num(datetime.datetime.fromtimestamp(d / 1000)))
    t2 = []
    for d in df2['t']:
        t2.append(md.date2num(datetime.datetime.fromtimestamp(d / 1000)))

    fig = plt.figure(figsize=(12, 9))
    gs = gridspec.GridSpec(3, 1, height_ratios=[1, 4, 1])
    plt.rc('axes', grid=True)

    ax2 = plt.subplot(gs[2])
    ax2.set_title("Volume")
    ax2.set_xlim(min(t1 + t2) - 100, max(t1 + t2) + 100)

    ax0 = plt.subplot(gs[0], sharex=ax2)
    ax0.set_title("spread")
    ax1 = plt.subplot(gs[1], sharex=ax2)
    ax1.set_title("px")

    ax0.fill_between(t1, 0, df2['close'] - df1['close'],
                     where=df2['close'] >= df1['close'], color='b', alpha=0.5)
    ax0.fill_between(t1, 0, df2['close'] - df1['close'],
                     where=df2['close'] <= df1['close'], color='y', alpha=0.5)

    # plot the 1st line
    ax1.plot(t1, df1['close'], color='y', linewidth=2)

    # plot the other line
    if name1[:3] == name2[:3]:
        ax1.plot(t2, df2['close'], color='b', linewidth=2)
    else:
        ax1.set_ylabel(name1, color='y')

        axt = ax1.twinx()
        axt.plot(t2, df2['close'], color='b', linewidth=2)
        axt.set_ylabel(name2, color='b')

    if freq > 10:
        M_fmt = md.DateFormatter('%Y %b %d', tz=pytz.timezone('Asia/Taipei'))
        m_fmt = md.DateFormatter('%b %d', tz=pytz.timezone('Asia/Taipei'))
    elif freq > 2:
        M_fmt = md.DateFormatter('%b %d', tz=pytz.timezone('Asia/Taipei'))
        m_fmt = md.DateFormatter('%H:%M', tz=pytz.timezone('Asia/Taipei'))
    else:
        M_fmt = md.DateFormatter('%H:%M', tz=pytz.timezone('Asia/Taipei'))
        m_fmt = md.DateFormatter('%H:%M:%S', tz=pytz.timezone('Asia/Taipei'))

    ax2.xaxis.set_major_formatter(M_fmt)
    ax2.xaxis.set_minor_formatter(m_fmt)
    ax2.set_xlabel('Yellow: ' + name1 + ' | Blue:' + name2)
    ax2.fill_between(t1, 0, df1['v'], color='y', alpha=0.5)
    ax2.fill_between(t2, 0, df2['v'], color='b', alpha=0.5)
    fig.autofmt_xdate()

    if DFs is not None:

        if len(DFs) < 10:
            print("v1")
            for df in DFs:
                ax1.plot(t1, df['close'])
        else:
            print("v2")
            ax1.plot(t1, DFs['close'])

    fig.savefig(name1.replace('/', '_') + '_' +
                name2.replace('/', '_') + '.png')
    ax2.xaxis_date()
    ax2.autoscale_view()
    plt.show()


pd.options.display.float_format = '{:,.3f}'.format

print("======================================================")
print(" 1: BTC/CNY spot  | 2: BTC/USD spot  |                ")
print(" 3: BTC/this week | 4: BTC/next week | 5: BTC/quarter ")
print(" 6: LTC/CNY spot  | 7: LTC/USD spot  |                ")
print(" 8: LTC/this week | 9: LTC/next week | 0: LTC/quarter ")
print("======================================================")
in_str = input("Please select 2 contract types (separte by space): ")
[x, y] = list(map(int, in_str.split()))
print("\n --- You select", F_contract_type(x).upper(),
      "and", F_contract_type(y).upper(), " --- \n")

print("======================================================")
print("  1:  1 min  |  2:  3 min  |  3: 5 min  |  4: 15 min  ")
print("  5: 30 min  |  6:  1 hour |  7: 2 hour |  8:  4 hour ")
print("  9:  6 hour | 10: 12 hour | 11: 1 day  | 12:  3 day  ")
print(" 13:  1 week |                                        ")
print("======================================================")
f = int(input("Please select a k-bar interval: "))
print("\n --- You select", F_type(f), " ---\n")

s = input("Please give data size (default value = 500): ")

try:
    sz = int(s)
except:
    sz = 500

df1 = get_OHLC_api(CP=F_contract_type(x), type=F_type(f), size=sz)
df2 = get_OHLC_api(CP=F_contract_type(y), type=F_type(f), size=sz)

print("\n", F_contract_type(x).upper())
print(df1.iloc[len(df1.index) - 1])
print("\n", F_contract_type(y).upper())
print(df2.iloc[len(df1.index) - 1])

print('\n\nCurrent FX:', get_USDCNY(), "\nCurrent Index:", get_Findex())
print(df1['v'].sum())
print(df2['v'].sum())

graph_compare(df1, df2, f, F_contract_type(x), F_contract_type(y))
