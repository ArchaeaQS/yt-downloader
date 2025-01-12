import os
import subprocess
from pathlib import Path

import requests


class ToolManager:
    def __init__(self, save_dir=None):
        if save_dir is None:
            # ユーザーのホームディレクトリから tools ディレクトリを作成
            self.save_dir = Path.home() / "AppData" / "Local" / "yt-downloader" / "tools"
            self.save_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.save_dir = Path(save_dir)

    def _get_tool_path(self, tool_name: str) -> Path:
        return self.save_dir / tool_name

    def check_tool_exists(self, tool_name: str) -> bool:
        return self._get_tool_path(tool_name).exists()

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
        ffmpeg_path = self._get_tool_path("ffmpeg.exe")

        # システムパスまたは保存ディレクトリ内の確認
        if self.is_tool_installed("ffmpeg"):
            return True
        elif ffmpeg_path.exists():
            os.environ["PATH"] += os.pathsep + str(self.save_dir)
            return True

        # ダウンロード
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = self._get_tool_path("ffmpeg.zip")
        try:
            if self.download_file(url, str(zip_path)):
                # ZIPファイルを解凍
                subprocess.run(
                    [
                        "powershell",
                        "-Command",
                        f"Expand-Archive -Path '{zip_path}' -DestinationPath '{self.save_dir}' -Force",
                    ],
                    check=True,
                )
                zip_path.unlink()

                # binフォルダ内のffmpeg.exeを探して移動
                bin_path = self.save_dir / "ffmpeg-master-latest-win64-gpl" / "bin" / "ffmpeg.exe"
                if bin_path.exists():
                    bin_path.rename(ffmpeg_path)

                    # 不要になったディレクトリを削除
                    import shutil

                    shutil.rmtree(self.save_dir / "ffmpeg-master-latest-win64-gpl")

                    os.environ["PATH"] += os.pathsep + str(self.save_dir)
                    return True

                print("ffmpeg.exeが見つかりませんでした")
                return False

        except Exception as e:
            print(f"ffmpegのダウンロード中にエラーが発生しました: {e}")
            return False
        return False

    # yt-dlpを確認し、インストールまたはアップデート
    def check_and_download_yt_dlp(self):
        yt_dlp_path = self._get_tool_path("yt-dlp.exe")

        if yt_dlp_path.exists():
            subprocess.run([str(yt_dlp_path), "-U"], check=True)
            return True

        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        return self.download_file(url, str(yt_dlp_path))

    # AtomicParsleyを確認し、インストール
    def check_and_download_atomicparsley(self):
        atomic_path = self._get_tool_path("AtomicParsley.exe")

        if atomic_path.exists():
            return True

        url = "https://github.com/wez/atomicparsley/releases/latest/download/AtomicParsleyWindows.zip"
        zip_path = self._get_tool_path("AtomicParsley.zip")

        if self.download_file(url, str(zip_path)):
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    f"Expand-Archive -Path '{zip_path}' -DestinationPath '{self.save_dir}' -Force",
                ],
                check=True,
            )
            zip_path.unlink()
            return True
        return False
