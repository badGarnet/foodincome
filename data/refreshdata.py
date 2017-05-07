import requests
import numpy as np
import pandas as pd

def to_number(s):
    def to_number(s):
        try:
    return np.int64(s)
        except ValueError:
        return 0

def getnycdata(url, sumincomebyzip):
    headers = {'X-App-Token': 'QxER95TdAEH9MulIhECo8BjIi'}
    url = "https://data.cityofnewyork.us/resource/9w7m-hzhe.json"
    payload = {'$select': 'max(camis), max(dba), max(boro), max(building), max(street), max(zipcode), max(cuisine_description)', \
                         '$group': 'camis',
                         '$limit': 100000}
    r = requests.get(url, headers=headers, params=payload)
    aggdata = pd.DataFrame(r.json())
    foodbyzip = pd.DataFrame(aggdata.groupby('max_zipcode').max_boro.agg('count'))
    foodbyzip.index.rename('zipcode', inplace=True)
    foodbyzip.index = foodbyzip.index.map(to_number)
    foodbyzip.columns = ['foodsize']
    df2 = pd.DataFrame(sumincomebyzip)
    df2.columns = ['sumincome']
    return foodbyzip.join(df2, how='left')
