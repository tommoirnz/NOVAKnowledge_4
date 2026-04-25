import requests
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Get the API key
# Worth keeping to test your Brave key
# Ensure you have a .env file with BRAVE_KEY=xxxxxxxxnumber from braveapi
key = os.getenv("BRAVE_KEY", "")

# Make the API request
r = requests.get(
    "https://api.search.brave.com/res/v1/images/search",
    headers={"X-Subscription-Token": key, "Accept": "application/json"},
    params={"q": "Scotland", "count": 5}  # You can increase count for more results
)

if r.status_code == 200:
    data = r.json()
    print(f"Found {len(data.get('results', []))} images")

    # Print first image result
    if data.get('results'):
        first_image = data['results'][0]
        print(f"Title: {first_image.get('title')}")
        print(f"URL: {first_image.get('url')}")
        print(f"Thumbnail: {first_image.get('thumbnail', {}).get('src')}")
else:
    print(f"Error: {r.status_code}")
    print(r.text)