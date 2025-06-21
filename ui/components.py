"""UI状態管理とコンポーネント定義"""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow


class UIState:
    """UI状態を管理するクラス"""

    def __init__(self) -> None:
        self.save_folder_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.quality_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.get_cookies_from_browser = tk.BooleanVar(value=False)

        # リトライ設定
        self.enable_retry = tk.BooleanVar(value=True)
        self.max_retries = tk.IntVar(value=3)
        self.enable_individual_download = tk.BooleanVar(value=True)


class ProgressTracker:
    """プログレス管理クラス"""

    def __init__(self, main_window: "MainWindow") -> None:
        self.main_window = main_window

    def update_progress(self, percent: float, status_text: str = "") -> None:
        """プログレスバーと状態テキストを更新"""
        self.main_window.state.progress_var.set(percent)
        if status_text:
            self.main_window.status_label.config(text=status_text)

    def show_progress(self) -> None:
        """プログレスバーを表示"""
        self.main_window.progress_bar.pack(fill="x", pady=(0, 5))

    def hide_progress(self) -> None:
        """プログレスバーを非表示"""
        self.main_window.progress_bar.pack_forget()

    def set_status(self, text: str) -> None:
        """ステータステキストを設定"""
        self.main_window.status_label.config(text=text)
