########################## Imported libraries ##########################
import pandas as pd
import urllib.request
import json
import time
import os
pd.set_option('display.float_format', lambda x: '%.8f' % x)

########################## Utility functions ##########################
# Rounding function (2 decimals)
def rounding(n):
    return int(n*100)/100

# getPrices() gets the latest price data from Binance API
def getPrices():
    openUrl = urllib.request.urlopen('https://api.binance.com/api/v3/ticker/24hr')
    data = openUrl.read()
    jsonData = json.loads(data)
    
    binanceData = pd.DataFrame(columns=['Pair', 'CurrentPrice'])
    for i in range(len(jsonData)):
        binanceData = binanceData.append({'Pair': jsonData[i]['symbol'], 'CurrentPrice': jsonData[i]['lastPrice']}, ignore_index=True)

    return binanceData




########################## Data analysis ###########################
path =os.path.dirname(os.path.realpath(__file__))
path = os.path.join(path,'myOrders.csv')
myOrders = pd.read_csv(path)
myOrders = myOrders[::-1]
myOrders = myOrders[(myOrders['Status'].isin(['FILLED', 'PARTIALLY_FILLED'])) & (myOrders['Pair'].str.contains('BTC')) & \
    (myOrders['Pair']!='BTCEUR') & (myOrders['Pair']!='BTCUSDT')].reset_index(drop=True)

while True:
    binanceData = getPrices()
    tableAlts = pd.DataFrame(float(0),index=myOrders['Pair'].unique(), columns=['Num Altcoin', 'Invested BTC', 'Current BTC', 'Gained BTC', \
        'Gained %', 'Avg Price', 'Last Purchasing Price', 'Last Selling Price', 'Current Price', 'Consolidated Gains']).astype(float)
    tableAlts['Gained %'] = tableAlts['Gained %'].astype(str)

    for _, row in myOrders.iterrows():
        orderBTC = float(row['Trading total'][0:12].replace(',',''))
        orderAlt = float(row['Executed'][0:12].replace(',',''))
        priceAlt = float(binanceData[binanceData['Pair']==row['Pair']].reset_index(drop=True)['CurrentPrice'])
        tableAlts.at[row['Pair'], 'Current Price'] = priceAlt


        if row['Side']=='BUY':
            tableAlts.at[row['Pair'], 'Num Altcoin'] = tableAlts['Num Altcoin'][row['Pair']]  + orderAlt
            tableAlts.at[row['Pair'], 'Invested BTC'] = tableAlts['Invested BTC'][row['Pair']] + orderBTC

            tableAlts.at[row['Pair'], 'Current BTC'] = priceAlt * tableAlts['Num Altcoin'][row['Pair']]
            tableAlts.at[row['Pair'], 'Gained BTC'] = tableAlts['Current BTC'][row['Pair']] - tableAlts['Invested BTC'][row['Pair']]
            tableAlts.at[row['Pair'], 'Gained %'] = str(rounding(100*tableAlts['Gained BTC'][row['Pair']] / tableAlts['Invested BTC'][row['Pair']])) + ' %'
            tableAlts.at[row['Pair'], 'Avg Price'] = tableAlts['Invested BTC'][row['Pair']] / tableAlts['Num Altcoin'][row['Pair']]
            tableAlts.at[row['Pair'], 'Last Purchasing Price'] = orderBTC / orderAlt
                                            
            
        elif row['Side']=='SELL':
            ratioAlt = orderAlt / tableAlts['Num Altcoin'][row['Pair']]
            tableAlts.at[row['Pair'], 'Consolidated Gains'] = tableAlts['Consolidated Gains'][row['Pair']] + orderBTC - ratioAlt*tableAlts['Invested BTC'][row['Pair']]

            tableAlts.at[row['Pair'], 'Num Altcoin'] = tableAlts['Num Altcoin'][row['Pair']]  - orderAlt
            tableAlts.at[row['Pair'], 'Invested BTC'] = tableAlts['Invested BTC'][row['Pair']] - ratioAlt*tableAlts['Invested BTC'][row['Pair']]

            tableAlts.at[row['Pair'], 'Current BTC'] = priceAlt * tableAlts['Num Altcoin'][row['Pair']]
            tableAlts.at[row['Pair'], 'Gained BTC'] = tableAlts['Current BTC'][row['Pair']] - tableAlts['Invested BTC'][row['Pair']]
            tableAlts.at[row['Pair'], 'Last Selling Price'] = orderBTC / orderAlt
           

    tableAlts.dropna(inplace=True)

    os.system('clear')
    print("\n**************************************** CryptoBoard ****************************************")
    print('BTC Price: %.0f EUR / %.0f USD' %(float(binanceData[binanceData['Pair']=='BTCEUR']['CurrentPrice']), \
        float(binanceData[binanceData['Pair']=='BTCUSDT']['CurrentPrice'])))
    print('Invested BTC: %.4f BTC - Current BTC: %.4f BTC - Current gains: %.4f BTC - Current gain: %.2f' \
        %(tableAlts['Invested BTC'].sum(), \
        tableAlts['Current BTC'].sum(), \
        tableAlts['Gained BTC'].sum(),  \
        100*tableAlts['Gained BTC'].sum()/tableAlts['Invested BTC'].sum()) + ' %') 
    print('Consolidated BTC: %.4f BTC\n' %(tableAlts['Consolidated Gains'].sum()))

    tableAlts = tableAlts.drop(tableAlts[tableAlts['Invested BTC']<10/float(binanceData[binanceData['Pair']=='BTCEUR']['CurrentPrice'])].index)
    printedTable = tableAlts.filter(['Invested BTC', 'Current BTC', 'Avg Price' ,'Current Price', 'Gained BTC', 'Gained %'], axis=1)
    printedTable = printedTable.sort_values(by='Invested BTC', ascending=False)
    print(printedTable)

    print('\nLast updated at {last_update}'.format(last_update = time.strftime("%m/%d/%Y %H:%M:%S",time.localtime())))

    time.sleep(60)