import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup, Comment
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import requests


def driver_init():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(options=chrome_options)

    # Load the credentials and URLs
    with open("credentials_and_urls.json") as json_file:
        data = json.load(json_file)

    # Set up the Chrome driver with options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--incognito")
    driver = webdriver.Chrome(options=chrome_options)

    url = "https://www.linkedin.com/login"
    driver.get(url)
    time.sleep(2)
    username = data["login_credentials"]["username"]
    password = data["login_credentials"]["password"]

    uname = driver.find_element(By.ID, "username")
    uname.send_keys(username)
    time.sleep(2)
    pword = driver.find_element(By.ID, "password")
    pword.send_keys(password)
    time.sleep(2)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    desired_url = "https://www.linkedin.com/feed/"

    def wait_for_correct_current_url(desired_url):
        while driver.current_url != desired_url:
            time.sleep(0.01)

    wait_for_correct_current_url(desired_url)

    return driver


def extract_connections(soup):
    # Find the element containing the connections count.
    connections_section = soup.find("span", class_="link-without-visited-state")
    if connections_section:
        # This ensures that "connections" is in the text and avoids matching "followers"
        connections_text = connections_section.get_text(strip=True)
        if "connections" in connections_text:
            return connections_text
    return "Not found or less than 500"


def safe_lower(text):
    if text:
        return text.lower()
    return ""


def get_contact_info(driver):
    try:
        # Ensure the Contact Info modal is open
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@href, 'contact-info')]")
            )
        ).click()

        # Wait for the contact info section to appear
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "div.pv-contact-info__ci-container")
            )
        )

        # Extract the contact info HTML content
        contact_info_html = driver.page_source
        contact_soup = BeautifulSoup(contact_info_html, "html.parser")

        # Find the 'Connected' date
        connected_date_element = contact_soup.find(
            "span", {"class": "pv-contact-info__contact-item"}
        )
        connected_date = (
            connected_date_element.get_text(strip=True)
            if connected_date_element
            else "Not found"
        )

        # Locate the email using the updated class selectors
        email_element = contact_soup.select_one(
            "div.pv-contact-info__ci-container a[href^='mailto:']"
        )
        if email_element:
            email = email_element.get("href").replace(
                "mailto:", ""
            )  # This removes the 'mailto:' part
        else:
            email = "Not found"

        # You might need to close the modal if it obstructs the page
        # Find the close button by its class or other attributes and click it

        return connected_date, email
    except TimeoutException:
        return "Not found", "Not found"


def extract_education_from_html(soup, profile_data):
    education_section = soup.find("section", id="education-section")
    if not education_section:
        return

    education_section = soup.find("section", id="education-section")
    if education_section:
        educations = education_section.find_all("li", class_="artdeco-list__item")
        for edu in educations:
            edu_data = {}
            school_name = edu.find(
                "h3", class_="t-16"
            )  # Adjust class as per actual HTML structure
            edu_data["School Name"] = (
                school_name.get_text(strip=True) if school_name else "Not found"
            )

            degree_name = edu.find(
                "span", class_="t-14"
            )  # Adjust class as per actual HTML structure
            edu_data["Degree Name"] = (
                degree_name.get_text(strip=True) if degree_name else "Not found"
            )

            field_of_study = edu.find(
                "span", class_="pv-entity__comma-item"
            )  # Adjust class as per actual HTML structure
            edu_data["Field of Study"] = (
                field_of_study.get_text(strip=True) if field_of_study else "Not found"
            )

            dates = edu.find(
                "time", class_="t-14"
            )  # Adjust class as per actual HTML structure
            dates_attended = (
                " - ".join([date.get_text(strip=True) for date in dates])
                if dates
                else "Not found"
            )
            edu_data["Dates Attended"] = dates_attended

            profile_data["Education"].append(edu_data)


def get_text_excluding_comments(tag):
    texts = [t for t in tag.contents if not isinstance(t, Comment)]
    return "".join(texts).strip()


def scrape_profile_selenium(data):
    driver = driver_init()
    profiles_data = []

    for profile_url in data["profile_urls"]:  ## Dict containing list of urls
        profile_data = {
            "Name": "",
            "Company": "",
            "Location": "",
            "Connections": "",
            "Experience": [],
            "Education": [],
        }
        driver.get(profile_url)
        time.sleep(5)  # Adjust timing as needed for the page to load

        soup = BeautifulSoup(driver.page_source, "html.parser")

        intro = soup.find("div", {"class": "mt2 relative"})
        name_loc = intro.find("h1") if intro else None
        profile_data["Name"] = name_loc.text.strip() if name_loc else ""

        company_loc = soup.find("div", class_="text-body-medium")
        profile_data["Company"] = company_loc.text.strip() if company_loc else ""

        location_loc = (
            intro.find_all("span", {"class": "text-body-small"}) if intro else []
        )
        profile_data["Location"] = location_loc[0].text.strip() if location_loc else ""

        connections_element = soup.find(
            "span", string=lambda text: "connections" in safe_lower(text)
        )
        profile_data["Connections"] = extract_connections(soup)

        repost_date_element = soup.find("span", class_="white-space-pre")
        profile_data["LastRepostDate"] = (
            repost_date_element.text.strip() if repost_date_element else "Not found"
        )

        repost_date_element = soup.find(
            "span", class_="feed-mini-update-contextual-description__text"
        )
        if repost_date_element:
            # Extracting the text and stripping it to remove unnecessary whitespace.
            profile_data["LastRepostDate"] = repost_date_element.get_text(strip=True)
        else:
            profile_data["LastRepostDate"] = "Not found"

        connected_date, email = get_contact_info(driver)
        profile_data["ConnectedDate"] = connected_date
        profile_data["Email"] = email

        # Process Experience Section
        experience_section = soup.find(
            lambda tag: tag.name == "section" and tag.find("div", {"id": "experience"})
        )
        if experience_section:
            experiences = experience_section.find_all(
                "li", {"class": "artdeco-list__item"}
            )
            for exp in experiences:
                exp_data = {}
                exp_data["Job Title"] = (
                    exp.find("span").text.strip() if exp.find("span") else ""
                )
                # Assuming company and date are in 't-14' spans; adjust as needed
                company_exp_elements = exp.find_all("span", class_="t-14")
                exp_data["Company"] = (
                    company_exp_elements[0].text.strip()
                    if len(company_exp_elements) > 0
                    else ""
                )
                exp_data["Date"] = (
                    company_exp_elements[1].text.strip()
                    if len(company_exp_elements) > 1
                    else ""
                )
                profile_data["Experience"].append(exp_data)

        # Process Education Section (similar logic to Experience)
        education_section = soup.find(
            lambda tag: tag.name == "section" and tag.find("div", {"id": "education"})
        )
        if education_section:
            educations = education_section.find_all(
                "li", {"class": "artdeco-list__item"}
            )
            for edu in educations:
                edu_data = {}
                edu_data["School Name"] = (
                    edu.find("span", {"class": "t-bold"}).text.strip()
                    if edu.find("span", {"class": "t-bold"})
                    else ""
                )
                edu_data["Degree Name"] = (
                    edu.find("span", {"class": "t-14"}).text.strip()
                    if edu.find("span", {"class": "t-14"})
                    else ""
                )
                edu_field_of_study = edu.find(
                    "span", {"class": "pv-entity__comma-item"}
                )
                edu_data["Field of Study"] = (
                    edu_field_of_study.text.strip() if edu_field_of_study else ""
                )
                edu_dates = edu.find_all("span", class_="visually-hidden")
                edu_data["Dates Attended"] = (
                    edu_dates[-1].text.strip() if edu_dates else ""
                )  # Assuming the last 'visually-hidden' span contains the date
                profile_data["Education"].append(edu_data)

            school_name_element = edu.find("span", attrs={"aria-hidden": "true"})

            # Extract text while excluding comments
            edu_data["School Name"] = (
                get_text_excluding_comments(school_name_element)
                if school_name_element
                else "Not found"
            )
        extract_education_from_html(soup, profile_data)
        profiles_data.append(profile_data)

        # Print the collected profile data to the terminal
        print(f"\nScraped Profile Data:")
        print(f"Name: {profile_data['Name']}")
        print(f"Company: {profile_data['Company']}")
        print(f"Location: {profile_data['Location']}")
        print(f"Connections: {profile_data['Connections']}")
        print(f"Last Repost Date: {profile_data['LastRepostDate']}")
        print(f"Connected Date: {profile_data['ConnectedDate']}")
        print(f"Email: {profile_data['Email']}")
        print("Experience:")
        for exp in profile_data["Experience"]:
            print(
                f" - Job Title: {exp['Job Title']}, Company: {exp['Company']}, Date: {exp['Date']}"
            )
        print("Education:")
        for edu in profile_data["Education"]:
            print(
                f" - School Name: {edu['School Name']}, Degree Name: {edu['Degree Name']}, Field of Study: {edu['Field of Study']}, Dates Attended: {edu['Dates Attended']}"
            )

        # Closing the driver after scraping
        driver.quit()

        return profiles_data


def scrape_profile_pcurl(data):
    with open("pcurl.key", "r") as f:
        api_key = f.read()

    profiles_data = []

    for profile_url in data["profile_urls"]:
        headers = {"Authorization": "Bearer " + api_key}
        api_endpoint = "https://nubela.co/proxycurl/api/v2/linkedin"
        response = requests.get(
            api_endpoint,
            params={
                "url": profile_url,
                "use_cache": "if-recent",
            },  # if-recent uses two credits
            headers=headers,
        )

        # print(response)

        profiles_data.append(response.json())

    return profiles_data


def master(data):
    try:
        output = scrape_profile_selenium(data)  # scrape_profile_selenium

    except (KeyError, ValueError) as e:  # Jaliya to test
        print(
            f"Selenium failed, trying scraping through proxycurl - error {type(e).__name__}, {e}"
        )
        output = scrape_profile_pcurl(data)

    # Add data validation and uniformity for both calls

    return output


class SupportFuns:

    @staticmethod
    def csv_export(profiles_data, filename):
        # Convert the scraped data to a pandas DataFrame
        profiles_df = pd.DataFrame.from_records(profiles_data)

        # Expand 'Experience' and 'Education' lists into string representations for CSV
        profiles_df["Experience"] = profiles_df["Experience"].apply(
            lambda x: (
                "\n".join(
                    [
                        f"{exp['Job Title']} at {exp['Company']}, {exp['Date']}"
                        for exp in x
                    ]
                )
                if x
                else ""
            )
        )
        profiles_df["Education"] = profiles_df["Education"].apply(
            lambda x: (
                "\n".join(
                    [
                        f"{edu['School Name']}, {edu['Degree Name']}, {edu['Field of Study']}, {edu['Dates Attended']}"
                        for edu in x
                    ]
                )
                if x
                else ""
            )
        )

        # Save the DataFrame to a CSV file
        profiles_df.to_csv(filename, index=False, encoding="utf-8")

        print(
            "\nLinkedIn profile data has been successfully saved to linkedin_profiles.csv."
        )

        return True
