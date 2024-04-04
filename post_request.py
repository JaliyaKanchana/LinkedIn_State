import requests

# The URL where your Flask API is running
api_url = 'http://localhost:5000/scrape'

# Profile URLs to be scraped (as a list)
profile_urls = ['https://www.linkedin.com/in/jaliya-kanchana-b1a595210/']

# Send a POST request with the profile URLs
response = requests.post(api_url, json={'profile_urls': profile_urls})

# Print the response
print(response.json())
