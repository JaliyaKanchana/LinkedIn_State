import requests

# The URL where your Flask API is running
api_url = 'http://localhost:5000/scrape'

# Profile URL to be scraped
profile_url = 'https://www.linkedin.com/in/jaliya-kanchana-b1a595210/'

try:
    # The POST request with the profile URL
    response = requests.post(api_url, json={'profile_urls': [profile_url]})
    
    # Print the response from the server
    print(response.json())
except Exception as e:
    print(f"An error occurred: {e}")
