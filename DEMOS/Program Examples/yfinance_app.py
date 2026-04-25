import yfinance as yf

# Get the data
gld = yf.download('GLD', period='5d', progress=False)
gold_futures = yf.download('GC=F', period='5d', progress=False)

# Print raw values to see what we have
print("GLD Close prices:")
print(gld['Close'])
print("\n")

print("Last GLD value:")
last_gld = gld['Close'].iloc[-1]
print(last_gld)
print(type(last_gld))
print("\n")

# Calculate approximate gold price
approx_gold = last_gld * 10
print(f"Approximate gold price per ounce: ${approx_gold}")
print("\n")

print("GC=F Close prices:")
print(gold_futures['Close'])
print("\n")

print("Last GC=F value:")
last_futures = gold_futures['Close'].iloc[-1]
print(f"GC=F shows: ${last_futures}")