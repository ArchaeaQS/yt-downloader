"""メインウィンドウのUI管理"""
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Callable, Optional

import config
from ui.components import ProgressTracker, UIState

if TYPE_CHECKING:
    from download.manager import DownloadManager


class CookieDialog:
    """Cookie設定ダイアログ"""
    
    def __init__(self, parent: tk.Tk, current_cookies: str) -> None:
        self.result: Optional[str] = None
        self._create_dialog(parent, current_cookies)
    
    def _create_dialog(self, parent: tk.Tk, current_cookies: str) -> None:
        """ダイアログウィンドウの作成"""
        self.cookie_window = tk.Toplevel(parent)
        self.cookie_window.title("Cookie設定")
        self.cookie_window.geometry("600x400")
        self.cookie_window.transient(parent)
        self.cookie_window.grab_set()

        self.text_area = tk.Text(self.cookie_window)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text_area.insert("1.0", current_cookies)

        button_frame = tk.Frame(self.cookie_window)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        tk.Button(button_frame, text="保存", command=self._save_cookies).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="キャンセル", command=self._cancel).pack(side=tk.LEFT, padx=5)

    def _save_cookies(self) -> None:
        """Cookieの保存処理"""
        cookie_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
        cookie_dir.mkdir(exist_ok=True, parents=True)
        cookie_file = cookie_dir / "cookies.txt"
        
        cookie_content = self.text_area.get("1.0", tk.END).strip()
        cookie_file.write_text(cookie_content, encoding="utf-8")
        os.chmod(str(cookie_file), 0o600)  # ユーザーのみ読み書き可能に設定
        
        self.result = cookie_content
        self.cookie_window.destroy()

    def _cancel(self) -> None:
        """キャンセル処理"""
        self.cookie_window.destroy()


class MainWindow:
    """メインウィンドウのUI管理クラス"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.resizable(width=False, height=False)
        
        self.state = UIState()
        self.progress_tracker = ProgressTracker(self)
        
        # UIコンポーネントの初期化
        self.notebook: ttk.Notebook
        self.download_tab: tk.Frame
        self.settings_tab: tk.Frame
        self.setting_frame: tk.Frame
        self.cookies_frame: tk.Frame  
        self.button_frame: tk.Frame
        self.progress_bar: ttk.Progressbar
        self.status_label: tk.Label
        self.download_button: tk.Button
        self.stop_button: tk.Button
        self.quality_combobox: ttk.Combobox
        
        # コールバック関数（後で設定される）
        self.start_download_callback: Optional[Callable[[], None]] = None
        self.stop_download_callback: Optional[Callable[[], None]] = None
        self.set_cookies_callback: Optional[Callable[[], None]] = None
        
        self._create_ui()

    def set_callbacks(self, 
                     start_download: Callable[[], None],
                     stop_download: Callable[[], None], 
                     set_cookies: Callable[[], None]) -> None:
        """コールバック関数の設定"""
        self.start_download_callback = start_download
        self.stop_download_callback = stop_download
        self.set_cookies_callback = set_cookies

    def _create_ui(self) -> None:
        """UIコンポーネントの作成と配置"""
        self._create_notebook()
        self._create_download_tab()
        self._create_settings_tab()

    def _create_notebook(self) -> None:
        """ノートブック（タブコンテナ）の作成"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # タブフレームの作成
        self.download_tab = tk.Frame(self.notebook)
        self.settings_tab = tk.Frame(self.notebook)
        
        # タブを追加
        self.notebook.add(self.download_tab, text="ダウンロード")
        self.notebook.add(self.settings_tab, text="設定")

    def _create_download_tab(self) -> None:
        """ダウンロードタブの作成"""
        # フレームの作成
        self.setting_frame = tk.Frame(self.download_tab)
        self.cookies_frame = tk.Frame(self.download_tab)
        self.button_frame = tk.Frame(self.download_tab)
        
        self.setting_frame.pack(padx=10, pady=10)
        self.cookies_frame.pack(fill="x", padx=10, pady=5)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        # セクションの作成
        self._create_save_folder_section()
        self._create_url_section()
        self._create_quality_section()
        self._create_cookies_section()
        self._create_progress_section()
        self._create_button_section()

    def _create_settings_tab(self) -> None:
        """設定タブの作成"""
        # 設定用のフレーム
        settings_frame = tk.Frame(self.settings_tab)
        settings_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # リトライ設定セクション
        self._create_retry_settings_section(settings_frame)
        
        # 詳細設定セクション
        self._create_advanced_settings_section(settings_frame)

    def _create_save_folder_section(self) -> None:
        """保存フォルダ選択セクションの作成"""
        tk.Label(self.setting_frame, text="保存フォルダ:").grid(row=0, column=0, padx=5, pady=5)
        tk.Entry(self.setting_frame, textvariable=self.state.save_folder_var, width=40).grid(
            row=0, column=1, padx=5, pady=5
        )
        tk.Button(self.setting_frame, text="フォルダ選択", command=self._choose_save_folder).grid(
            row=0, column=2, padx=5, pady=5
        )

    def _create_url_section(self) -> None:
        """URL入力セクションの作成"""
        tk.Label(self.setting_frame, text="動画URL:").grid(row=1, column=0, padx=5, pady=5)
        tk.Entry(self.setting_frame, textvariable=self.state.url_var, width=40).grid(
            row=1, column=1, padx=5, pady=5
        )

    def _create_quality_section(self) -> None:
        """画質選択セクションの作成"""
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

    def _create_cookies_section(self) -> None:
        """Cookie設定セクションの作成"""
        tk.Button(
            self.cookies_frame, 
            text="Cookie設定", 
            command=self._on_set_cookies
        ).pack(side="left", padx=5, pady=5)

    def _create_retry_settings_section(self, parent: tk.Widget) -> None:
        """リトライ設定セクションの作成"""
        # リトライ設定グループ
        retry_group = ttk.LabelFrame(parent, text="エラー対応設定", padding=10)
        retry_group.pack(fill="x", pady=(0, 10))
        
        # リトライ有効化チェックボックス
        tk.Checkbutton(
            retry_group,
            variable=self.state.enable_retry,
            text="エラー時の自動リトライを有効にする",
        ).pack(anchor="w", pady=2)
        
        # 最大リトライ回数設定
        retry_count_frame = tk.Frame(retry_group)
        retry_count_frame.pack(anchor="w", pady=2)
        
        tk.Label(retry_count_frame, text="最大リトライ回数:").pack(side="left")
        retry_spinbox = tk.Spinbox(
            retry_count_frame,
            from_=1,
            to=10,
            width=5,
            textvariable=self.state.max_retries
        )
        retry_spinbox.pack(side="left", padx=(5, 0))
        tk.Label(retry_count_frame, text="回").pack(side="left", padx=(2, 0))
        
        # プレイリスト個別ダウンロード設定
        tk.Checkbutton(
            retry_group,
            variable=self.state.enable_individual_download,
            text="プレイリストでエラーが発生した場合、個別動画として再ダウンロードを試行する",
            wraplength=400
        ).pack(anchor="w", pady=2)

    def _create_advanced_settings_section(self, parent: tk.Widget) -> None:
        """詳細設定セクションの作成"""
        # 詳細設定グループ
        advanced_group = ttk.LabelFrame(parent, text="詳細設定", padding=10)
        advanced_group.pack(fill="x", pady=(0, 10))
        
        # Cookie自動更新設定
        tk.Checkbutton(
            advanced_group,
            variable=self.state.get_cookies_from_browser,
            text="ブラウザからCookieを自動取得する（Firefox）",
        ).pack(anchor="w", pady=2)
        
        # 設定保存・読み込みボタン
        button_frame = tk.Frame(advanced_group)
        button_frame.pack(fill="x", pady=(10, 0))
        
        tk.Button(
            button_frame,
            text="設定を保存",
            command=self._save_settings
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            button_frame,
            text="設定を読み込み",
            command=self._load_settings
        ).pack(side="left")
        
        # 説明文
        info_label = tk.Label(
            advanced_group,
            text="※ 設定はアプリケーション終了時に自動保存されます",
            font=("", 8),
            fg="gray"
        )
        info_label.pack(anchor="w", pady=(5, 0))

    def _create_progress_section(self) -> None:
        """プログレスセクションの作成"""
        self.progress_bar = ttk.Progressbar(
            self.button_frame, 
            variable=self.state.progress_var, 
            maximum=100, 
            mode="determinate"
        )
        self.progress_bar.grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.progress_bar.grid_remove()

        self.status_label = tk.Label(self.button_frame, text="")
        self.status_label.grid(row=1, column=0, columnspan=3, padx=5, pady=5)

    def _create_button_section(self) -> None:
        """ボタンセクションの作成"""
        self.button_frame.grid_columnconfigure(0, weight=2)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)
        
        self.download_button = tk.Button(
            self.button_frame, 
            text="ダウンロード開始", 
            command=self._on_start_download
        )
        self.download_button.grid(row=2, column=1, padx=5, pady=5)

        self.stop_button = tk.Button(
            self.button_frame, 
            text="停止", 
            command=self._on_stop_download, 
            state=tk.DISABLED
        )
        self.stop_button.grid(row=2, column=2, padx=5, pady=5)

    def _choose_save_folder(self) -> None:
        """保存フォルダの選択"""
        folder = filedialog.askdirectory()
        if folder:
            self.state.save_folder_var.set(folder)

    def _on_start_download(self) -> None:
        """ダウンロード開始ボタンのイベントハンドラ"""
        if self.start_download_callback:
            self.start_download_callback()

    def _on_stop_download(self) -> None:
        """停止ボタンのイベントハンドラ"""
        if self.stop_download_callback:
            self.stop_download_callback()

    def _on_set_cookies(self) -> None:
        """Cookie設定ボタンのイベントハンドラ"""
        if self.set_cookies_callback:
            self.set_cookies_callback()

    def show_cookie_dialog(self, current_cookies: str) -> Optional[str]:
        """Cookie設定ダイアログの表示"""
        dialog = CookieDialog(self.root, current_cookies)
        self.root.wait_window(dialog.cookie_window)
        return dialog.result

    def set_download_in_progress(self, in_progress: bool) -> None:
        """ダウンロード中の状態に応じてUIを更新"""
        if in_progress:
            self.download_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.progress_tracker.show_progress()
            self.state.progress_var.set(0)
        else:
            self.download_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.progress_tracker.hide_progress()

    def show_error(self, title: str, message: str) -> None:
        """エラーダイアログの表示"""
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str) -> None:
        """情報ダイアログの表示"""
        messagebox.showinfo(title, message)
    
    def show_question(self, title: str, message: str) -> bool:
        """質問ダイアログの表示"""
        return messagebox.askyesno(title, message)

    def _save_settings(self) -> None:
        """設定の保存"""
        try:
            import json
            from pathlib import Path
            
            settings = {
                "enable_retry": self.state.enable_retry.get(),
                "max_retries": self.state.max_retries.get(),
                "enable_individual_download": self.state.enable_individual_download.get(),
                "get_cookies_from_browser": self.state.get_cookies_from_browser.get(),
                "quality_default": self.state.quality_var.get(),
                "last_save_folder": self.state.save_folder_var.get()
            }
            
            settings_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
            settings_dir.mkdir(exist_ok=True, parents=True)
            settings_file = settings_dir / "settings.json"
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            self.show_info("設定保存", "設定を保存しました")
            
        except Exception as e:
            self.show_error("設定保存エラー", f"設定の保存に失敗しました: {str(e)}")

    def _load_settings(self) -> None:
        """設定の読み込み"""
        try:
            import json
            from pathlib import Path
            
            settings_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
            settings_file = settings_dir / "settings.json"
            
            if not settings_file.exists():
                self.show_info("設定読み込み", "保存された設定が見つかりません")
                return
            
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # 設定を復元
            self.state.enable_retry.set(settings.get("enable_retry", True))
            self.state.max_retries.set(settings.get("max_retries", 3))
            self.state.enable_individual_download.set(settings.get("enable_individual_download", True))
            self.state.get_cookies_from_browser.set(settings.get("get_cookies_from_browser", False))
            
            if settings.get("quality_default"):
                self.state.quality_var.set(settings["quality_default"])
            
            if settings.get("last_save_folder"):
                self.state.save_folder_var.set(settings["last_save_folder"])
            
            self.show_info("設定読み込み", "設定を読み込みました")
            
        except Exception as e:
            self.show_error("設定読み込みエラー", f"設定の読み込みに失敗しました: {str(e)}")

    def load_settings_on_startup(self) -> None:
        """起動時の設定読み込み"""
        try:
            import json
            from pathlib import Path
            
            settings_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
            settings_file = settings_dir / "settings.json"
            
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # 設定を復元（エラーダイアログは表示しない）
                self.state.enable_retry.set(settings.get("enable_retry", True))
                self.state.max_retries.set(settings.get("max_retries", 3))
                self.state.enable_individual_download.set(settings.get("enable_individual_download", True))
                self.state.get_cookies_from_browser.set(settings.get("get_cookies_from_browser", False))
                
                if settings.get("quality_default"):
                    self.state.quality_var.set(settings["quality_default"])
                
                if settings.get("last_save_folder"):
                    self.state.save_folder_var.set(settings["last_save_folder"])
                    
        except Exception:
            # 起動時は静かに失敗する
            pass

    def save_settings_on_exit(self) -> None:
        """終了時の設定保存"""
        try:
            import json
            from pathlib import Path
            
            settings = {
                "enable_retry": self.state.enable_retry.get(),
                "max_retries": self.state.max_retries.get(),
                "enable_individual_download": self.state.enable_individual_download.get(),
                "get_cookies_from_browser": self.state.get_cookies_from_browser.get(),
                "quality_default": self.state.quality_var.get(),
                "last_save_folder": self.state.save_folder_var.get()
            }
            
            settings_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
            settings_dir.mkdir(exist_ok=True, parents=True)
            settings_file = settings_dir / "settings.json"
            
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
        except Exception:
            # 終了時は静かに失敗する
            pass