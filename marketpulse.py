#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import requests
import shutil
import os
from datetime import timedelta, date, datetime
from pandas.tseries.holiday import USFederalHolidayCalendar as calendar

def _daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

# Odd image URLs:
# http://www.investors.com/wp-content/uploads/2017/03/MP4-3_030717.png
# http://www.investors.com/wp-content/uploads/2017/03/MP4-3_030617.png
# http://www.investors.com/wp-content/uploads/2017/02/MP_5nas_022317.png
def _download_pulse(date, directory):
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

def download_pulse_range(start, end, pulsedir):
    cal = calendar()

    if not os.path.exists(pulsedir):
        os.makedirs(pulsedir)

    for day in _daterange(start, end):
        if day.weekday() < 5: # Monday...Friday == 0..4
            if day in cal.holidays():
                print u'(Holiday)...',
            _download_pulse(day, pulsedir)
        else:
            print u'%s (Weekend)' % str(day)
