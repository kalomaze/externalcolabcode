from mega import Mega
import os
import shutil
from urllib.parse import urlparse, parse_qs
import urllib.parse
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
import requests
import hashlib
import subprocess

def download_and_import_model(url, private_model):
    def calculate_md5(file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    # Initialize gspread
    scope = ['https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive']

    config_path = f'/content/Retrieval-based-Voice-Conversion-WebUI/stats/peppy-generator-388800-07722f17a188.json'

    if os.path.exists(config_path):
        # File exists, proceed with creation of creds and client
        creds = Credentials.from_service_account_file(config_path, scopes=scope)
        client = gspread.authorize(creds)
    else:
        # File does not exist, print message and skip creation of creds and client
        print("Sheet credential file missing.")

    # Open the Google Sheet (this will write any URLs so I can easily track popular models)
    book = client.open("RealtimeRVCStats")
    sheet = book.get_worksheet(3)  # get the fourth sheet

    def update_sheet(url, filename, filesize, md5_hash, index_version):
        data = sheet.get_all_records()
        df = pd.DataFrame(data)

        if md5_hash in df['MD5 Hash'].values:
            idx = df[df['MD5 Hash'] == md5_hash].index[0]

            # Update download count
            df.loc[idx, 'Download Counter'] = int(df.loc[idx, 'Download Counter']) + 1
            sheet.update_cell(idx+2, df.columns.get_loc('Download Counter') + 1, int(df.loc[idx, 'Download Counter']))

            # Find the next available Alt URL field
            alt_url_cols = [col for col in df.columns if 'Alt URL' in col]
            alt_url_values = [df.loc[idx, col_name] for col_name in alt_url_cols]

            # Check if url is the same as the main URL or any of the Alt URLs
            if url not in alt_url_values and url != df.loc[idx, 'URL']:
                for col_name in alt_url_cols:
                    if df.loc[idx, col_name] == '':
                        df.loc[idx, col_name] = url
                        sheet.update_cell(idx+2, df.columns.get_loc(col_name) + 1, url)
                        break
        else:
            # Prepare a new row as a dictionary
            new_row_dict = {'URL': url, 'Download Counter': 1, 'Filename': filename,
                            'Filesize (.pth)': filesize, 'MD5 Hash': md5_hash, 'RVC Version': index_version}

            alt_url_cols = [col for col in df.columns if 'Alt URL' in col]
            for col in alt_url_cols:
                new_row_dict[col] = ''  # Leave the Alt URL fields empty

            # Convert fields other than 'Download Counter' and 'Filesize (.pth)' to string
            new_row_dict = {key: str(value) if key not in ['Download Counter', 'Filesize (.pth)'] else value for key, value in new_row_dict.items()}

            # Append new row to sheet in the same order as existing columns
            ordered_row = [new_row_dict.get(col, '') for col in df.columns]
            sheet.append_row(ordered_row, value_input_option='RAW')

    condition1 = False
    condition2 = False
    already_downloaded = False

    # condition1 here is to check if the .index was imported. 2 is for if the .pth was.

    # Remove directories if they exist
    subprocess.run(['rm', '-rf', '/content/unzips/'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(['rm', '-rf', '/content/zips/'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Create directories
    os.makedirs('/content/unzips', exist_ok=True)
    os.makedirs('/content/zips', exist_ok=True)

    def sanitize_directory(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                if filename == ".DS_Store" or filename.startswith("._"):
                    os.remove(file_path)
            elif os.path.isdir(file_path):
                sanitize_directory(file_path)

    model_zip = urlparse(url).path.split('/')[-2] + '.zip'
    model_zip_path = '/content/zips/' + model_zip

    #@markdown This option should only be ticked if you don't want your model listed on the public tracker.
    private_model = False #@param{type:"boolean"}

    if url != '':
        MODEL = ""  # Initialize MODEL variable

        # Create directories if they don't exist
        os.makedirs(f'/content/Retrieval-based-Voice-Conversion-WebUI/logs/{MODEL}', exist_ok=True)
        os.makedirs('/content/zips/', exist_ok=True)
        os.makedirs('/content/Retrieval-based-Voice-Conversion-WebUI/weights/', exist_ok=True)

        if "drive.google.com" in url:
            subprocess.run(['gdown', url, '--fuzzy', '-O', model_zip_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elif "/blob/" in url:
            url = url.replace("blob", "resolve")
            print("Resolved URL:", url)  # Print the resolved URL
            subprocess.run(['wget', url, '-O', model_zip_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        elif "mega.nz" in url:
            m = Mega()
            print("Starting download from MEGA....")
            m.download_url(url, '/content/zips')
        elif "/tree/main" in url:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            temp_url = ''
            for link in soup.find_all('a', href=True):
                if link['href'].endswith('.zip'):
                    temp_url = link['href']
                    break
            if temp_url:
                url = temp_url
                print("Updated URL:", url)  # Print the updated URL
                url = url.replace("blob", "resolve")
                print("Resolved URL:", url)  # Print the resolved URL

                if "huggingface.co" not in url:
                    url = "https://huggingface.co" + url

                subprocess.run(['wget', url, '-O', model_zip_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            else:
                print("No .zip file found on the page.")
                # Handle the case when no .zip file is found
        else:
            subprocess.run(['wget', url, '-O', model_zip_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        for filename in os.listdir("/content/zips"):
            if filename.endswith(".zip"):
                zip_file = os.path.join("/content/zips", filename)
                shutil.unpack_archive(zip_file, "/content/unzips", 'zip')

    sanitize_directory("/content/unzips")

    def find_pth_file(folder):
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".pth"):
                    file_name = os.path.splitext(file)[0]
                    if file_name.startswith("G_") or file_name.startswith("P_"):
                        config_file = os.path.join(root, "config.json")
                        if os.path.isfile(config_file):
                            print("Outdated .pth detected! This is not compatible with the RVC method. Find the RVC equivalent model!")
                        continue  # Continue searching for a valid file
                    file_path = os.path.join(root, file)
                    if os.path.getsize(file_path) > 100 * 1024 * 1024:  # Check file size in bytes (100MB)
                        print("Skipping unusable training file:", file)
                        continue  # Continue searching for a valid file
                    return file_name
        return None

    MODEL = find_pth_file("/content/unzips")
    if MODEL is not None:
        print("Found .pth file:", MODEL + ".pth")
    else:
        print("Error: Could not find a valid .pth file within the extracted zip.")
        print("If there's an error above this talking about 'Access denied', try one of the Alt URLs in the Google Sheets for this model.")
        MODEL = ""
        global condition3
        condition3 = True

    index_path = ""

    def find_version_number(index_path):
        if condition2 and not condition1:
            if file_size >= 55180000:
                return 'RVC v2'
            else:
                return 'RVC v1'

        filename = os.path.basename(index_path)

        if filename.endswith("_v2.index"):
            return 'RVC v2'
        elif filename.endswith("_v1.index"):
            return 'RVC v1'
        else:
            if file_size >= 55180000:
                return 'RVC v2'
            else:
                return 'RVC v1'

    if MODEL != "":
        # Move model into logs folder
        for root, dirs, files in os.walk('/content/unzips'):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith(".index"):
                    print("Found index file:", file)
                    condition1 = True
                    logs_folder = os.path.join(f"/content/Retrieval-based-Voice-Conversion-WebUI/logs", MODEL)
                    os.makedirs(logs_folder, exist_ok=True)  # Create the logs folder if it doesn't exist

                    # Delete identical .index file if it exists
                    if file.endswith(".index"):
                        identical_index_path = os.path.join(logs_folder, file)
                        if os.path.exists(identical_index_path):
                            os.remove(identical_index_path)

                    shutil.move(file_path, logs_folder)
                    index_path = os.path.join(logs_folder, file)  # Set index_path variable

                elif "G_" not in file and "D_" not in file and file.endswith(".pth"):
                    destination_path = f'/content/Retrieval-based-Voice-Conversion-WebUI/weights/{MODEL}.pth'
                    if os.path.exists(destination_path):
                        print("You already downloaded this model. Re-importing anyways..")
                        already_downloaded = True
                    shutil.move(file_path, destination_path)
                    condition2 = True
                    if already_downloaded is False and os.path.exists(config_path):
                        file_size = os.path.getsize(destination_path) # Get file size
                        md5_hash = calculate_md5(destination_path) # Calculate md5 hash
                        index_version = find_version_number(index_path)  # Get the index version

    if condition1 is False:
        logs_folder = os.path.join(f"/content/Retrieval-based-Voice-Conversion-WebUI/logs", MODEL)
        os.makedirs(logs_folder, exist_ok=True)
    # this is here so it doesnt crash if the model is missing an index for some reason

    if condition2 and not condition1:
        print("Model partially imported! No .index file was found in the model download. The author may have forgotten to add the index file.")
        if already_downloaded is False and os.path.exists(config_path) and not private_model:
            update_sheet(url, MODEL, file_size, md5_hash, index_version)

    elif condition1 and condition2:
        print("Model successfully imported!")
        if already_downloaded is False and os.path.exists(config_path) and not private_model:
            update_sheet(url, MODEL, file_size, md5_hash, index_version)

    elif condition3:
        pass  # Do nothing when condition3 is true
    else:
        print("URL cannot be left empty. If you don't want to download a model now, just skip this step.")

    subprocess.run(['rm', '-r', '/content/unzips/'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    subprocess.run(['rm', '-r', '/content/zips/'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)