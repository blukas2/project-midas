from yfinance import Ticker
from sklearn.linear_model import LinearRegression

# Steps:
# 1. Load data for two assets
# 2. Calculate percentage change for all columns
# 3. Train a linear regression model to predict one asset based on the other
# 4. Backcast the asset value based on the reference asset


ticker_name = "LYP6.DE"
column_name = "lyp6de"
def load_asset_data(ticker_name, column_name, period="1y"):
    ticker = Ticker(ticker_name)
    df = ticker.history(period=period)
    df[column_name] = df["Close"]    
    df[column_name + "_pct"] = df[column_name].pct_change()
    return df[[column_name, column_name + "_pct"]]


df_asset = load_asset_data(ticker_name="LYP6.DE", column_name="asset", period="6mo")
df_reference = load_asset_data(ticker_name="^STOXX", column_name="reference", period="1y")

df_full = df_reference.merge(df_asset, how="left", on="Date")

df_train = df_full.copy()
df_train.dropna(inplace=True)

print(df_train)

X = df_train["reference_pct"].to_numpy().reshape(-1, 1)
Y = df_train["asset_pct"].to_numpy()

model = LinearRegression().fit(X, Y)
Y_pred = model.predict(X)
print(model.get_params())
print(model.score(X, Y))

df_train["asset_pct_pred"] = Y_pred



# plot lyp6de and lyp6de_pred as two time series
import matplotlib.pyplot as plt
plt.plot(df_train["asset_pct"], label="lyp6de")
plt.plot(df_train["asset_pct_pred"], label="lyp6de_pred")
plt.legend()
plt.show()


#ticker_stoxx = Ticker("LYP6.DE")
#df_stoxx = ticker_stoxx.history()  

