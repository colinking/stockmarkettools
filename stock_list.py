from collections import defaultdict
from datetime import date
import requests
import json
import os

cache = defaultdict(dict)
stocklists = ['ibd50','canslim','sectorleaders','spotlight','bigcap','newhigh','relstrnewhighs','funds','ipos','global','risingprofits']

def _load_page(url, session):
    assert session != None
    assert url != None
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    page = session.get(url, headers=headers)
    return page

def _stocks(url, session):
    stock_page = _load_page(url, session)
    stocks = [stock["Symbol"] for stock in json.loads(stock_page.text)["d"]["ETablesDataList"]]
    return stocks

def load_list(listname, session):
    today = date.today()
    if today in cache[listname]: return cache[listname][today]

    stocklist = None
    if listname == 'ibd50': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetIBD50?sortcolumn1=%22ibd100rank%22&sortOrder1=%22asc%22&sortcolumn2=%22%22&sortOrder2=%22ASC%22', session)
    elif listname == 'canslim': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetCanslimSelect?sortcolumn1=%22comprating%22&sortOrder1=%22desc%22&sortcolumn2=%22symbol%22&sortOrder2=%22ASC%22', session)
    elif listname == 'sectorleaders': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetSectorLeaders?sortcolumn1=%22sectorrank%22&sortOrder1=%22asc%22&sortcolumn2=%22symbol%22&sortOrder2=%22Asc%22', session)
    elif listname == 'spotlight': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetStockSpotlight?sortcolumn1=%22comprating%22&sortOrder1=%22desc%22&sortcolumn2=%22%22&sortOrder2=%22ASC%22', session)
    elif listname == 'bigcap': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetBigCap20?sortcolumn1=%22ibd100rank%22&sortOrder1=%22asc%22&sortcolumn2=%22%22&sortOrder2=%22ASC%22', session)
    elif listname == 'newhigh': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetNewHigh?sortcolumn1=%22comprating%22&sortOrder1=%22desc%22&sortcolumn2=%22symbol%22&sortOrder2=%22ASC%22', session)
    elif listname == 'relstrnewhighs': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetBoltingRSLines?sortcolumn1=%22rsrating%22&sortOrder1=%22desc%22&sortcolumn2=%22symbol%22&sortOrder2=%22ASC%22', session)
    elif listname == 'funds': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetAccelMFOwnership?sortcolumn1=%22nofunds%22&sortOrder1=%22desc%22&sortcolumn2=%22symbol%22&sortOrder2=%22ASC%22', session)
    elif listname == 'ipos': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetIPOLeaders?sortcolumn1=%22comprating%22&sortOrder1=%22desc%22&sortcolumn2=%22symbol%22&sortOrder2=%22ASC%22', session)
    elif listname == 'global': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetGlobalLeaders?sortcolumn1=%22rank%22&sortOrder1=%22asc%22&sortcolumn2=%22CompRating%22&sortOrder2=%22ASC%22', session)
    elif listname == 'risingprofits': stocklist = _stocks('http://research.investors.com/Services/SiteAjaxService.asmx/GetLeadersRisingEstimates?sortcolumn1=%22comprating%22&sortOrder1=%22desc%22&sortcolumn2=%22symbol%22&sortOrder2=%22ASC%22', session)
    else: raise Exception('Unknown stocklist: %s' % listname)

    cache[listname][today] = stocklist
    return stocklist

def write_stocklist(stocklist, listname):
    """
    Writes a list of stocks to a file in lists/<listname>/<date>.txt
    """
    assert isinstance(stocklist, list)
    assert listname != None and isinstance(listname, str) and len(listname) > 0

    if not os.path.exists('lists/%s' % listname):
        os.makedirs('lists/%s' % listname)

    # Store the list in an output file, one symbol per line
    filename = "lists/%s/%s.txt" % (listname, str(date.today()))
    with open(filename, "w") as f:
        for symbol in stocklist:
            f.write(symbol + "\n")
