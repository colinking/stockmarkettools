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
$ python stocks.py --pulse --pulse_start=01/01/2016 --pulse_dir=pulse
```

#### Complete Stock Checklist

Pulls information on a stock from a variety of sources (Yahoo Finance, IBD, etc.).
```
$ python stocks.py --symbols GOOG
```

#### Download IBD Stock Lists

Downloads a specific stock list from IBD.
```
$ python stocks.py --lists ibd50
```
