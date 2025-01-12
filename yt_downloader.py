import asyncio
import os
import tkinter as tk
from threading import Thread
from tkinter import filedialog, messagebox, ttk

from yt_dlp import YoutubeDL

import config
import tool_manager


class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.resizable(width=False, height=False)

        # 変数の初期化
        self.save_folder_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar()

        # UI要素の作成
        self.create_ui()

        # 非同期イベントループを作成して別スレッドで開始
        self.asyncio_loop = asyncio.new_event_loop()
        self.thread = Thread(target=self.start_asyncio_loop, daemon=True)
        self.thread.start()

    def create_ui(self):
        # 保存フォルダ
        tk.Label(self.root, text="保存フォルダ:").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.save_folder_var, width=40).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self.root, text="フォルダ選択", command=self.choose_save_folder).grid(
            row=0, column=2, padx=5, pady=5
        )

        # URL入力
        tk.Label(self.root, text="動画URL:").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(self.root, textvariable=self.url_var, width=40).grid(row=1, column=1, padx=5, pady=5)

        # 画質選択（ドロップダウン）
        tk.Label(self.root, text="画質:").grid(row=2, column=0, padx=5, pady=5)

        # Comboboxを使用
        self.quality_combobox = ttk.Combobox(
            self.root,
            textvariable=self.quality_var,
            values=config.quality_options,
            state="readonly",
            width=37,
        )
        self.quality_combobox.set(config.quality_options[config.quality_default_idx])
        self.quality_combobox.grid(row=2, column=1, padx=5, pady=5)

        # ダウンロードプログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress_bar.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.progress_bar.grid_remove()  # 最初は非表示

        # ステータスラベル
        self.status_label = tk.Label(self.root, text="")
        self.status_label.grid(row=4, column=0, columnspan=3, padx=5, pady=5)

        # Cookie取得ボタン
        tk.Button(self.root, text="Cookie設定", command=self.set_cookies).grid(row=5, column=0, padx=5, pady=5)

        # ダウンロードボタン
        tk.Button(self.root, text="ダウンロード開始", command=self.start_download).grid(
            row=5, column=1, columnspan=2, padx=5, pady=5
        )

    def start_asyncio_loop(self):
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    def start_download(self):
        # プログレスバーを表示
        self.progress_bar.grid()
        # ダウンロード開始時にプログレスバーをリセット
        self.progress_var.set(0)
        self.status_label.config(text="ダウンロードを開始します...")
        asyncio.run_coroutine_threadsafe(self.download_video(), self.asyncio_loop)

    def choose_save_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_folder_var.set(folder)

    def set_cookies(self):
        try:

            def save_cookies():
                with open("cookies.txt", "w", encoding="utf-8") as file:  # エンコーディングを指定
                    file.write(text_area.get("1.0", tk.END))
                cookie_window.destroy()

            # 既存のcookieファイルを読み込む
            current_cookies = ""
            try:
                with open("cookies.txt", "r", encoding="utf-8") as file:  # エンコーディングを指定
                    current_cookies = file.read()
            except FileNotFoundError:
                pass

            # Cookie編集ウィンドウを作成
            cookie_window = tk.Toplevel(self.root)
            cookie_window.title("Cookie設定")
            cookie_window.geometry("600x400")
            cookie_window.transient(self.root)  # メインウィンドウに対するモーダルウィンドウに設定
            cookie_window.grab_set()  # モーダルにする

            # ボタンフレーム
            button_frame = tk.Frame(cookie_window)
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

            tk.Button(button_frame, text="保存", command=save_cookies).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="キャンセル", command=cookie_window.destroy).pack(side=tk.LEFT, padx=5)

            # テキストエリアを作成
            text_area = tk.Text(cookie_window)
            text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text_area.insert("1.0", current_cookies)

        except Exception as e:
            messagebox.showerror("エラー", f"エラーが発生しました: {e}")

    async def download_video(self):
        url = self.url_var.get().strip()  # 前後の空白を削除
        save_folder = self.save_folder_var.get()
        # 選択された画質から数値のみを抽出
        quality = self.quality_var.get().split()[0]

        if not url or not save_folder:
            messagebox.showerror("エラー", "URLまたは保存フォルダを指定してください")
            self.progress_bar.grid_remove()  # エラー時はプログレスバーを非表示
            return

        # cookiesファイルの存在確認
        cookies_exist = os.path.exists("cookies.txt")

        # yt-dlp のオプション設定
        ydl_opts = {
            "outtmpl": os.path.join(save_folder, "%(title)s.%(ext)s"),
            "format": f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]",
            "merge_output_format": "mp4",
            "verbose": True,  # 詳細なログを出力
            "no_warnings": False,  # 警告を表示
            "progress_hooks": [self.update_progress],
        }

        # cookiesファイルが存在する場合のみ追加
        if cookies_exist:
            ydl_opts["cookiefile"] = "cookies.txt"

        try:
            with YoutubeDL(ydl_opts) as ydl:
                await asyncio.to_thread(ydl.download, [url])

            # メインスレッドでメッセージボックスを表示
            self.root.after(0, lambda: messagebox.showinfo("成功", "動画のダウンロードが完了しました！"))
            # 完了後にプログレスバーを非表示
            self.root.after(0, self.progress_bar.grid_remove)
        except Exception as e:
            # メインスレッドでエラーメッセージを表示
            self.root.after(
                0, lambda err=e: messagebox.showerror("エラー", f"動画のダウンロードに失敗しました: {err}")
            )
            # エラー時にプログレスバーを非表示
            self.root.after(0, self.progress_bar.grid_remove)

    def update_progress(self, data):
        if data["status"] == "downloading":
            try:
                # ダウンロード済みバイト数とファイルサイズを取得
                downloaded = data.get("downloaded_bytes", 0)
                total = data.get("total_bytes") or data.get("total_bytes_estimate", 0)

                if total > 0:
                    percent = (downloaded / total) * 100
                    speed = data.get("speed", 0)
                    if speed:
                        speed_str = f"{speed/1024/1024:.1f} MB/s"
                    else:
                        speed_str = "計算中..."

                    # メインスレッドでUIを更新
                    self.root.after(0, lambda: self.progress_var.set(percent))
                    self.root.after(
                        0, lambda: self.status_label.config(text=f"ダウンロード中: {percent:.1f}%, 速度: {speed_str}")
                    )
            except Exception:
                pass
        elif data["status"] == "finished":
            self.root.after(0, lambda: self.progress_var.set(100))
            self.root.after(0, lambda: self.status_label.config(text="ダウンロード完了！"))


def main():
    root = tk.Tk()
    _ = YouTubeDownloader(root)

    # ツール管理
    tool_manager_instance = tool_manager.ToolManager(".")
    tool_manager_instance.check_and_download_ffmpeg()
    tool_manager_instance.check_and_download_yt_dlp()
    tool_manager_instance.check_and_download_atomicparsley()

    root.mainloop()


if __name__ == "__main__":
    main()
