import sys
from yahooquery import Ticker

def check_options():
    tk = Ticker("AAPL")
    df = tk.option_chain
    if type(df) is dict:
        print("Dict returned")
    else:
        print("Columns:", df.columns.tolist())
        print("Index names:", df.index.names)
        
        # Check actual values to verify casing
        print("\nSample Data:")
        # Reset index to see how it flattens
        flat_df = df.reset_index()
        print("Flattened Columns:", flat_df.columns.tolist())
        print(flat_df[['expiration', 'optionType', 'strike', 'bid', 'ask']].head(2).to_string())

if __name__ == "__main__":
    check_options()
