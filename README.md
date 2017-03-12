# stockmarkettools
Stock market research tool for assessing individual stocks and the overall market trend

## Setup

```
$ virtualenv stockmarkettools
```

## Tools

#### Download Market Pulses

Downloads Market Pulse images from [Investors.com](http://www.investors.com).

```
$ python marketpulse.py --start_date=01/01/2016 --dir=pulse
```

#### Complete Stock Checklist

Pulls information on a stock from a variety of sources (Yahoo Finance, IBD, etc.).
```
$ python stock_checklist.py GOOG
```
