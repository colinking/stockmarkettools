#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime,date
from yahoo_finance import Share
import requests
import re
from lxml import html
from bs4 import BeautifulSoup
from stockstats import StockDataFrame
from pandas_datareader import data
from pandas import Series,Timestamp,Timedelta
import os
import json
import pprint

def yahoo_ks(ticker):
    """
    Loads the Key Statistics page on Yahoo Finance for a given ticker symbol.
    Returns all of the matching values for each of the statistics.
    Each of the stats should match (substring match is fine) one of the stats on
    the key statistics page (ex. "Market Cap").
    """
    stats = [
        "Short % of Float",
        "% Held by Institutions",
        "Return on Equity",
        "Float",
    ]
    page = requests.get('http://finance.yahoo.com/q/ks?s=%s+Key+Statistics' % ticker)
    tree = html.fromstring(page.text)
    results = {}
    for stat in stats:
        value = tree.xpath('//td[contains(text(), "'+stat+'")]/following-sibling::td[1]/text()')
        results[stat] = value[0] if value else None
    return results

def ibd_stock_checkup(ticker, session):
    """
    Loads information from Investors.com's IBD Stock Checkup Tool.
    """
    page = session.get('http://research.investors.com/stockcheckup.aspx?symbol=%s'%ticker)
    soup = BeautifulSoup(page.text, "html.parser")
    tree = html.fromstring(page.text)
    stats = {
        "Industry Group Rank (1 to 197)": "industry_rank",
        "EPS Due Date": "next_earning",
        "EPS Rating": "eps_rating",
        "EPS % Chg (Last Qtr)": "eps_change",
        "3 Yr EPS Growth Rate": "3y_eps_growth",
        "3 Yr Sales Growth Rate": "3y_sales_growth",
        "RS Rating": "rs_rating",
        "Accumulation/Distribution Rating": "acc_distr_rating",
        "Composite Rating": "ibd_rating"
    }
    results = {}
    for stat,statkey in stats.iteritems():
        value = tree.xpath('//*[contains(text(), "'+stat+'")]/parent::td/following-sibling::td[1]/text()')
        results[statkey] = value[0].strip()
    # Fetch Industry name
    results["industry"] = soup.find(id='groupName').text.strip(' :')[12:]
    # Check if top 5 composite ranking
    composite_rankings = soup.find(id="divComposite").find_all(class_="stockRoll")
    results["industry_top5"] = False
    for i in range(len(composite_rankings)):
        if composite_rankings[i].text == ticker:
            results["industry_top5"] = i+1
    # Count the green circles
    results["fundamental_greens"] = len(soup.find(id="Fundamentals").find_all('a', class_='passDef', rel='#cluetipPass'))
    results["technical_greens"] = len(soup.find(id="Technicals").find_all('a', class_='passDef', rel='#cluetipPass'))
    return results

def checklist(symbol, ibd50_list, ibd_session):
    """
    Looks up information on a given stock market symbol.
    The returned dictionary contains all information from
    Dr. Wish's Stock Checklist for HONR348M.
    """
    stock = {}
    # Load price data from yahoo.
    share = Share(symbol)
    ks = yahoo_ks(symbol)

    # Basics
    basics = stock["basics"] = {}
    basics["date"] = datetime.now().strftime("%m/%d/%Y %I:%M:%S%z")
    basics["symbol"] = symbol
    basics["equity_name"] = share.get_name()
    basics["price"] = float(share.get_price())
    basics["52w_low"] = float(share.get_year_low())
    basics["52w_high"] = float(share.get_year_high())
    basics["percent_from_52w_low"] = share.get_percent_change_from_year_low()
    basics["percent_from_52w_high"] = share.get_percent_change_from_year_high()

    # IBD (Stocks only)
    ibd = stock["ibd"] = ibd_stock_checkup(symbol, ibd_session)
    # ibd["industry"]
    ibd["industry_rank"] = float(ibd["industry_rank"])
    # ibd["industry_top5"]
    # ibd["3y_eps_growth"]
    # ibd["3y_sales_growth"]
    # ibd["eps_change"]
    ibd["eps_rating"] = float(ibd["eps_rating"])
    ibd["rs_rating"] = float(ibd["rs_rating"])
    # ibd["acc_distr_rating"]
    ibd["ibd_rating"] = float(ibd["ibd_rating"])
    ibd["in_ibd50"] = symbol in ibd50_list
    # ibd["fundamental_greens"]
    # ibd["technical_greens"]
    ibd["next_earning"] = datetime.strptime(ibd["next_earning"], '%m/%d/%Y')

    # Yahoo Finance (Stocks only)
    yahoo = stock["yahoo"] = {}
    yahoo["pe"] = float(share.get_price_earnings_ratio())
    yahoo["peg"] = float(share.get_price_earnings_growth_ratio())
    yahoo["ps"] = float(share.get_price_sales())
    yahoo["market_cap"] = share.get_market_cap()
    yahoo["float"] = ks["Float"]
    yahoo["annual_roe"] = ks["Return on Equity"]
    yahoo["percent_inst"] = ks["% Held by Institutions"]
    yahoo["percent_float_short"] = ks["Short % of Float"]
    yahoo["short_ratio"] = float(share.get_short_ratio())

    # Evidence of an uptrend/downtrend
    uptrend = stock["uptrend"] = {}
    downtrend = stock["downtrend"] = {}

    pdstockdata = data.DataReader(symbol, 'yahoo', '1900-01-01')
    sd = StockDataFrame.retype(pdstockdata)
    sd.BOLL_PERIOD = 15

    close1 = sd['close'][-1]
    close2 = sd['close'][-2]
    low1 = sd['low'][-1]
    low2 = sd['low'][-2]
    high1 = sd['high'][-1]
    high2 = sd['high'][-2]
    avg_30d = sd['close_30_sma'][-1]
    avg_4w = sd['close_20_sma'][-1]
    avg_10w = sd['close_50_sma'][-1]
    avg_30w = sd['close_150_sma'][-1]
    high_52w = sd['high'].tail(250).max()
    lbb1 = sd['boll_lb'][-1]
    lbb2 = sd['boll_lb'][-2]
    ubb1 = sd['boll_ub'][-1]
    ubb2 = sd['boll_ub'][-2]

    # Find all GLTs (ATH not broken for at least another 90 days)
    last_ath = 0.0
    ath = Series()
    for day,day_high in sd['high'].iteritems():
        last_ath = max(last_ath, day_high)
        ath.set_value(day,last_ath)
    ath_days = sd[sd['high'] == ath]['high']
    glt = Series()
    for i,(day,high) in enumerate(ath_days.iteritems()):
        next_day = ath_days.keys()[i+1] if i < len(ath_days)-1 else Timestamp(str(date.today()))
        if next_day - day >= Timedelta('90 days'):
            glt.set_value(day, high)

    uptrend["c>30d_avg"] = close1 > avg_30d
    uptrend["c>10w_avg"] = close1 > avg_10w
    uptrend["c>30w_avg"] = close1 > avg_30w
    uptrend["4w>10w>30w"] = avg_4w > avg_10w > avg_30w
    # uptrend["w_rwb"] =
    uptrend["last_glt_date"] = glt.keys()[-1].to_datetime().date() if len(glt) > 0 else None
    uptrend["last_glt_high"] = glt[-1] if len(glt) > 0 else None
    uptrend["above_last_glt"] = len(glt) > 0 and close1 > glt[-1]
    uptrend["macd_hist_rising"] = sd['macdh'][-1] > sd['macdh_4_sma'][-1]
    uptrend["stoch_fast>slow"] = sd['rsv_10_4_sma'][-1] > sd['rsv_10_4_sma_4_sma'][-1]
    # uptrend["bb_up_expansion_l2"]
    # uptrend["rs>30d_avg"] = (Need Investors.com data)
    # uptrend["rs_rising"] = (Need Investors.com data)
    uptrend["52w_high_l2"] = high_52w == high1 or high_52w == high2
    uptrend["ath_l2"] = ath[-1] == high1 or ath[-2] == high2
    uptrend["1y_doubled"] = close1 >= 2*sd['close'][-255:-245].mean()
    # uptrend["bounce_30d_l2"] =
    # uptrend["bounce_10w_l2"] =
    # uptrend["bounce_30w_l2"] =
    uptrend["stoch<50"] = sd['rsv_10_4_sma'][-1] < 50
    uptrend["<bb_lower_l2"] = low1 < lbb1 or low2 < lbb2
    uptrend["above_avg_volume"] = sd['volume'][-1] > 1.5*sd['volume_50_sma'][-1]

    downtrend["c<30d_avg"] = close1 < avg_30d
    downtrend["c<10w_avg"] = close1 < avg_10w
    downtrend["c<30w_avg"] = close1 < avg_30w
    downtrend["4w<10w<30w"] = avg_4w < avg_10w < avg_30w
    # downtrend["w_bwr"] =
    downtrend["macd_hist_falling"] = sd['macdh'][-1] < sd['macdh_4_sma'][-1]
    downtrend["stoch_fast<slow"] = sd['rsv_10_4_sma'][-1] < sd['rsv_10_4_sma_4_sma'][-1]
    # downtrend["bb_down_expansion_l2"]
    # downtrend["bounce_30d_l2"] =
    # downtrend["bounce_10w_l2"] =
    # downtrend["bounce_30w_l2"] =
    downtrend["stoch>50"] =sd['rsv_10_4_sma'][-1] > 50
    downtrend[">bb_upper_l2"] = high1 > ubb1 or high2 > ubb2

    return stock

def write_checklist(stock, checklistjson):
    """
    Writes a completed stock checklist to a file in stocks/<stock>_<date>.txt
    """
    assert stock != None and isinstance(stock, str) and len(stock) > 0

    if not os.path.exists('stocks'):
        os.makedirs('stocks')

    # Store the list in an output file, one symbol per line
    filename = "stocks/%s_%s.txt" % (stock, str(date.today()))
    with open(filename, "w") as f:
        pp = pprint.PrettyPrinter(indent=4)
        f.write(pp.pformat(checklistjson))
