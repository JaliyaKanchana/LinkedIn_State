import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import time
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

def scrape_linkedin(profile_url):
    # Load credentials and URLs from your JSON file
    with open('credentials_and_urls.json') as json_file:
        data = json.load(json_file)

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--headless")  # Run in headless mode

    # Setup WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Login to LinkedIn
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)  # Ensure the page has loaded
    driver.find_element(By.ID, "username").send_keys(data["login_credentials"]["username"])
    driver.find_element(By.ID, "password").send_keys(data["login_credentials"]["password"])
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    time.sleep(2)  # Wait for login to complete

    # Navigate to the specified profile URL
    driver.get(profile_url)
    time.sleep(5)  # Wait for the profile page to load

    # Now perform the scraping...
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Example: Extracting the name of the profile
    name_loc = soup.find('h1')
    name = name_loc.text.strip() if name_loc else 'Name not found'

    # Close the driver
    driver.quit()

    # Return the scraped data
    return {'Name': name}
