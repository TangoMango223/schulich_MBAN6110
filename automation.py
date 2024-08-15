# Faster download and renaming files, and putting the files into the right folders.

import os
import csv
import requests
import time

# Specify the path to your CSV file
csv_file_path = r'C:\Users\chris\OneDrive\Documents\VSCode\schulich_MBAN6110\name.csv'
retry_attempts = 3  # Number of retry attempts if a download fails
retry_delay = 5  # Delay in seconds between retry attempts

# Open and read the CSV file
with open(csv_file_path, mode='r', newline='', encoding='utf-8') as file:
    reader = csv.reader(file)
    
    # Skip the header row if present
    next(reader, None)

    for row in reader:
        file_name = row[0]  # Column A
        file_url = row[1]   # Column B
        category = row[2]   # Column C
        
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

                    # Save the file with the name from Column A in the appropriate category folder
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

print("All files have been processed.")
