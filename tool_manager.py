import os
import subprocess

import requests


class ToolManager:
    def __init__(self, save_dir):
        self.save_dir = save_dir

    # ツールの存在確認関数
    def is_tool_installed(self, tool_name: str) -> bool:
        try:
            subprocess.run([tool_name, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    # ファイルをダウンロードする関数
    def download_file(self, url: str, save_path: str) -> bool:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    file.write(chunk)
            return True
        return False

    def check_and_download_ffmpeg(self) -> bool:
        ffmpeg_path = os.path.join(self.save_dir, "ffmpeg.exe")

        # システムパスまたは保存ディレクトリ内の確認
        if self.is_tool_installed("ffmpeg"):
            return True
        elif os.path.exists(ffmpeg_path):
            os.environ["PATH"] += os.pathsep + self.save_dir
            return True

        # ダウンロード
        url = "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-release-essentials.zip"
        zip_path = os.path.join(self.save_dir, "ffmpeg.zip")
        if self.download_file(url, zip_path):
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Expand-Archive -Path '{zip_path}' -DestinationPath '{self.save_dir}' -Force",
                ],
                check=True,
            )
            os.remove(zip_path)
            extracted_dir = os.path.join(self.save_dir, "ffmpeg")
            for root, _, files in os.walk(extracted_dir):
                for file in files:
                    if file.lower() == "ffmpeg.exe":
                        os.rename(os.path.join(root, file), ffmpeg_path)
                        break
            os.environ["PATH"] += os.pathsep + self.save_dir
            return True
        return False

    # yt-dlpを確認し、インストールまたはアップデート
    def check_and_download_yt_dlp(self):
        yt_dlp_path = os.path.join(self.save_dir, "yt-dlp.exe")

        if os.path.exists(yt_dlp_path):
            subprocess.run([yt_dlp_path, "-U"], check=True)
            return True

        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        return self.download_file(url, yt_dlp_path)

    # AtomicParsleyを確認し、インストール
    def check_and_download_atomicparsley(self):
        atomic_path = os.path.join(self.save_dir, "AtomicParsley.exe")

        if os.path.exists(atomic_path):
            return True

        url = "https://github.com/wez/atomicparsley/releases/latest/download/AtomicParsleyWindows.zip"
        zip_path = os.path.join(self.save_dir, "AtomicParsley.zip")

        if self.download_file(url, zip_path):
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Expand-Archive -Path '{zip_path}' -DestinationPath '{self.save_dir}' -Force",
                ],
                check=True,
            )
            os.remove(zip_path)
            return True
        return False
