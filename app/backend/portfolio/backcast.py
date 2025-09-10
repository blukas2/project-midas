from pandas import DataFrame
import pandas as pd
from yfinance import Ticker
import numpy as np
from sklearn.linear_model import LinearRegression

import matplotlib.pyplot as plt


class Backcast:
    def __init__(self, df_asset: DataFrame, df_reference: DataFrame):
        self.df_asset_orig = df_asset
        self.df_asset = self._load_data(df_asset, "asset")
        self.df_reference = self._load_data(df_reference, "reference")

    def _load_data(self, df: DataFrame, column_name):
            df = df.copy()
            df[column_name] = df["Value"]    
            df[column_name + "_pct"] = df[column_name].pct_change()
            #df.set_index("Date", inplace=True, drop=True)
            #return df[[column_name, column_name + "_pct"]]
            return df[["Date", column_name, column_name + "_pct"]]
    
    def run(self):
        df_full = self.df_reference.merge(self.df_asset, how="left", on="Date")
        df_full.dropna(subset=["reference_pct"], inplace=True)

        model, score = self._train_model(df_full)

        df_full = self._predict_asset_pct(df_full, model, score)

        initial_asset_value = self._get_first_asset_value(df_full)

        df_backcast = df_full.copy()
        df_backcast = df_backcast[df_backcast["asset"].isna()]
        df_backcast = df_backcast.sort_values(by="Date", ascending=False)
        df_backcast["asset_pct_pred_inv"] = 1/(1+df_backcast["asset_pct_pred"]) - 1
        df_backcast['asset_backcast'] = initial_asset_value * (1 + df_backcast['asset_pct_pred_inv']).cumprod()
        
        #plt.plot(df_backcast["asset_backcast"], label="backcast")
        #plt.plot(df_backcast["asset"], label="original")                
        ##plt.xticks(ticks=range(0, len(df_asset), len(df_asset)//10), labels=df_asset["Date"].iloc[::len(df_asset)//10], rotation=45)
        #plt.legend()
        #plt.show()
        
        
        df_backcast = df_backcast[["Date", "asset_backcast"]]
        
        self.df_asset_orig = self.df_asset_orig.merge(df_backcast, how="outer", on="Date")

        
        self.df_asset_orig["Value"] = np.where(
             self.df_asset_orig["Value"].isna(), self.df_asset_orig["asset_backcast"], self.df_asset_orig["Value"]
        )
        self.df_asset_orig.drop(columns=["asset_backcast"], inplace=True)
        self.df_asset_orig.sort_values(by="Date", ascending=True, inplace=True)
        self.df_asset_orig.reset_index(drop=True, inplace=True)

        return self.df_asset_orig

    def _train_model(self, df_full: DataFrame) -> tuple[LinearRegression, float]:
        df_train = df_full.copy()
        df_train.dropna(inplace=True)

        X = df_train["reference_pct"].to_numpy().reshape(-1, 1)
        Y = df_train["asset_pct"].to_numpy()

        model = LinearRegression().fit(X, Y)
        model_score = model.score(X, Y)
        print("The model score is: ", model_score)
        return model, model_score

    def _predict_asset_pct(self, df_full: DataFrame, model: LinearRegression, score: float) -> DataFrame:    
        if score > 0.5:
            X_ref = df_full["reference_pct"].to_numpy().reshape(-1, 1)
            Y_asset = model.predict(X_ref)
            df_full["asset_pct_pred"] = Y_asset
        else:
            print("The model score is too low to make predictions automatically taking defult values...")
            df_full["asset_pct_pred"] = df_full["reference_pct"]
        return df_full

    def _get_first_asset_value(self, df_full: DataFrame) -> float:
        df_check = df_full.copy()
        df_check.dropna(subset=["asset"], inplace=True)
        return df_check["asset"].iloc[0]



# Backcasted VUAA.DE with reference asset ^GSPC

#Reference asset for XDWD.DE is ^GSPC

#def load(ticker_name: str, period: str):
#    ticker = Ticker(ticker_name)
#    df = ticker.history(period=period)
#    df["Value"] = df["Close"]
#    df.reset_index(inplace=True)
#    df['Date'] = pd.to_datetime(df['Date']).dt.date
#    return df
#
##df_asset = load(ticker_name="LYP6.DE", period="5y")
##df_reference = load(ticker_name="^STOXX", period="5y")
#
#df_asset = load(ticker_name="VUAA.DE", period="5y")
#df_reference = load(ticker_name="^GSPC", period="5y")
#
##df_asset = load(ticker_name="XDWD.DE", period="5y")
##df_reference = load(ticker_name="^GSPC", period="5y")
#
##print(df_asset)
##print(df_reference)
#
#
#backcast = Backcast(df_asset, df_reference)
#
#df_asset = backcast.run()
#
#print(df_asset)
#


##plt.plot(df_asset["Value"], label="original")
#plt.xticks(ticks=range(0, len(df_asset), len(df_asset)//10), labels=df_asset["Date"].iloc[::len(df_asset)//10], rotation=45)
#plt.legend()
#plt.show()
