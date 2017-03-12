#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import requests
import shutil
import os
from datetime import timedelta, date, datetime
import holidays

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

# http://www.investors.com/wp-content/uploads/2017/03/MP4-3_030717.png
# http://www.investors.com/wp-content/uploads/2017/03/MP4-3_030617.png
# http://www.investors.com/wp-content/uploads/2017/02/MP_5nas_022317.png
def download_pulse(date, directory):
    """
    Downloads the daily Market Pulse image from Investors.com's Big Picture
    section.
    """
    def download_image(url):
        filename = os.path.join(directory, date.strftime("%Y.%m.%d.png"))
        # Check if MP already downloaded
        if os.path.exists(filename):
            return True
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
        return r.status_code == 200

    raw_pulse_url = 'http://www.investors.com/wp-content/uploads/%d/%02d/MP%02d%02d%02d.png'
    pulse_url = raw_pulse_url % (date.year, date.month, date.month, date.day, date.year % 100)
    alt_raw_pulse_url = 'http://www.investors.com/wp-content/uploads/%d/%02d/MP4-3_%02d%02d%02d.png'
    alt_pulse_url = alt_raw_pulse_url % (date.year, date.month, date.month, date.day, date.year % 100)

    if download_image(pulse_url) or download_image(alt_pulse_url):
        print u'%s ✔' % str(date)
    else:
        print u'%s ✖' % str(date)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download Market Pulse from Investors.com')
    parser.add_argument('--dir','-d', default='./pulse', help='output directory for PNGs')
    parser.add_argument('--start_date', '-s', default='./pulse', help='start date for MP scrape date range (MM/DD/YYYY)', type=lambda d: datetime.strptime(d, '%m/%d/%Y').date())
    args = parser.parse_args()

    us_holidays = holidays.US()

    if not os.path.exists(args.dir):
        os.makedirs(args.dir)

    for date in daterange(args.start_date, date.today()):
        if date.weekday() < 5: # Monday...Friday == 0..4
            if date in us_holidays:
                print u'(Holiday)...',
            download_pulse(date, args.dir)
        else:
            print u'%s (Weekend)' % str(date)
