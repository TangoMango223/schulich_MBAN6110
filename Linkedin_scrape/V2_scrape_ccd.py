# Python Code to scrape Schulich CCD page for Linkedin networking opportunities
# Written by: Christine Tang

# Import statements
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from gspread_dataframe import set_with_dataframe

# Check pandas
import pandas as pd

# Environment variables handling
import os
from dotenv import load_dotenv


# Setup: 

# Load the Environmental Variables from .env 
load_dotenv()

# Initialize variables:
driver = None


# ------------------------------ PART 1: LINKEDIN SCRAPPING AND CLEANING ------------------------------


# --------------- INITIALIZE PYTHON DRIVER ---------------

def initialize_driver():
    # Set up Chrome options to pass:
    options = webdriver.ChromeOptions()

    # Path to your Chrome profile
    options.add_argument("user-data-dir=/Users/christine/Library/Application Support/Google/Chrome/Default")  # macOS example
    # options.add_argument("profile-directory=Default")  # Replace with the profile you want to use
    options.add_experimental_option("detach", True)

    # Use the correct path to chromedriver
    chrome_service = ChromeService('/Users/christine/chromedriver-mac-arm64/chromedriver')
    driver = webdriver.Chrome(service=chrome_service, options = options)
    
    # Return:
    return driver

# ---- Login to Linkedin. Mary's Login was saved to Cookies ---


def login_linkedin():
    # Open the LinkedIn page
    url = "https://www.linkedin.com/in/schulichccd/recent-activity/all/"
    driver.get(url)

    time.sleep(5)

    # Load cookies to a variable from a file
    with open('/Users/christine/VSCode/MBAN 6110 - remote/schulich_MBAN6110/Linkedin_scrape/cookies.json', 'r') as file:
        cookies = json.load(file)

    # Set stored cookies to maintain the session
    for cookie in cookies:
        driver.add_cookie(cookie)

# --------------- Set Scrolling Behaviour on Linkedin to scrape information ---------------

def scroll_and_scrape(driver, num_scrolls=20, scroll_amount=500):
    scroll_pause_time = 2  # Time to wait after each scroll
    all_texts = []  # List to store all scraped texts

    for i in range(num_scrolls):
        # Scroll down by a smaller amount
        driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        
        # Wait for new content to load
        time.sleep(scroll_pause_time)

        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Example: Find all div elements with dir="ltr"
        ltr_divs = soup.find_all('div', {'dir': 'ltr'})

        # Collect text from the relevant divs
        div_texts = [div.get_text().strip() for div in ltr_divs]

        # Append the newly found texts to the main list
        all_texts.extend(div_texts)

        # Optionally, break out of loop early if a certain condition is met (e.g., no new content found)
        if len(div_texts) == 0 and i > 0:  # Ensure at least one scroll
            print("No new content found on scroll number:", i+1)
            break

    # Return all collected texts
    return all_texts

    
# -------- Retrieve Information  --------
driver = initialize_driver()
time.sleep(1)
login_linkedin()

# Scroll and scrape content
scraped_texts = scroll_and_scrape(driver, num_scrolls=20, scroll_amount=500)

# Print the collected texts, give it a few seconds before closing
for text in scraped_texts:
    print(text)
    
# Time:
time.sleep(2)

# Close the WebDriver once completed.
driver.quit()


# -------- Cleaning  --------

# Remove duplicates:
cleaned_repo = list(set(scraped_texts))

# Extract Info:
def extract_all_event_info(posts):
    extracted_info = []

    for post in posts:
        # Find all event names before each 📅 emoji
        event_names = re.findall(r'(.*?)📅', post)

        # Find all event dates associated with the 📅 emoji
        event_dates = re.findall(r'📅\s*(.*?)\s*(?=📍|📝|https://lnkd|$)', post)

        # Find all event types associated with the 📍 emoji
        event_types = re.findall(r'📍\s*(.*?)\s*(?=📝|https://lnkd|$)', post)

        # Find all signup URLs associated with 📝 or directly with the https://lnkd link
        signup_urls = re.findall(r'(https://lnkd[^\s]+)', post)

        # Combine the results into a structured format
        for i in range(max(len(event_names), len(event_dates), len(event_types), len(signup_urls))):
            event_info = {
                'event_name': event_names[i].strip() if i < len(event_names) else 'N/A',
                'event_date': event_dates[i].strip() if i < len(event_dates) else 'N/A',
                'event_type': event_types[i].strip() if i < len(event_types) else 'N/A',
                'signup_url': signup_urls[i].strip() if i < len(signup_urls) else 'N/A'
            }
            extracted_info.append(event_info)

    return extracted_info

# Assuming scraped_texts is your list of posts
new_info = extract_all_event_info(scraped_texts)

# Filter posts to include only those containing "job opportunities" or "events"
filtered_posts = [post for post in cleaned_repo if "event" or "kickoff" in post.lower()]

# Remove duplicates:    
unique_event_posts = list(set(filtered_posts))

# Check:
for post in unique_event_posts:
    print(post)
    
    
# -------- Split by delimiters and extract from each string in the list ----------
import re

def split_based_on_delimiters(text_list):
    # Define the pattern to split on periods, ❗ emoji, and LinkedIn URLs
    # pattern = r'(\.|❗|https://lnkd[^\s]+)'
    pattern = r'(❗|https://lnkd[^\s]+)'
    
    all_segments = []

    for text in text_list:
        # Split the string based on the pattern and keep the delimiters
        split_text = re.split(pattern, text)
        
        # Combine the delimiters with their preceding text
        combined_segments = []
        temp_segment = ""
        
        for segment in split_text:
            if re.match(pattern, segment):
                # If the segment is a delimiter, add it to the current temp_segment
                temp_segment += segment
                combined_segments.append(temp_segment.strip())
                temp_segment = ""
            else:
                # Otherwise, add the text to the temp_segment
                temp_segment += segment
        
        # Add the last segment if there's anything left
        if temp_segment.strip():
            combined_segments.append(temp_segment.strip())
        
        # Append combined segments to the main list
        all_segments.extend(combined_segments)
    
    return all_segments


# Call the function above
new_entries = split_based_on_delimiters(unique_event_posts)

# Clean Step #1 - Remove unnecessary emojis
# Filter out entries
filter_events_seg = [seg for seg in new_entries if "📅" in seg]

# Remove all instances of ⬆  emoji:
new_list = [entry.replace("⬆", "") for entry in filter_events_seg]


# Clean Step #2 - Split iva emojis commonly found in CCD posts:
split_pattern = r'(📅.*?|📍.*?|📝.*?|👗 .*?|https://[^\s]+|\.)'
stuff = []

for line in new_list:
    a = re.split(split_pattern, line)
    # print(a)
    # print("----")
    stuff.append(a)
    
# Clean Step #3 - Final removal of "at", periods, and remove emojis used to identify events:
def clean_event_postings(event_lists):
    cleaned_events = []

    for event_list in event_lists:
        
        # Remove Nones
        the_list = [item for item in event_list if item is not None]
        
        # Remove any "at" keywords:
        the_list = [item for item in the_list if item!="at"]
        
        # Remove any empty strings:
        the_list = [item for item in the_list if item!=""]
        
        # Remove any periods:
        the_list = [item for item in the_list if item!="."]
        
        # Remove the emojis now:
        the_list = [item for item in the_list if item not in ['📅', '📍', '📝']]
        
        # Remove the words "registration deadline:"

        
        # Add the cleaned list to the final result if it's not empty about th
        if the_list:
            cleaned_events.append(the_list)
    
    return cleaned_events

# Call the function
final_list = clean_event_postings(stuff)


# Convert to Dataframe - will use later to write to Google Sheets
df = pd.DataFrame(final_list)

# ------------------------------ PART 2: Write to Google Sheet ------------------------------
# The format is still very ugly and not good, but faster for Christine to add entries in the Networking Sheet

# Step 1: Authentication
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('/Users/christine/VSCode/MBAN 6110 - remote/schulich_MBAN6110/Linkedin_scrape/linkedin_scraping.json', scope)
client = gspread.authorize(creds)

# Step 2: Open the Google Sheet using the Spreadsheet ID
spreadsheet_id = '1duHH_x9eqMIu3Ci727bL2D71mksA_29DC3nKm2m09jM'  # Replace with your actual Spreadsheet ID
spreadsheet = client.open_by_key(spreadsheet_id)

# Step 3: Access this specific sheet and tab
worksheet_name = 'ccd_linkedin_scrape_dump'  # Replace with the actual name of the worksheet
sheet = spreadsheet.worksheet(worksheet_name)

# Step 4: Clear sheet, then dump latest scrap from Schulich CCD Linkedin page:
# Clear Sheet
sheet.clear()

# Dump this into the sheet
set_with_dataframe(sheet, df) 
