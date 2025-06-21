"""YouTube Downloader - メインアプリケーション"""

import tkinter as tk

from download.manager import DownloadManager
from ui.main_window import MainWindow
from utils.cookie_manager import CookieManager


class YouTubeDownloaderApp:
    """YouTubeダウンローダーアプリケーション"""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.download_manager = DownloadManager()
        self.cookie_manager = CookieManager()
        self.main_window = MainWindow(self.root)

        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """コールバック関数の設定"""
        # UIのコールバック設定
        self.main_window.set_callbacks(
            start_download=self._start_download, stop_download=self._stop_download, set_cookies=self._set_cookies
        )

        # ダウンロードマネージャーのコールバック設定
        self.download_manager.set_callbacks(
            progress_callback=self._on_progress_update,
            status_callback=self._on_status_update,
            error_callback=self._on_error,
            success_callback=self._on_success,
        )

    def _start_download(self) -> None:
        """ダウンロード開始処理"""
        # UIから設定値を取得
        url = self.main_window.state.url_var.get().strip()
        save_folder = self.main_window.state.save_folder_var.get().strip()
        quality = self.main_window.state.quality_var.get()
        use_browser_cookies = self.main_window.state.get_cookies_from_browser.get()

        # 入力値の検証
        if not url:
            self.main_window.show_error("エラー", "URLを入力してください")
            return

        if not save_folder:
            self.main_window.show_error("エラー", "保存フォルダを選択してください")
            return

        # UIを更新
        self.main_window.set_download_in_progress(True)

        # ダウンロード開始
        success = self.download_manager.start_download(
            url=url, save_folder=save_folder, quality=quality, use_browser_cookies=use_browser_cookies
        )

        if not success:
            self.main_window.set_download_in_progress(False)

    def _stop_download(self) -> None:
        """ダウンロード停止処理"""
        self.download_manager.stop_download()
        self.main_window.set_download_in_progress(False)

    def _set_cookies(self) -> None:
        """Cookie設定処理"""
        try:
            # 現在のCookieを読み込み
            current_cookies = self.cookie_manager.load_cookies()

            # Cookie設定ダイアログを表示
            result = self.main_window.show_cookie_dialog(current_cookies)

            if result is not None:
                # Cookieを保存
                if self.cookie_manager.save_cookies(result):
                    self.main_window.show_info("成功", "Cookieを保存しました")
                else:
                    self.main_window.show_error("エラー", "Cookieの保存に失敗しました")
        except Exception as e:
            self.main_window.show_error("エラー", f"Cookie設定中にエラーが発生しました: {str(e)}")

    def _on_progress_update(self, percent: float, status_text: str) -> None:
        """プログレス更新処理"""

        def update_ui():
            self.main_window.progress_tracker.update_progress(percent, status_text)

        self.root.after(0, update_ui)

    def _on_status_update(self, status_text: str) -> None:
        """ステータス更新処理"""

        def update_ui():
            self.main_window.progress_tracker.set_status(status_text)

        self.root.after(0, update_ui)

    def _on_error(self, error_message: str) -> None:
        """エラー処理"""

        def show_error():
            self.main_window.set_download_in_progress(False)
            self.main_window.show_error("エラー", error_message)

        self.root.after(0, show_error)

    def _on_success(self) -> None:
        """成功処理"""

        def show_success():
            self.main_window.set_download_in_progress(False)
            self.main_window.show_info("成功", "動画のダウンロードが完了しました！")

        self.root.after(0, show_success)

    def run(self) -> None:
        """アプリケーションの実行"""
        self.root.mainloop()


def main() -> None:
    """メインエントリーポイント"""
    app = YouTubeDownloaderApp()
    app.run()


if __name__ == "__main__":
    main()
