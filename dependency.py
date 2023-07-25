import os
import csv
import shutil
import tarfile
import subprocess
from pathlib import Path
from datetime import datetime

def install_packages_but_jank_af():
    packages = ['build-essential', 'python3-dev', 'ffmpeg', 'aria2']
    pip_packages = ['pip', 'setuptools', 'wheel', 'httpx==0.23.0', 'faiss-gpu', 'fairseq', 'gradio==3.34.0',
                    'ffmpeg', 'ffmpeg-python', 'praat-parselmouth', 'pyworld', 'numpy==1.23.5',
                    'numba==0.56.4', 'librosa==0.9.2', 'mega.py', 'gdown', 'onnxruntime', 'pyngrok==4.1.12',
                    'gTTS', 'elevenlabs']

    print("Updating and installing system packages...")
    for package in packages:
        print(f"Installing {package}...")
        subprocess.check_call(['apt-get', 'install', '-qq', '-y', package])

    print("Updating and installing pip packages...")
    subprocess.check_call(['pip', 'install', '--upgrade'] + pip_packages)

    print('Packages up to date.')


def setup_environment(ForceUpdateDependencies, ForceTemporaryStorage):
    # Mounting Google Drive
    if not ForceTemporaryStorage:
        from google.colab import drive

        if not os.path.exists('/content/drive'):
            drive.mount('/content/drive')
        else:
            print('Drive is already mounted. Proceeding...')

    # Function to install dependencies with progress
    def install_packages():
        packages = ['build-essential', 'python3-dev', 'ffmpeg', 'aria2']
        pip_packages = ['pip', 'setuptools', 'wheel', 'httpx==0.23.0', 'faiss-gpu', 'fairseq', 'gradio==3.34.0',
                        'ffmpeg', 'ffmpeg-python', 'praat-parselmouth', 'pyworld', 'numpy==1.23.5',
                        'numba==0.56.4', 'librosa==0.9.2', 'mega.py', 'gdown', 'onnxruntime', 'pyngrok==4.1.12',
                        'gTTS', 'elevenlabs']

        print("Updating and installing system packages...")
        for package in packages:
            print(f"Installing {package}...")
            subprocess.check_call(['apt-get', 'install', '-qq', '-y', package])

        print("Updating and installing pip packages...")
        subprocess.check_call(['pip', 'install', '--upgrade'] + pip_packages)

        print('Packages up to date.')

    # Function to scan a directory and writes filenames and timestamps
    def scan_and_write(base_path, output_file):
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            for dirpath, dirs, files in os.walk(base_path):
                for filename in files:
                    fname = os.path.join(dirpath, filename)
                    try:
                        mtime = os.path.getmtime(fname)
                        writer.writerow([fname, mtime])
                    except Exception as e:
                        print(f'Skipping irrelevant nonexistent file {fname}: {str(e)}')
        print(f'Finished recording filesystem timestamps to {output_file}.')

    # Function to compare files
    def compare_files(old_file, new_file):
        old_files = {}
        new_files = {}

        with open(old_file, 'r') as f:
            reader = csv.reader(f)
            old_files = {rows[0]:rows[1] for rows in reader}

        with open(new_file, 'r') as f:
            reader = csv.reader(f)
            new_files = {rows[0]:rows[1] for rows in reader}

        removed_files = old_files.keys() - new_files.keys()
        added_files = new_files.keys() - old_files.keys()
        unchanged_files = old_files.keys() & new_files.keys()

        changed_files = {f for f in unchanged_files if old_files[f] != new_files[f]}

        for file in removed_files:
            print(f'File has been removed: {file}')

        for file in changed_files:
            print(f'File has been updated: {file}')

        return list(added_files) + list(changed_files)

    # Check if CachedRVC.tar.gz exists
    if ForceTemporaryStorage:
        file_path = '/content/CachedRVC.tar.gz'
    else:
        file_path = '/content/drive/MyDrive/RVC_Cached/CachedRVC.tar.gz'

    content_file_path = '/content/CachedRVC.tar.gz'
    extract_path = '/'

    if not os.path.exists(file_path):
        folder_path = os.path.dirname(file_path)
        os.makedirs(folder_path, exist_ok=True)
        print('No cached dependency install found. Attempting to download GitHub backup..')

        try:
            download_url = "https://github.com/kalomaze/QuickMangioFixes/releases/download/release3/CachedRVC.tar.gz"
            subprocess.run(["wget", "-O", file_path, download_url])
            print('Download completed successfully!')
        except Exception as e:
            print('Download failed:', str(e))

            # Delete the failed download file
            if os.path.exists(file_path):
                os.remove(file_path)
            print('Failed download file deleted. Continuing manual backup..')

    if Path(file_path).exists():
        if ForceTemporaryStorage:
            print('Finished downloading CachedRVC.tar.gz.')
        else:
            print('CachedRVC.tar.gz found on Google Drive. Proceeding to copy and extract...')

        # Check if ForceTemporaryStorage is True and skip copying if it is
        if ForceTemporaryStorage:
            pass
        else:
            shutil.copy(file_path, content_file_path)

        print('Beginning backup copy operation...')

        with tarfile.open(content_file_path, 'r:gz') as tar:
            for member in tar.getmembers():
                target_path = os.path.join(extract_path, member.name)
                try:
                    tar.extract(member, extract_path)
                except Exception as e:
                    print('Failed to extract a file (this isn\'t normal)... forcing an update to compensate')
                    ForceUpdateDependencies = True
            print(f'Extraction of {content_file_path} to {extract_path} completed.')

        if ForceUpdateDependencies:
            install_packages()
            ForceUpdateDependencies = False
    else:
        print('CachedRVC.tar.gz not found. Proceeding to create an index of all current files...')
        scan_and_write('/usr/', '/content/usr_files.csv')

        install_packages()

        scan_and_write('/usr/', '/content/usr_files_new.csv')
        changed_files = compare_files('/content/usr_files.csv', '/content/usr_files_new.csv')

        with tarfile.open('/content/CachedRVC.tar.gz', 'w:gz') as new_tar:
            for file in changed_files:
                new_tar.add(file)
                print(f'Added to tar: {file}')

        os.makedirs('/content/drive/MyDrive/RVC_Cached', exist_ok=True)
        shutil.copy('/content/CachedRVC.tar.gz', '/content/drive/MyDrive/RVC_Cached/CachedRVC.tar.gz')
        print('Updated CachedRVC.tar.gz copied to Google Drive.')
        print('Dependencies fully up to date; future runs should be faster.')

