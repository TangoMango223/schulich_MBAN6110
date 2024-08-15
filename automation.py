# Data Pipeline to quickly download all research papers

import os
import csv
import requests
import time
import re

# Specify the path to your CSV file
csv_file_path = r'C:\Users\chris\OneDrive\Documents\VSCode\schulich_MBAN6110\name.csv'
retry_attempts = 3  # Number of retry attempts if a download fails
retry_delay = 5  # Delay in seconds between retry attempts
failed_downloads = []  # List to store failed download attempts

# Function to sanitize file names by removing special characters and new lines
# This makes it robust against any issues with naming or new lines, which was my earlier issue.
def sanitize_filename(file_name):
    # Remove new line characters
    file_name = file_name.replace('\n', '').replace('\r', '')
    # Define a pattern to match invalid characters for file names
    return re.sub(r'[<>:"/\\|?*\'"]', '', file_name)

# Open and read the CSV file
with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    
    # Skip the header row if present
    next(reader, None)

    for row in reader:
        file_name = row[0]  # Column A
        file_url = row[1]   # Column B
        category = row[2]   # Column C
        
        # Sanitize the file name
        file_name = sanitize_filename(file_name)
        
        # Ensure the category matches one of the expected values
        if category not in ['Technical_Paper', 'Academic_Paper']:
            print(f"Unknown category {category} for file {file_name}. Skipping...")
            continue

        # Create the category folder if it doesn't exist
        os.makedirs(category, exist_ok=True)

        # Create the file path
        file_path = os.path.join(category, f"{file_name}.pdf")
        
        for attempt in range(retry_attempts):
            try:
                # Download the file from the URL
                response = requests.get(file_url, timeout=10)
                response.raise_for_status()  # Check for HTTP errors
                
                # Verify Content-Type to ensure it's a PDF
                if 'application/pdf' in response.headers.get('Content-Type', ''):
                    
                    # Optionally verify content length
                    content_length = response.headers.get('Content-Length')
                    if content_length and int(content_length) != len(response.content):
                        print(f"File size mismatch for {file_name}. Retrying...")
                        continue

                    # Save the file with the sanitized name in the appropriate category folder
                    with open(file_path, 'wb') as downloaded_file:
                        downloaded_file.write(response.content)

                    # Verify file integrity by checking if the file size is non-zero
                    if os.path.getsize(file_path) > 0:
                        print(f"Successfully downloaded and saved: {file_name}.pdf in category {category}")
                        break  # Exit the retry loop if successful
                    else:
                        print(f"Downloaded file {file_name}.pdf is empty. Retrying...")

                else:
                    print(f"File {file_name} is not a valid PDF. Skipping...")
                    break

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed to download {file_name} in category {category}. Error: {e}")
                
            time.sleep(retry_delay)  # Wait before retrying

        else:
            print(f"Failed to download {file_name} in category {category} after {retry_attempts} attempts.")
            # Add to the list of failed downloads with name, url, and category
            failed_downloads.append({
                'File Name': file_name,
                'URL': file_url,
                'Category': category
            })

# Export the failed downloads to a CSV file
if failed_downloads:
    failed_csv_path = 'failed_downloads.csv'
    with open(failed_csv_path, mode='w', newline='', encoding='utf-8') as failed_file:
        fieldnames = ['File Name', 'URL', 'Category']
        writer = csv.DictWriter(failed_file, fieldnames=fieldnames)

        writer.writeheader()
        for failed in failed_downloads:
            writer.writerow(failed)

    print(f"\nFailed downloads have been saved to {failed_csv_path}.")
else:
    print("\nAll files were successfully downloaded.")

print("All files have been processed.")

