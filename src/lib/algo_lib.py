import pandas as pd
import pandas as pd
from datetime import datetime as dt
from datetime import timedelta

from talib import MACD, MACDEXT, RSI, BBANDS, MACD, AROON, STOCHF, ATR, OBV, ADOSC, MINUS_DI, PLUS_DI, ADX, EMA, SMA
from talib import LINEARREG, BETA, LINEARREG_INTERCEPT, LINEARREG_SLOPE, STDDEV, TSF, ADOSC, VAR, ROC, MIN, MAX, MINMAX
#from talib import CDLABANDONEDBABY, CDL3BLACKCROWS,CDLDOJI, CDLDOJISTAR, CDLDRAGONFLYDOJI,CDLENGULFING,CDLEVENINGDOJISTAR,CDLEVENINGSTAR, CDLGRAVESTONEDOJI, CDLHAMMER, CDLHANGINGMAN,CDLHARAMI,CDLHARAMICROSS,CDLINVERTEDHAMMER,CDLMARUBOZU,CDLMORNINGDOJISTAR,CDLMORNINGSTAR,CDLSHOOTINGSTAR,CDLSPINNINGTOP,CDL3BLACKCROWS, CDL3LINESTRIKE, CDLKICKING
from lib.logging_lib import pdebug, pdebug1, pdebug5, perror, pinfo, cache_type, pdebug7

# ====== Tradescript Wrapper =======
# Methods


#Heikin Asi
def HAIKINASI(ohlc_data_df):
    REF = lambda key, i: ohlc_get(ohlc_data_df.shift(i), key)
    
    OPEN  = ohlc_data_df['open']
    HIGH  = ohlc_data_df['high']
    LOW   = ohlc_data_df['low']
    CLOSE = ohlc_data_df['close']
    
    haOPEN  = (OPEN.shift(1) + CLOSE.shift(1))/2
    haHIGH  = pd.DataFrame([HIGH,OPEN,CLOSE]).max(axis = 0, skipna = True)
    haLOW   = pd.DataFrame([LOW,OPEN,CLOSE]).min(axis = 0, skipna = True)
    haCLOSE = (OPEN+HIGH+LOW+CLOSE)/4
    
    return (haOPEN, haHIGH, haLOW, haCLOSE)

ohlc_get = lambda df, key: df.iloc[-1][key]
#REF = lambda df, i: df.iloc[-i-1]


def order_details(cache, key, decision = 'WAIT', x2 = -1, qty=-1, sl=-1, tp=-1):
    cache.set('decision'+cache_type,decision)


def myalgo(cache, key, ohlc_data_df, algo=None, state='SCANNING', quick=False): 
    pdebug7('myalgo {}'.format(key))

    if quick == False:
        ohlc_data_temp = ohlc_data_df.tail(51).head(50) #to reduce calculation load, remove last candle
    else:
        ohlc_data_temp = ohlc_data_df

    OPEN = ohlc_data_temp['open']
    CLOSE = ohlc_data_temp['close']
    HIGH = ohlc_data_temp['high']
    LOW = ohlc_data_temp['low']
    #VOLUME = ohlc_data_temp['volume']
    
    (haOPEN, haHIGH, haLOW, haCLOSE) = HAIKINASI(ohlc_data_temp)
 
    TIME = ohlc_data_temp.index.minute+ohlc_data_temp.index.hour*60
    
    REF = lambda df, i: df.shift(i)
    TREND_UP = lambda a,b=3: ROC(a, b) > 0.1
    TREND_DOWN = lambda a,b=3: ROC(a, b) < -0.1
    CROSSOVER = lambda a, b: (REF(a,1)<=REF(b,1)) & (a > b)
    sell = pd.DataFrame()
    buy = pd.DataFrame()
    
    BUY = lambda qty=-1, sl=-1, tp=-1, x2 = -1:order_details(cache, key, 'BUY', x2, qty, sl, tp)
    SELL = lambda qty=-1, sl=-1, tp=-1, x2 = -1:order_details(cache, key, 'SELL', x2, qty, sl, tp)
    WAIT = lambda : order_details(cache, key, 'WAIT')
    def update_decision(buy, sell):
        #pinfo(buy.index)
        cache.set('buy_df',buy.to_json(orient='index'))
        cache.set('sell_df',sell.to_json(orient='index'))
        #buy1 = buy.copy(deep=True)
        #sell1 = sell.copy(deep=True)
        try:
            if buy[-1] == True:
                BUY()
            elif sell[-1] == True:
                SELL()
            else:
                WAIT()
        except:
            WAIT()

    decision = 'WAIT'
    cache.set('decision'+cache_type,decision)
   
    try:
        if algo != '' and algo is not None:

            postfix = "update_decision(buy, sell)"
            code = algo + '\n'+ postfix

            exec(code)
            
        else:
            sell = (REF(haOPEN, 0) > REF(haCLOSE,0)) & (REF(haOPEN, 1) < REF(haCLOSE,1))
            buy = (REF(haOPEN, 0) < REF(haCLOSE,0)) & (REF(haOPEN, 1) > REF(haCLOSE,1))
            update_decision(buy, sell)
        
        decision = cache.get('decision'+cache_type)
    except:
        perror("Error in executing algorithm")

    if quick == False:
        #pinfo(decision)
        return decision #"BUY"|"SELL"
    else:
        buy = pd.read_json(cache.get('buy_df'), orient='index')
        sell = pd.read_json(cache.get('sell_df'), orient='index')
        #pinfo(buy)
        return buy[0].values, sell[0].values