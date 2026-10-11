# Project Midas

Project Midas is a Python desktop application for exploring investment portfolios. It retrieves market data with Yahoo Finance, converts values to EUR, and provides portfolio and asset analysis.

## Features

- Create, open, and save portfolios of stocks and ETFs.
- View portfolio value history, returns, annualized returns, volatility, and asset correlations.
- Analyze risk and performance, including Sharpe ratio, drawdown, beta, alpha, value at risk, and diversification measures.
- Search for assets and compare assets side by side.
- View asset and portfolio history in EUR.
- Follow the operating system appearance by default, with a light/dark theme toggle and themed dialogs.

Market data availability and accuracy depend on Yahoo Finance and your internet connection. This application is for informational purposes only; it is not financial advice.

## Requirements

- Python 3.10 or newer.
- A working Tkinter installation.
- CustomTkinter (installed with the project dependencies).
- Internet access for market data and asset search.

## Setup

1. Clone the repository and open a terminal in its root directory.
2. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   On macOS or Linux, activate it with:

   ```sh
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```sh
   python -m pip install -r requirements.txt
   ```

4. Configure the application data directory in `app/backend/globals/location.py`. Set `ROOT_FOLDER` to a directory on your computer where the app can read and save portfolio data. The default value points to a machine-specific path and will not exist on most computers.
5. Create a `portfolios` directory inside `ROOT_FOLDER`. The app stores saved custom portfolios there.

To load imported portfolios, the data directory must also contain portfolio subdirectories with dated source CSV files, plus an `asset_names.csv` ticker mapping file. The source files are expected to be semicolon-delimited; portfolio CSVs use UTF-16 encoding and the headers `ISIN`, `Titel`, and `Menge`. The ticker mapping CSV is expected to use ISO-8859-1 encoding and include `isin` and `ticker` columns. You can use the app with newly created portfolios without importing these source files.

## Run

From the repository root:

```powershell
python app\app.py
```

The app opens a desktop window with **Portfolio**, **Assets**, and **Analysis** dropdowns in the top bar. Use **Portfolio > New** to create a portfolio, **Assets > Find Asset...** to search for a ticker, and the portfolio controls to add positions and recalculate. Use **Portfolio > Save** to save a custom portfolio. **Portfolio > Open** lists portfolios found in the configured data directory; **Analysis > Compare** opens asset comparison. Use **Theme** in the top bar to switch between light and dark appearance.

Market data requests require an internet connection and may take time or fail when the data provider is unavailable.

## Tests

Install the project dependencies, then run the test suite from the repository root:

```sh
python -m pytest
```

## Project layout

```text
app/
  app.py                 Application entry point
  backend/               Portfolio data, market-data, and analysis logic
  ui/                    CustomTkinter windows, themed dialogs, and charts
tests/                   Backend, UI, and application tests
research/                Project analysis notes
requirements.txt         Python dependencies
```
