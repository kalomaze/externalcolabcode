import os
import subprocess
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm.notebook import tqdm

def clone_repository():

    def run_cmd(cmd):
        process = subprocess.run(cmd, shell=True, check=True, text=True)
        return process.stdout

    # Change the current directory to /content/
    os.chdir('/content/')

    # Your function to edit the file
    def edit_file(file_path):
        temp_file_path = "/tmp/temp_file.py"
        changes_made = False
        with open(file_path, "r") as file, open(temp_file_path, "w") as temp_file:
            previous_line = ""
            second_previous_line = ""
            for line in file:
                new_line = line.replace("value=160", "value=128")
                if new_line != line:
                    print("Replaced 'value=160' with 'value=128'")
                    changes_made = True
                line = new_line

                new_line = line.replace("crepe hop length: 160", "crepe hop length: 128")
                if new_line != line:
                    print("Replaced 'crepe hop length: 160' with 'crepe hop length: 128'")
                    changes_made = True
                line = new_line

                new_line = line.replace("value=0.88", "value=0.75")
                if new_line != line:
                    print("Replaced 'value=0.88' with 'value=0.75'")
                    changes_made = True
                line = new_line

                if "label=i18n(\"输入源音量包络替换输出音量包络融合比例，越靠近1越使用输出包络\")" in previous_line and "value=1," in line:
                    new_line = line.replace("value=1,", "value=0.25,")
                    if new_line != line:
                        print("Replaced 'value=1,' with 'value=0.25,' based on the condition")
                        changes_made = True
                    line = new_line

                if "label=i18n(\"总训练轮数total_epoch\")" in previous_line and "value=20," in line:
                    new_line = line.replace("value=20,", "value=500,")
                    if new_line != line:
                        print("Replaced 'value=20,' with 'value=500,' based on the condition for DEFAULT EPOCH")
                        changes_made = True
                    line = new_line

                if 'choices=["pm", "harvest", "dio", "crepe", "crepe-tiny", "mangio-crepe", "mangio-crepe-tiny"], # Fork Feature. Add Crepe-Tiny' in previous_line:
                    if 'value="pm",' in line:
                        new_line = line.replace('value="pm",', 'value="mangio-crepe",')
                        if new_line != line:
                            print("Replaced 'value=\"pm\",' with 'value=\"mangio-crepe\",' based on the condition")
                            changes_made = True
                        line = new_line

                new_line = line.replace('label=i18n("输入训练文件夹路径"), value="E:\\\\语音音频+标注\\\\米津玄师\\\\src"', 'label=i18n("输入训练文件夹路径"), value="/content/dataset/"')
                if new_line != line:
                    print("Replaced 'label=i18n(\"输入训练文件夹路径\"), value=\"E:\\\\语音音频+标注\\\\米津玄师\\\\src\"' with 'label=i18n(\"输入训练文件夹路径\"), value=\"/content/dataset/\"'")
                    changes_made = True
                line = new_line

                if 'label=i18n("是否仅保存最新的ckpt文件以节省硬盘空间"),' in second_previous_line:
                    if 'value=i18n("否"),' in line:
                        new_line = line.replace('value=i18n("否"),', 'value=i18n("是"),')
                        if new_line != line:
                            print("Replaced 'value=i18n(\"否\"),' with 'value=i18n(\"是\"),' based on the condition for SAVE ONLY LATEST")
                            changes_made = True
                        line = new_line

                if 'label=i18n("是否在每次保存时间点将最终小模型保存至weights文件夹"),' in second_previous_line:
                    if 'value=i18n("否"),' in line:
                        new_line = line.replace('value=i18n("否"),', 'value=i18n("是"),')
                        if new_line != line:
                            print("Replaced 'value=i18n(\"否\"),' with 'value=i18n(\"是\"),' based on the condition for SAVE SMALL WEIGHTS")
                            changes_made = True
                        line = new_line

                temp_file.write(line)
                second_previous_line = previous_line
                previous_line = line

        # After finished, we replace the original file with the temp one
        import shutil
        shutil.move(temp_file_path, file_path)

        if changes_made:
            print("Changes made and file saved successfully.")
        else:
            print("No changes were needed.")

    # Define the repo path
    repo_path = '/content/Retrieval-based-Voice-Conversion-WebUI'

    if not os.path.exists(repo_path):
        # Clone the latest code from the Mangio621/Mangio-RVC-Fork repository
        run_cmd("git clone https://github.com/Mangio621/Mangio-RVC-Fork.git")
        os.chdir('/content/Mangio-RVC-Fork')
        run_cmd("wget https://github.com/777gt/EasyGUI-RVC-Fork/raw/main/EasierGUI.py")
        os.chdir('/content/')
        shutil.move('/content/Mangio-RVC-Fork', '/content/Retrieval-based-Voice-Conversion-WebUI')
        edit_file("/content/Retrieval-based-Voice-Conversion-WebUI/infer-web.py")
    else:
        print(f"The repository already exists at {repo_path}. Checking for 'utils' folder.")

        utils_folder_path = os.path.join(repo_path, 'utils')
        temp_folder_path = os.path.join(repo_path, 'temp_utils')

        if os.path.exists(utils_folder_path):
            print("Found 'utils' folder. Copying it to a temporary location.")

            # Copy 'utils' folder to temporary location
            shutil.copytree(utils_folder_path, temp_folder_path)

            # Delete the original RVC folder
            shutil.rmtree(repo_path)

        print("Continuing cloning...")
        # Clone the latest code from the Mangio621/Mangio-RVC-Fork repository
        run_cmd("git clone https://github.com/Mangio621/Mangio-RVC-Fork.git")
        os.chdir('/content/Mangio-RVC-Fork')
        run_cmd("wget https://github.com/777gt/EasyGUI-RVC-Fork/raw/main/EasierGUI.py")
        os.chdir('/content/')
        shutil.move('/content/Mangio-RVC-Fork', '/content/Retrieval-based-Voice-Conversion-WebUI')
        edit_file("/content/Retrieval-based-Voice-Conversion-WebUI/infer-web.py")

        if os.path.exists(temp_folder_path):
            print("Copying 'utils' folder back after cloning.")
            # Copy 'utils' folder back after cloning
            shutil.copytree(temp_folder_path, utils_folder_path)

            # Delete temporary 'utils' folder
            shutil.rmtree(temp_folder_path)

    # Download the credentials file for RVC archive sheet
    os.makedirs('/content/Retrieval-based-Voice-Conversion-WebUI/stats/', exist_ok=True)
    run_cmd("wget -q https://cdn.discordapp.com/attachments/945486970883285045/1114717554481569802/peppy-generator-388800-07722f17a188.json -O /content/Retrieval-based-Voice-Conversion-WebUI/stats/peppy-generator-388800-07722f17a188.json")

    # Forcefully delete any existing torchcrepe dependency from an earlier run
    shutil.rmtree('/Retrieval-based-Voice-Conversion-WebUI/torchcrepe', ignore_errors=True)

    # Download the torchcrepe folder from the maxrmorrison/torchcrepe repository
    run_cmd("git clone https://github.com/maxrmorrison/torchcrepe.git")
    shutil.move('torchcrepe/torchcrepe', 'Retrieval-based-Voice-Conversion-WebUI/')
    shutil.rmtree('torchcrepe', ignore_errors=True)  # Delete the torchcrepe repository folder

    # Change the current directory to /content/Retrieval-based-Voice-Conversion-WebUI
    os.chdir('/content/Retrieval-based-Voice-Conversion-WebUI')
    os.makedirs('pretrained', exist_ok=True)
    os.makedirs('uvr5_weights', exist_ok=True)

    def download_pretrained_models():
        pretrained_models = {
            "pretrained": [
                "D40k.pth",
                "G40k.pth",
                "f0D40k.pth",
                "f0G40k.pth"
            ],
            "pretrained_v2": [
                "D40k.pth",
                "G40k.pth",
                "f0D40k.pth",
                "f0G40k.pth",
                "f0G48k.pth",
                "f0D48k.pth"
            ],
            "uvr5_weights": [
                "HP2-人声vocals+非人声instrumentals.pth",
                "HP5-主旋律人声vocals+其他instrumentals.pth"
            ]
        }

        base_url = "https://huggingface.co/lj1995/VoiceConversionWebUI/resolve/main/"
        base_path = "/content/Retrieval-based-Voice-Conversion-WebUI/"

        def download_file(url, filepath, position):
            with tqdm(total=1, desc=f"Downloading {os.path.basename(filepath)}", position=position) as pbar:
                subprocess.run(["aria2c", "--console-log-level=error", "-c", "-x", "16", "-s", "16", "-k", "1M", url, "-d", os.path.dirname(filepath), "-o", os.path.basename(filepath)], check=True)
                pbar.update(1)

        with ThreadPoolExecutor() as executor:
            position = 0
            for folder, models in pretrained_models.items():
                folder_path = os.path.join(base_path, folder)
                os.makedirs(folder_path, exist_ok=True)
                download_tasks = []
                for model in models:
                    url = base_url + folder + "/" + model
                    filepath = os.path.join(folder_path, model)
                    download_tasks.append(executor.submit(download_file, url, filepath, position))
                    position += 1
                for task in download_tasks:
                    task.result()

        # Download hubert_base.pt to the base path
        hubert_url = base_url + "hubert_base.pt"
        hubert_filepath = os.path.join(base_path, "hubert_base.pt")
        position += 1  # Increment position for hubert_base.pt
        download_file(hubert_url, hubert_filepath, position)

    download_pretrained_models()