
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
    
    def handle_files(root, files, is_weight_files=False):
        for filename in files:
            filepath = os.path.join(root, filename)
            if filename.endswith('.pth') and is_weight_files:
                weights_exist = True
                backup_filepath = os.path.join(WEIGHTS_FOLDER, os.path.relpath(filepath, GOOGLE_DRIVE_PATH))
            else:
                backup_filepath = os.path.join(LOGS_FOLDER, os.path.relpath(filepath, GOOGLE_DRIVE_PATH))
            backup_folderpath = os.path.dirname(backup_filepath)
            if not os.path.exists(backup_folderpath):
                os.makedirs(backup_folderpath)
                print(f'Created folder: {backup_folderpath}', flush=True)
            if is_weight_files:
                weights_to_copy.append((filepath, backup_filepath))
            else:
                files_to_copy.append((filepath, backup_filepath))

    for root, dirs, files in os.walk(os.path.join(GOOGLE_DRIVE_PATH, 'logs')):
        handle_files(root, files)
    
    for root, dirs, files in os.walk(os.path.join(GOOGLE_DRIVE_PATH, 'weights')):
        handle_files(root, files, True)

    # Copy files in batches
    total_files = len(files_to_copy)
    start_time = time.time()
    for i, (source, dest) in enumerate(files_to_copy, start=1):
        with open(source, 'rb') as src, open(dest, 'wb') as dst:
            shutil.copyfileobj(src, dst, 1024*1024)  # 1MB buffer size
        # Report progress every 5 seconds or after every 100 files, whichever is less frequent
        if time.time() - start_time > 5 or i % 100 == 0:
            print(f'\rCopying file {i} of {total_files} ({i * 100 / total_files:.2f}%)', end="")
            start_time = time.time()
    print(f'\nImported {len(files_to_copy)} files from Google Drive backup')

    # Copy weights in batches
    total_weights = len(weights_to_copy)
    start_time = time.time()
    for i, (source, dest) in enumerate(weights_to_copy, start=1):
        with open(source, 'rb') as src, open(dest, 'wb') as dst:
            shutil.copyfileobj(src, dst, 1024*1024)  # 1MB buffer size
        # Report progress every 5 seconds or after every 100 files, whichever is less frequent
        if time.time() - start_time > 5 or i % 100 == 0:
            print(f'\rCopying weight file {i} of {total_weights} ({i * 100 / total_weights:.2f}%)', end="")
            start_time = time.time()
    if weights_exist:
        print(f'\nImported {len(weights_to_copy)} weight files')
        print("Copied weights from Google Drive backup to local weights folder.")
    else:
        print("\nNo weights found in Google Drive backup.")
    print("Google Drive backup import completed.")

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
