#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
from yahoo_finance import Share
import pdb
import requests
import re
from lxml import html
from bs4 import BeautifulSoup
import os
import json

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

def ibd_session():
    """
    Logs in to IBD and returns a new session
    """
    s = requests.Session()
    s.post('https://myibd.investors.com/Services/SiteAjaxService.asmx/MemberSingIn', json={"strEmail": os.environ["IBD_USERNAME"], "strPassword": os.environ["IBD_PASSWORD"],"blnRemember":False})
    return s

def ibd_stock_checkup(ticker):
    """
    Loads information from Investors.com's IBD Stock Checkup Tool.
    """
    s = ibd_session()
    page = s.get('http://research.investors.com/stockcheckup.aspx?symbol=%s'%ticker)
    s.close()
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
    for i in range(5):
        if composite_rankings[i].text == ticker:
            results["industry_top5"] = i+1
    # Count the green circles
    results["fundamental_greens"] = len(soup.find(id="Fundamentals").find_all('a', class_='passDef', rel='#cluetipPass'))
    results["technical_greens"] = len(soup.find(id="Technicals").find_all('a', class_='passDef', rel='#cluetipPass'))
    return results

def ibd50(out=None):
    """
    Pulls the IBD50 from Investors.com and optionally writes it to a file.
    """
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    s = ibd_session()
    page = s.get('http://research.investors.com/Services/SiteAjaxService.asmx/GetIBD50?sortcolumn1=%22ibd100rank%22&sortOrder1=%22asc%22&sortcolumn2=%22%22&sortOrder2=%22ASC%22', headers=headers)
    s.close()
    # Pull out each symbol
    ibd50 = [stock["Symbol"] for stock in json.loads(page.text)["d"]["ETablesDataList"]]
    if out:
        # Store the list in an output file, one symbol per line (in IBD50 order)
        with open(out,"w") as f:
            for symbol in ibd50:
                f.write(symbol + "\n")
    return ibd50

def stock_checklist(symbol, ibd50_list):
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
    ibd = stock["ibd"] = ibd_stock_checkup(symbol)
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

    # TODO:
    # 30D,10W,30W SMA price
    # RWB plot
    # Most recent Greenline top
    # MACD 12/26/9 histogram
    # Stochastic 10.4, 10.4.4
    # BBD 15.2 upper/middle/lower bands (-> upward/downward expansion)
    # BBD Bounce 30D/10W/30W today/yesterday
    # Current RS v. SPY & 30D SMA RS v. SPY
    # Yesterday's close
    # Close 52W ago
    # Last two lows/highs
    # AVGV50

    return stock

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download Market Pulse from Investors.com')
    parser.add_argument('symbol', help='Stock Symbol')
    args = parser.parse_args()

    if not os.path.exists('ibd50'):
        os.makedirs('ibd50')

    ibd50_list = ibd50(out='ibd50/%s' % datetime.today().strftime("%Y.%m.%d.txt"))

    print stock_checklist(args.symbol, ibd50_list)
