
import os
import shutil
import hashlib
import time

LOGS_FOLDER = '/content/Retrieval-based-Voice-Conversion-WebUI/logs'
WEIGHTS_FOLDER = '/content/Retrieval-based-Voice-Conversion-WebUI/weights'
GOOGLE_DRIVE_PATH = '/content/drive/MyDrive/RVC_Backup'

def import_google_drive_backup():
    print("Importing Google Drive backup...")
    GOOGLE_DRIVE_PATH = '/content/drive/MyDrive/RVC_Backup'  # change this to your Google Drive path
    LOGS_FOLDER = '/content/Retrieval-based-Voice-Conversion-WebUI/logs'
    WEIGHTS_FOLDER = '/content/Retrieval-based-Voice-Conversion-WebUI/weights'
    weights_exist = False
    files_to_copy = []
    weights_to_copy = []

    for root, dirs, files in os.walk(GOOGLE_DRIVE_PATH):
        for filename in files:
            filepath = os.path.join(root, filename)
            if os.path.isfile(filepath) and not filepath.startswith(os.path.join(GOOGLE_DRIVE_PATH, 'weights')):
                backup_filepath = os.path.join(LOGS_FOLDER, os.path.relpath(filepath, GOOGLE_DRIVE_PATH))
                backup_folderpath = os.path.dirname(backup_filepath)
                if not os.path.exists(backup_folderpath):
                    os.makedirs(backup_folderpath)
                    print(f'Created backup folder: {backup_folderpath}', flush=True)
                files_to_copy.append((filepath, backup_filepath))  # add to list of files to copy
            elif filepath.startswith(os.path.join(GOOGLE_DRIVE_PATH, 'weights')) and filename.endswith('.pth'):
                weights_exist = True
                weights_filepath = os.path.join(WEIGHTS_FOLDER, os.path.relpath(filepath, os.path.join(GOOGLE_DRIVE_PATH, 'weights')))
                weights_folderpath = os.path.dirname(weights_filepath)
                if not os.path.exists(weights_folderpath):
                    os.makedirs(weights_folderpath)
                    print(f'Created weights folder: {weights_folderpath}', flush=True)
                weights_to_copy.append((filepath, weights_filepath))  # add to list of weights to copy

    # Copy files in batches
    total_files = len(files_to_copy)
    for i, (source, dest) in enumerate(files_to_copy, start=1):
        shutil.copy2(source, dest)
        # using '\r' to return to the start of the line and 'end=""' to prevent newline
        print(f'\rCopying file {i} of {total_files} ({i * 100 / total_files:.2f}%)', end="")

    print(f'\nImported {len(files_to_copy)} files from Google Drive backup')

    # Copy weights in batches
    total_weights = len(weights_to_copy)
    for i, (source, dest) in enumerate(weights_to_copy, start=1):
        shutil.copy2(source, dest)
        # using '\r' to return to the start of the line and 'end=""' to prevent newline
        print(f'\rCopying weight file {i} of {total_weights} ({i * 100 / total_weights:.2f}%)', end="")
    
    if weights_exist:
        print(f'\nImported {len(weights_to_copy)} weight files')
        print("Copied weights from Google Drive backup to local weights folder.")
    else:
        print("\nNo weights found in Google Drive backup.")

    print("Google Drive backup import completed.")
    
def get_md5_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def copy_weights_folder_to_drive():
    destination_folder = os.path.join(GOOGLE_DRIVE_PATH, 'weights')
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    num_copied = 0
    for filename in os.listdir(WEIGHTS_FOLDER):
        if filename.endswith('.pth'):
            source_file = os.path.join(WEIGHTS_FOLDER, filename)
            destination_file = os.path.join(destination_folder, filename)
            if not os.path.exists(destination_file):
                shutil.copy2(source_file, destination_file)
                num_copied += 1
                print(f"Copied {filename} to Google Drive!")

    if num_copied == 0:
        print("No new finished models found for copying.")
    else:
        print(f"Finished copying {num_copied} files to Google Drive!")

def backup_files():
    print("\n Starting backup loop...")
    last_backup_timestamps_path = os.path.join(LOGS_FOLDER, 'last_backup_timestamps.txt')
    fully_updated = False  # boolean to track if all files are up to date
    try:
        with open(last_backup_timestamps_path, 'r') as f:
            last_backup_timestamps = dict(line.strip().split(':') for line in f)
    except:
        last_backup_timestamps = {}

    while True:
        updated = False
        files_to_copy = []
        files_to_delete = []

        for root, dirs, files in os.walk(LOGS_FOLDER):
            for filename in files:
                if filename != 'last_backup_timestamps.txt':
                    filepath = os.path.join(root, filename)
                    if os.path.isfile(filepath):
                        backup_filepath = os.path.join(GOOGLE_DRIVE_PATH, os.path.relpath(filepath, LOGS_FOLDER))
                        backup_folderpath = os.path.dirname(backup_filepath)

                        if not os.path.exists(backup_folderpath):
                            os.makedirs(backup_folderpath)
                            print(f'Created backup folder: {backup_folderpath}', flush=True)

                        # check if file has changed since last backup
                        last_backup_timestamp = last_backup_timestamps.get(filepath)
                        current_timestamp = os.path.getmtime(filepath)
                        if last_backup_timestamp is None or float(last_backup_timestamp) < current_timestamp:
                            files_to_copy.append((filepath, backup_filepath))  # add to list of files to copy
                            last_backup_timestamps[filepath] = str(current_timestamp)  # update last backup timestamp
                            updated = True
                            fully_updated = False  # if a file is updated, all files are not up to date

        # check if any files were deleted in Colab and delete them from the backup drive
        for filepath in list(last_backup_timestamps.keys()):
            if not os.path.exists(filepath):
                backup_filepath = os.path.join(GOOGLE_DRIVE_PATH, os.path.relpath(filepath, LOGS_FOLDER))
                if os.path.exists(backup_filepath):
                    files_to_delete.append(backup_filepath)  # add to list of files to delete
                del last_backup_timestamps[filepath]
                updated = True
                fully_updated = False  # if a file is deleted, all files are not up to date

        # Copy files in batches
        if files_to_copy:
            for source, dest in files_to_copy:
                shutil.copy2(source, dest)
            print(f'Copied or updated {len(files_to_copy)} files')

        # Delete files in batches
        if files_to_delete:
            for file in files_to_delete:
                os.remove(file)
            print(f'Deleted {len(files_to_delete)} files')

        if not updated and not fully_updated:
            print("Files are up to date.")
            fully_updated = True  # if all files are up to date, set the boolean to True
            copy_weights_folder_to_drive()

        with open(last_backup_timestamps_path, 'w') as f:
            for filepath, timestamp in last_backup_timestamps.items():
                f.write(f'{filepath}:{timestamp}\n')
        time.sleep(15)  # wait for 15 seconds before checking again
