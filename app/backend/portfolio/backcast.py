from pandas import DataFrame
from sklearn.linear_model import LinearRegression

class Backcast:
    def __init__(self, df_asset: DataFrame, df_reference: DataFrame):
        self.df_asset = self._load_data(df_asset, "asset")
        self.df_reference = self._load_data(df_reference, "reference")
    
    def _load_data(df: DataFrame, column_name):
            df = df.copy()
            df[column_name] = df["Value"]    
            df[column_name + "_pct"] = df[column_name].pct_change()
            return df[["Date", column_name, column_name + "_pct"]]
    
    def run(self):
        df_full = self.df_reference.merge(self.df_asset, how="left", on="Date")
        df_full.dropna(subset=["reference_pct"], inplace=True)

        model = self._train_model(df_full)

        df_full = self._predict_asset_pct(df_full, model)

        initial_asset_value = self._get_first_asset_value(df_full)

        df_backcast = df_full.copy()
        df_backcast = df_backcast[df_backcast["asset"].isna()]
        df_backcast = df_backcast.sort_values(by="Date", ascending=False)
        df_backcast["asset_pct_pred_inv"] = 1/(1+df_backcast["asset_pct_pred"]) - 1
        df_backcast['asset_backcast'] = initial_asset_value * (1 + df_backcast['asset_pct_pred_inv']).cumprod()
        df_backcast = df_backcast[["asset_backcast"]]
        print(df_backcast)


        df_full = df_full.merge(df_backcast, how="left", on="Date")


        import matplotlib.pyplot as plt
        plt.plot(df_full["asset"], label="original")
        plt.plot(df_full["asset_backcast"], label="backcast")
        plt.legend()
        plt.show()
    

    def _train_model(self, df_full: DataFrame) -> LinearRegression:
        df_train = df_full.copy()
        df_train.dropna(inplace=True)

        X = df_train["reference_pct"].to_numpy().reshape(-1, 1)
        Y = df_train["asset_pct"].to_numpy()

        model = LinearRegression().fit(X, Y)
        print("The model score is: ", model.score(X, Y))
        return model
    
    def _predict_asset_pct(self, df_full: DataFrame, model: LinearRegression) -> DataFrame:    
        X_ref = df_full["reference_pct"].to_numpy().reshape(-1, 1)
        Y_asset = model.predict(X_ref)
        df_full["asset_pct_pred"] = Y_asset
        return df_full

    def _get_first_asset_value(df_full: DataFrame) -> float:
        df_check = df_full.copy()
        df_check.dropna(subset=["asset"], inplace=True)
        return df_check["asset"].iloc[0]



