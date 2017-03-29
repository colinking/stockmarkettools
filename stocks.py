import argparse
import pdb
import os
import requests
from datetime import timedelta,date,datetime
from stock_list import load_list,write_stocklist,stocklists
from stock_checklist import checklist,write_checklist
from marketpulse import download_pulse_range

def _ibd_session(username, password):
    """
    Logs in to IBD and returns a new session
    """
    s = requests.Session()
    login_json = { "strEmail": username, "strPassword": password,"blnRemember":False }
    s.post('https://myibd.investors.com/Services/SiteAjaxService.asmx/MemberSingIn', json=login_json)
    print "Initialized IBD Session for %s" % username
    return s

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command center for running stock market tooling scripts')
    parser.add_argument('--lists', help='IBD Stock list to download', choices=['all']+stocklists, nargs='*')
    parser.add_argument('--symbols', help='Runs stock checklist on given stock symbols', nargs='*')
    parser.add_argument('--pulse', help='Downloads the Market Pulse PNG file for each day since pulse_start', action='store_true')
    parser.add_argument('--pulse_start', help='Inclusive start date for downloading Market Pulse PNG files (MM/DD/YYYY) (default: yesterday)', default=date.today()-timedelta(days=1), type=lambda d: datetime.strptime(d, '%m/%d/%Y').date())
    parser.add_argument('--pulse_dir', help='Directory to store Market Pulse PNG files (default: \'./pulse\')', default='pulse')
    # --market
    args = parser.parse_args()

    needs_ibd = args.symbols or args.lists

    if needs_ibd:
        # Initialize an IBD Session
        assert os.environ["IBD_USERNAME"] is not None
        assert os.environ["IBD_PASSWORD"] is not None
        ibd_session = _ibd_session(os.environ["IBD_USERNAME"], os.environ["IBD_PASSWORD"])

    # Download each stock list from IBD
    if args.lists:
        if 'all' in args.lists:
            args.lists = stocklists
        for listname in args.lists:
            stocklist = load_list(listname, ibd_session)
            write_stocklist(stocklist, listname)
            print "Downloaded %s for %s" % (listname, date.today())

    # Fill out a Stock Checklist for each symbol
    if args.symbols:
        ibd50_list = load_list('ibd50', ibd_session)
        for symbol in args.symbols:
            stockchecklist = checklist(symbol, ibd50_list, ibd_session)
            write_checklist(symbol, stockchecklist)
            print "Completed stock checklist for %s on %s" % (symbol, date.today())

    if args.pulse:
        download_pulse_range(args.pulse_start, date.today(), args.pulse_dir)

    if needs_ibd:
        ibd_session.close()
