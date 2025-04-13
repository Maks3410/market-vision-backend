from polygon import RESTClient
from .models import Fixing

polygon_client = RESTClient(api_key='HDarpSe1VjbNVodWFDgf1kop6Kw60KoN', trace=True)

aggs = []
for a in polygon_client.list_aggs(ticker="AAPL", multiplier=1, timespan="day", from_="2020-01-01", to="2023-06-13", limit=50000):
    aggs.append(a.close)

print(aggs)

def get_ticker_fixings(index, from_, to):

    isin = index.indexISIN
    fixings = []

    for a in polygon_client.list_aggs(ticker=isin, multiplier=1, timespan="day", from_=from_, to=to):
        fixings.append(Fixing(
            fixingDate=a.date
        ))