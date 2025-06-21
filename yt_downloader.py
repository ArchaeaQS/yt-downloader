import asyncio
import os
import subprocess
import tkinter as tk
from concurrent.futures import Future
from pathlib import Path
from threading import Thread
from tkinter import filedialog, messagebox, ttk

import config
import tool_manager


class DownloadState:
    """ダウンロード状態を管理するクラス"""

    def __init__(self):
        self.is_downloading = False
        self.stop_requested = False
        self.current_download_task: Future | None = None


class UIState:
    """UI状態を管理するクラス"""

    def __init__(self):
        self.save_folder_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.get_cookies_from_browser = tk.BooleanVar(value=False)

    def toggle_cookies(self) -> None:
        self.get_cookies_from_browser = not self.get_cookies_from_browser


class YouTubeDownloaderUI:
    """YouTubeダウンローダーのUI管理クラス"""

    def __init__(self, root: tk.Tk, downloader: "YouTubeDownloader") -> None:
        self.root = root
        self.setting_frame = tk.Frame()
        self.cookies_frame = tk.Frame()
        self.button_frame = tk.Frame()
        self.downloader = downloader
        self.state = UIState()
        self.create_ui()

    def create_ui(self) -> None:
        """UIコンポーネントの作成と配置"""
        self._create_save_folder_section()
        self._create_url_section()
        self._create_quality_section()
        self._create_get_cookies_setting_section()
        self._create_progress_section()
        self._create_button_section()

    def _create_save_folder_section(self) -> None:
        self.setting_frame.pack()
        tk.Label(self.setting_frame, text="保存フォルダ:").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(self.setting_frame, textvariable=self.state.save_folder_var, width=40).grid(
            row=0, column=1, padx=5, pady=5
        )
        tk.Button(self.setting_frame, text="フォルダ選択", command=self.choose_save_folder).grid(
            row=0, column=2, padx=5, pady=5
        )

    def _create_url_section(self) -> None:
        tk.Label(self.setting_frame, text="動画URL:").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(self.setting_frame, textvariable=self.state.url_var, width=40).grid(row=1, column=1, padx=5, pady=5)

    def _create_quality_section(self) -> None:
        tk.Label(self.setting_frame, text="画質:").grid(row=2, column=0, padx=5, pady=5)
        self.quality_combobox = ttk.Combobox(
            self.setting_frame,
            textvariable=self.state.quality_var,
            values=config.quality_options,
            state="readonly",
            width=37,
        )
        self.quality_combobox.set(config.quality_options[config.quality_default_idx])
        self.quality_combobox.grid(row=2, column=1, padx=5, pady=5)

    def _create_get_cookies_setting_section(self) -> None:
        self.cookies_frame.pack(fill="x")
        self.cookies_setting_button = tk.Button(
            self.cookies_frame, text="Cookie設定", command=self.downloader.set_cookies
        )
        self.cookies_setting_button.pack(side="left", padx=5, pady=5)
        self.cookies_toggle_button = tk.Checkbutton(
            self.cookies_frame,
            variable=self.state.get_cookies_from_browser,
            text="ブラウザからCookieを使用する",
            command=self.state.toggle_cookies,
        )
        self.cookies_toggle_button.pack(side="right", padx=5, pady=5)

    def _create_progress_section(self) -> None:
        self.button_frame.pack(fill="x")
        self.progress_bar = ttk.Progressbar(
            self.button_frame, variable=self.state.progress_var, maximum=100, mode="determinate"
        )
        self.progress_bar.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.progress_bar.grid_remove()

        self.status_label = tk.Label(self.button_frame, text="")
        self.status_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    def _create_button_section(self) -> None:
        self.button_frame.grid_columnconfigure(0, weight=2)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
        self.download_button = tk.Button(
            self.button_frame, text="ダウンロード開始", command=self.downloader.start_download
        )
        self.download_button.grid(row=2, column=1, padx=5, pady=5)

        self.stop_button = tk.Button(
            self.button_frame, text="停止", command=self.downloader.stop_download, state=tk.DISABLED
        )
        self.stop_button.grid(row=2, column=2, padx=5, pady=5)

    def choose_save_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.state.save_folder_var.set(folder)

    def show_cookie_dialog(self, current_cookies: str) -> None:
        cookie_window = tk.Toplevel(self.root)
        cookie_window.title("Cookie設定")
        cookie_window.geometry("600x400")
        cookie_window.transient(self.root)
        cookie_window.grab_set()

        text_area = tk.Text(cookie_window)
        text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_area.insert("1.0", current_cookies)

        button_frame = tk.Frame(cookie_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        def save_cookies() -> None:
            cookie_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
            cookie_dir.mkdir(exist_ok=True, parents=True)
            cookie_file = cookie_dir / "cookies.txt"
            cookie_file.write_text(text_area.get("1.0", tk.END).strip(), encoding="utf-8")
            os.chmod(str(cookie_file), 0o600)  # ユーザーのみ読み書き可能に設定
            cookie_window.destroy()

        tk.Button(button_frame, text="保存", command=save_cookies).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="キャンセル", command=cookie_window.destroy).pack(side=tk.LEFT, padx=5)


class YouTubeDownloader:
    """YouTubeの動画をダウンロードするためのアプリケーション"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.resizable(width=False, height=False)

        self.download_state = DownloadState()
        self.ui = YouTubeDownloaderUI(root, self)

        self.asyncio_loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._start_asyncio_loop, daemon=True)
        self.thread.start()

        self.tool_manager_instance = tool_manager.ToolManager()
        self.tool_manager_instance.check_and_download_ffmpeg()
        self.tool_manager_instance.check_and_download_yt_dlp()
        self.tool_manager_instance.check_and_download_atomicparsley()

    def _start_asyncio_loop(self) -> None:
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    def start_download(self) -> None:
        url = self.ui.state.url_var.get().strip()
        save_folder = self.ui.state.save_folder_var.get()

        if not url or not save_folder:
            messagebox.showerror("エラー", "URLまたは保存フォルダを指定してください")
            return

        self._prepare_download_ui()
        self.download_state.current_download_task = asyncio.run_coroutine_threadsafe(
            self.download_video(), self.asyncio_loop
        )

    def _prepare_download_ui(self) -> None:
        self.ui.progress_bar.grid()
        self.ui.state.progress_var.set(0)
        self.ui.status_label.config(text="ダウンロードを開始します...")
        self.download_state.is_downloading = True
        self.download_state.stop_requested = False
        self.ui.download_button.config(state=tk.DISABLED)
        self.ui.stop_button.config(state=tk.NORMAL)

    def stop_download(self) -> None:
        # TODO: ダウンロード停止処理の修正
        self.download_state.stop_requested = True

        if self.download_state.current_download_task and not self.download_state.current_download_task.done():
            self.download_state.current_download_task.cancel()
            self.download_state.current_download_task = None

        self._reset_ui_after_stop()

    def _reset_ui_after_stop(self) -> None:
        self.download_state.is_downloading = False
        self.ui.status_label.config(text="ダウンロードを中止しました")
        self.ui.progress_bar.grid_remove()
        self.ui.download_button.config(state=tk.NORMAL)
        self.ui.stop_button.config(state=tk.DISABLED)

    def _get_cookie_file_path(self) -> str:
        return Path.home() / "AppData" / "Local" / "yt-downloader" / "cookies.txt"

    def set_cookies(self) -> None:
        try:
            current_cookies = self._load_current_cookies()
            self.ui.show_cookie_dialog(current_cookies)
        except Exception as e:
            messagebox.showerror("エラー", f"エラーが発生しました: {e}")

    def _load_current_cookies(self) -> str:
        try:
            cookie_file = self._get_cookie_file_path()
            return cookie_file.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    async def download_video(self) -> None:
        def _download_video(self, quality, save_folder, url):
            yt_dlp_path = self.tool_manager_instance._get_tool_path("yt-dlp.exe")
            if self.ui.state.get_cookies_from_browser:
                subprocess.run(
                    [
                        str(yt_dlp_path),
                        "--cookies-from-browser",
                        "firefox",
                        "-f",
                        f"bestvideo[height<={int(quality)}][ext=mp4]+bestaudio[ext=m4a]/best",
                        "-o",
                        os.path.join(save_folder, "%(title)s.%(ext)s"),
                        f"{url}",
                    ],
                    check=True,
                )
            else:
                subprocess.run(
                    [
                        str(yt_dlp_path),
                        "--cookies",
                        self._get_cookie_file_path(),
                        "-f",
                        f"bestvideo[height<={int(quality)}][ext=mp4]+bestaudio[ext=m4a]/best",
                        "-o",
                        os.path.join(save_folder, "%(title)s.%(ext)s"),
                        f"{url}",
                    ],
                    check=True,
                )

        url = self.ui.state.url_var.get().strip()
        save_folder = self.ui.state.save_folder_var.get()
        quality = self.ui.state.quality_var.get().split()[0].replace("p", "")

        if not self._validate_download_params(url, save_folder):
            return

        if self.download_state.stop_requested:
            return

        try:
            if not self.download_state.stop_requested:

                async def download_with_check():
                    if self.download_state.stop_requested:
                        return
                    await asyncio.to_thread(_download_video, self, quality, save_folder, url)
                    if self.download_state.stop_requested:
                        return

                await asyncio.wait_for(download_with_check(), timeout=None)

            if self.download_state.is_downloading and not self.download_state.stop_requested:
                self._show_success_message()
        except Exception as e:
            if self.download_state.is_downloading and not self.download_state.stop_requested:
                self._show_error_message(str(e))
        finally:
            self._cleanup_after_download()

    def _validate_download_params(self, url: str, save_folder: str) -> bool:
        if not url or not save_folder:
            messagebox.showerror("エラー", "URLまたは保存フォルダを指定してください")
            self.ui.download_button.config(state=tk.NORMAL)
            self.ui.stop_button.config(state=tk.DISABLED)
            return False
        return True

    def _show_success_message(self) -> None:
        self.root.after(0, lambda: messagebox.showinfo("成功", "動画のダウンロードが完了しました！"))
        self.root.after(0, self.ui.progress_bar.grid_remove)

    def _show_error_message(self, error_msg: str) -> None:
        self.root.after(0, lambda: messagebox.showerror("エラー", f"動画のダウンロードに失敗しました: {error_msg}"))
        self.root.after(0, self.ui.progress_bar.grid_remove)

    def _cleanup_after_download(self) -> None:
        self.download_state.is_downloading = False
        self.download_state.stop_requested = False
        self.root.after(0, lambda: self.ui.download_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.ui.stop_button.config(state=tk.DISABLED))

    def update_progress(self, data: dict) -> None:
        if self.download_state.stop_requested or not self.download_state.is_downloading:
            raise Exception("Download cancelled")

        if data["status"] == "downloading":
            self._update_download_progress(data)
        elif data["status"] == "finished":
            self._update_finished_progress()

    def _update_download_progress(self, data: dict) -> None:
        # TODO: プログレスバーの修正
        try:
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)

            if total > 0:
                percent = (downloaded / total) * 100
                speed = data.get("speed", 0)
                speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "計算中..."

                self.root.after(0, lambda: self.ui.state.progress_var.set(percent))
                self.root.after(
                    0, lambda: self.ui.status_label.config(text=f"ダウンロード中: {percent:.1f}%, 速度: {speed_str}")
                )
        except Exception:
            pass

    def _update_finished_progress(self) -> None:
        self.root.after(0, lambda: self.ui.state.progress_var.set(100))
        self.root.after(0, lambda: self.ui.status_label.config(text="ダウンロード完了！"))


def main() -> None:
    root = tk.Tk()
    _ = YouTubeDownloader(root)

    root.mainloop()


if __name__ == "__main__":
    main()
