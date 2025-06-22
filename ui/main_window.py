"""メインウィンドウのUI管理"""

from __future__ import annotations

import json
import os
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk

import config
from ui.components import ProgressTracker, UIState
from ui.theme import (
    IconManager,
    ModernTheme,
)


class CookieDialog:
    """Cookie設定ダイアログ"""

    def __init__(self, parent: tk.Tk, current_cookies: str) -> None:
        self.result: str | None = None
        self._create_dialog(parent, current_cookies)

    def _create_dialog(self, parent: tk.Tk, current_cookies: str) -> None:
        """ダイアログウィンドウの作成"""
        self.cookie_window = tk.Toplevel(parent)
        self.cookie_window.title("🍪 Cookie設定")

        # ダイアログサイズの設定
        dialog_width = 700
        dialog_height = 500

        # 親ウィンドウの位置とサイズを取得
        parent.update_idletasks()  # ウィンドウサイズを確実に取得
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # 親ウィンドウの中央に配置する座標を計算
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # 画面の境界を超えないように調整
        screen_width = self.cookie_window.winfo_screenwidth()
        screen_height = self.cookie_window.winfo_screenheight()
        x = max(0, min(x, screen_width - dialog_width))
        y = max(0, min(y, screen_height - dialog_height))

        self.cookie_window.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        self.cookie_window.transient(parent)
        self.cookie_window.grab_set()
        self.cookie_window.resizable(True, True)
        self.cookie_window.minsize(500, 300)

        # CustomTkinterのダイアログスタイルを適用
        self.cookie_window.configure(bg=ModernTheme.CTK_COLORS["bg_dark"])

        # メインコンテナ
        main_container = ctk.CTkFrame(self.cookie_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # タイトルと説明
        title_label = ctk.CTkLabel(
            main_container,
            text=f"{IconManager.get('cookie')} Cookie設定",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(anchor="w", pady=(0, 10))

        info_label = ctk.CTkLabel(
            main_container,
            text="メンバー限定動画をダウンロードするためのCookieを設定してください",
            text_color=ModernTheme.CTK_COLORS["text_muted"]
        )
        info_label.pack(anchor="w", pady=(0, 15))

        # テキストエリア用フレーム
        text_frame = ctk.CTkFrame(main_container)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # CustomTkinterのテキストボックス
        self.text_area = ctk.CTkTextbox(
            text_frame,
            width=600,
            height=300,
            wrap="word",
            font=ctk.CTkFont(size=12)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.text_area.insert("1.0", current_cookies)

        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(fill=tk.X)

        # ボタンを右寄せ
        button_container = ctk.CTkFrame(button_frame, fg_color="transparent")
        button_container.pack(side=tk.RIGHT)

        # CustomTkinterボタン
        cancel_btn = ctk.CTkButton(
            button_container,
            text=f"{IconManager.get('error')} キャンセル",
            command=self._cancel,
            width=100,
            height=32,
            fg_color=ModernTheme.CTK_COLORS["button_secondary"],
            hover_color=ModernTheme.CTK_COLORS["button_secondary_hover"]
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        save_btn = ctk.CTkButton(
            button_container,
            text=f"{IconManager.get('check')} 保存",
            command=self._save_cookies,
            width=100,
            height=32,
            fg_color=ModernTheme.CTK_COLORS["button_primary"],
            hover_color=ModernTheme.CTK_COLORS["button_primary_hover"]
        )
        save_btn.pack(side=tk.LEFT)

        # フォーカスを設定
        self.text_area.focus_set()

    def _save_cookies(self) -> None:
        """Cookieの保存処理"""
        # Windows専用: %USERPROFILE%\AppData\Local\yt-downloader
        cookie_dir = Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "yt-downloader"
        cookie_dir.mkdir(exist_ok=True, parents=True)
        cookie_file = cookie_dir / "cookies.txt"

        cookie_content = self.text_area.get("1.0", "end").strip()
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
        # CustomTkinterのテーマ設定
        ctk.set_appearance_mode("system")  # システムのテーマに合わせる
        ctk.set_default_color_theme("blue")  # ブルーカラーテーマでモダンな印象

        self.root = root
        self.root.title("yt_downloader")
        self.root.resizable(width=True, height=True)

        # ウィンドウサイズの設定（テーマから取得）
        window_width = ModernTheme.WINDOW_SIZE["width"]
        window_height = ModernTheme.WINDOW_SIZE["height"]
        min_width = ModernTheme.WINDOW_SIZE["min_width"]
        min_height = ModernTheme.WINDOW_SIZE["min_height"]

        self.root.minsize(min_width, min_height)
        self.root.geometry(f"{window_width}x{window_height}")

        # ウィンドウを画面中央に配置
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (window_width // 2)
        y = (self.root.winfo_screenheight() // 2) - (window_height // 2)
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # ウィンドウを最前面に表示
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        self.root.focus_force()

        # CustomTkinterのルートウィンドウに変換
        try:
            if not isinstance(root, ctk.CTk):
                # 既存のrootがTkinterの場合、CustomTkinter用に設定
                self.root.configure(bg=ModernTheme.CTK_COLORS["bg_dark"])
        except (TypeError, AttributeError):
            # テスト時やモック使用時は無視
            pass

        self.state = UIState()
        self.progress_tracker = ProgressTracker(self)

        # UIコンポーネントの初期化
        self.tabview: ctk.CTkTabview
        self.download_tab: ctk.CTkFrame
        self.settings_tab: ctk.CTkFrame
        self.cookies_frame: ctk.CTkFrame
        self.button_frame: ctk.CTkFrame
        self.progress_bar: ctk.CTkProgressBar
        self.status_label: ctk.CTkLabel
        self.download_button: ctk.CTkButton
        self.stop_button: ctk.CTkButton
        self.quality_combobox: ctk.CTkComboBox

        # コールバック関数（後で設定される）
        self.start_download_callback: Callable[[], None] | None = None
        self.stop_download_callback: Callable[[], None] | None = None
        self.set_cookies_callback: Callable[[], None] | None = None

        self._create_ui()

    def set_callbacks(
        self, start_download: Callable[[], None], stop_download: Callable[[], None], set_cookies: Callable[[], None]
    ) -> None:
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
        """タブビューの作成"""
        # CustomTkinterのタブビューを使用
        tabview_width = ModernTheme.WINDOW_SIZE["tabview_width"]
        tabview_height = ModernTheme.WINDOW_SIZE["tabview_height"]
        tab_padding = ModernTheme.SPACING["section_padding"]

        self.tabview = ctk.CTkTabview(self.root, width=tabview_width, height=tabview_height)
        self.tabview.pack(fill="both", expand=True, padx=tab_padding, pady=tab_padding)

        # タブを追加
        self.download_tab = self.tabview.add(f"{IconManager.get('download')} ダウンロード")
        self.settings_tab = self.tabview.add(f"{IconManager.get('settings')} 設定")

    def _create_download_tab(self) -> None:
        """ダウンロードタブの作成"""
        # 設定カード（直接設定項目を配置）
        settings_card = self._create_card(self.download_tab, "基本設定")
        self._create_settings_content(settings_card)

        # Cookie設定カード
        cookies_card = self._create_card(self.download_tab, f"{IconManager.get('cookie')} Cookie設定")
        self._create_cookies_content(cookies_card)

        # プログレス表示カード
        progress_card = self._create_card(self.download_tab, f"{IconManager.get('info')} ダウンロード状況")
        self._create_progress_content(progress_card)

        # ボタンセクション
        button_padding = ModernTheme.SPACING["section_padding"]
        button_margin = ModernTheme.SPACING["card_padding"]

        self.button_frame = ctk.CTkFrame(self.download_tab, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=button_padding, pady=button_margin)
        self._create_button_section()

    def _create_card(self, parent, title: str) -> ctk.CTkFrame:
        """カードレイアウトの作成"""
        card_padding = ModernTheme.SPACING["section_padding"]
        card_margin = ModernTheme.SPACING["card_padding"]

        card_frame = ctk.CTkFrame(parent, corner_radius=10, border_width=1)
        card_frame.pack(fill="x", padx=card_padding, pady=card_margin)

        # カードヘッダー
        header_padding = ModernTheme.SPACING["card_padding"]

        title_label = ctk.CTkLabel(
            card_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(anchor="w", padx=header_padding, pady=(10, 5))

        return card_frame

    def _create_settings_content(self, parent: ctk.CTkFrame) -> None:
        """設定カード内のコンテンツを作成"""
        # 設定コンテンツエリア
        content_padding = ModernTheme.SPACING["card_padding"]

        content_frame = ctk.CTkFrame(parent, fg_color="transparent")
        content_frame.pack(fill="x", padx=content_padding, pady=content_padding)

        # 保存フォルダセクション
        # ラベル
        folder_label = ctk.CTkLabel(content_frame, text=f"{IconManager.get('folder')} 保存フォルダ:")
        folder_label.grid(row=0, column=0, padx=(0, 10), pady=15, sticky="w")

        # エントリ（CustomTkinter）
        self.save_folder_entry = ctk.CTkEntry(
            content_frame,
            textvariable=self.state.save_folder_var,
            width=350,
            height=32,
        )
        self.save_folder_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew")

        # ボタン（CustomTkinter）
        folder_btn = ctk.CTkButton(
            content_frame,
            text=f"{IconManager.get('folder')} 選択",
            command=self._choose_save_folder,
            width=100,
            height=32,
        )
        folder_btn.grid(row=0, column=2, padx=(10, 0), pady=15)

        # URL セクション
        # ラベル
        url_label = ctk.CTkLabel(content_frame, text="🔗 動画URL:")
        url_label.grid(row=1, column=0, padx=(0, 10), pady=15, sticky="w")

        # エントリ（CustomTkinter）
        self.url_entry = ctk.CTkEntry(
            content_frame,
            textvariable=self.state.url_var,
            width=450,
            height=32,
            placeholder_text="YouTubeのURLを入力してください"
        )
        self.url_entry.grid(row=1, column=1, columnspan=2, padx=(10, 0), pady=15, sticky="ew")

        # 画質セクション
        # ラベル
        quality_label = ctk.CTkLabel(content_frame, text="🎬 画質:")
        quality_label.grid(row=2, column=0, padx=(0, 10), pady=15, sticky="w")

        # コンボボックス（CustomTkinter）
        self.quality_combobox = ctk.CTkComboBox(
            content_frame,
            variable=self.state.quality_var,
            values=config.quality_options,
            state="readonly",
            width=450,
            height=32,
        )
        self.quality_combobox.set(config.quality_options[config.quality_default_idx])
        self.quality_combobox.grid(row=2, column=1, columnspan=2, padx=(10, 0), pady=15, sticky="ew")

        # グリッドの設定
        content_frame.grid_columnconfigure(1, weight=1)

        # 設定変更時の自動保存を設定
        self.state.save_folder_var.trace('w', lambda *args: self._auto_save_settings())
        self.state.url_var.trace('w', lambda *args: self._auto_save_settings())
        self.state.quality_var.trace('w', lambda *args: self._auto_save_settings())

    def _create_cookies_content(self, parent: ctk.CTkFrame) -> None:
        """Cookie設定カード内のコンテンツを作成"""
        # Cookie設定コンテンツ
        content_padding = ModernTheme.SPACING["card_padding"]

        cookie_content = ctk.CTkFrame(parent, fg_color="transparent")
        cookie_content.pack(fill="x", padx=content_padding, pady=content_padding)

        # 上段: Cookie設定ボタンと説明
        top_row = ctk.CTkFrame(cookie_content, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))

        # Cookie設定ボタン
        cookie_btn = ctk.CTkButton(
            top_row,
            text=f"{IconManager.get('cookie')} Cookie設定",
            command=self._on_set_cookies,
            width=120,
            height=32,
        )
        cookie_btn.pack(side="left", padx=10)

        # 説明ラベル
        info_label = ctk.CTkLabel(
            top_row,
            text="※ メンバー限定動画をダウンロードするにはCookieの設定が必要です",
            text_color=ModernTheme.CTK_COLORS["text_muted"]
        )
        info_label.pack(side="left", padx=(20, 0))

        # 下段: ブラウザからCookie取得設定
        bottom_row = ctk.CTkFrame(cookie_content, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(20, 0))

        # ブラウザCookie取得チェックボックス
        browser_cookie_check = ctk.CTkCheckBox(
            bottom_row,
            variable=self.state.get_cookies_from_browser,
            text=f"{IconManager.get('refresh')} ブラウザ（Firefox）からCookieを自動取得する",
            command=self._auto_save_settings
        )
        browser_cookie_check.pack(side="left", padx=10)

        # ブラウザCookie設定の説明
        browser_info_label = ctk.CTkLabel(
            bottom_row,
            text="※ この設定を有効にすると、手動でCookieを設定する必要がありません",
            text_color=ModernTheme.CTK_COLORS["text_muted"]
        )
        browser_info_label.pack(side="left", padx=(10, 0))

    def _create_progress_content(self, parent: ctk.CTkFrame) -> None:
        """プログレス表示カード内のコンテンツを作成"""
        # プログレスコンテンツ
        content_padding = ModernTheme.SPACING["card_padding"]

        progress_content = ctk.CTkFrame(parent, fg_color="transparent")
        progress_content.pack(fill="x", padx=content_padding, pady=content_padding)

        # ステータスラベル（常に表示）
        self.status_label = ctk.CTkLabel(
            progress_content,
            text="ダウンロード開始ボタンを押してください",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(fill="x", pady=(0, 15))

        # プログレスバー用のプレースホルダーフレーム（常に表示でスペースを確保）
        self.progress_placeholder = ctk.CTkFrame(progress_content, fg_color="transparent", height=34)
        self.progress_placeholder.pack(fill="x", pady=(0, 10))
        self.progress_placeholder.pack_propagate(False)  # 高さを固定

        # プログレスバー（CustomTkinter）
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_placeholder,
            width=500,
            height=24,
            progress_color=ModernTheme.CTK_COLORS["progress_bar"],
            corner_radius=12
        )
        # 初期状態では非表示
        self.progress_bar.set(0)

    def _auto_save_settings(self) -> None:
        """設定の自動保存"""
        try:
            settings = {
                "enable_retry": self.state.enable_retry.get(),
                "max_retries": self.state.max_retries.get(),
                "enable_individual_download": self.state.enable_individual_download.get(),
                "get_cookies_from_browser": self.state.get_cookies_from_browser.get(),
                "quality_default": self.state.quality_var.get(),
                "last_save_folder": self.state.save_folder_var.get(),
            }

            # Windows専用: %USERPROFILE%\AppData\Local\yt-downloader
            settings_dir = Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "yt-downloader"
            settings_dir.mkdir(exist_ok=True, parents=True)
            settings_file = settings_dir / "settings.json"

            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

        except Exception:
            # 自動保存では静かに失敗する
            pass

    def _create_settings_tab(self) -> None:
        """設定タブの作成"""
        # エラー対応設定カード
        retry_card = self._create_card(self.settings_tab, "エラー対応設定")
        self._create_retry_settings_section(retry_card)



    def _create_retry_settings_section(self, parent: ctk.CTkFrame) -> None:
        """リトライ設定セクションの作成"""
        # リトライ設定コンテンツ
        content_padding = ModernTheme.SPACING["card_padding"]

        retry_content = ctk.CTkFrame(parent, fg_color="transparent")
        retry_content.pack(fill="x", padx=content_padding, pady=content_padding)

        # リトライ有効化チェックボックス
        retry_check = ctk.CTkCheckBox(
            retry_content,
            variable=self.state.enable_retry,
            text="エラー時の自動リトライを有効にする",
            command=self._auto_save_settings
        )
        retry_check.pack(anchor="w", pady=(0, 10))

        # 最大リトライ回数設定
        retry_count_frame = ctk.CTkFrame(retry_content, fg_color="transparent")
        retry_count_frame.pack(anchor="w", pady=(0, 10))

        retry_label = ctk.CTkLabel(retry_count_frame, text="最大リトライ回数:")
        retry_label.pack(side="left")

        # CustomTkinterにはSpinboxがないので、Entryで代用
        retry_entry = ctk.CTkEntry(
            retry_count_frame,
            textvariable=self.state.max_retries,
            width=50,
            height=28
        )
        retry_entry.pack(side="left", padx=(5, 0))
        # リトライ回数変更時の自動保存
        self.state.max_retries.trace('w', lambda *args: self._auto_save_settings())

        retry_unit_label = ctk.CTkLabel(retry_count_frame, text="回")
        retry_unit_label.pack(side="left", padx=(5, 0))

        # プレイリスト個別ダウンロード設定
        individual_check = ctk.CTkCheckBox(
            retry_content,
            variable=self.state.enable_individual_download,
            text="プレイリストでエラーが発生した場合、個別動画として再ダウンロードを試行する",
            command=self._auto_save_settings
        )
        individual_check.pack(anchor="w")



    def _create_button_section(self) -> None:
        """ボタンセクションの作成"""
        # ボタン用フレーム
        section_padding = ModernTheme.SPACING["section_padding"]

        button_container = ctk.CTkFrame(self.button_frame, fg_color="transparent")
        button_container.pack(fill="x", pady=section_padding)

        # ボタンを中央に配置
        button_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        button_frame.pack()

        # ダウンロードボタン（大きなプライマリボタン）
        self.download_button = ctk.CTkButton(
            button_frame,
            text=f"{IconManager.get('play')} ダウンロード開始",
            command=self._on_start_download,
            width=180,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=ModernTheme.CTK_COLORS["button_primary"],
            hover_color=ModernTheme.CTK_COLORS["button_primary_hover"]
        )
        self.download_button.pack(side="left", padx=10)

        # 停止ボタン
        self.stop_button = ctk.CTkButton(
            button_frame,
            text=f"{IconManager.get('stop')} 停止",
            command=self._on_stop_download,
            state=tk.DISABLED,
            width=120,
            height=40,
            fg_color=ModernTheme.CTK_COLORS["button_danger"],
            hover_color=ModernTheme.CTK_COLORS["button_danger_hover"]
        )
        self.stop_button.pack(side="left", padx=10)

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

    def show_cookie_dialog(self, current_cookies: str) -> str | None:
        """Cookie設定ダイアログの表示"""
        dialog = CookieDialog(self.root, current_cookies)
        self.root.wait_window(dialog.cookie_window)
        return dialog.result

    def set_download_in_progress(self, in_progress: bool) -> None:
        """ダウンロード中の状態に応じてUIを更新"""
        if in_progress:
            # ボタン状態の更新
            self.download_button.configure(state="disabled")
            self.download_button.configure(text=f"{IconManager.get('pause')} ダウンロード中...")
            self.stop_button.configure(state="normal")

            # プログレスバー表示
            self.progress_tracker.show_progress()
            self.progress_bar.set(0)
        else:
            # ボタン状態の復元
            self.download_button.configure(state="normal")
            self.download_button.configure(text=f"{IconManager.get('play')} ダウンロード開始")
            self.stop_button.configure(state="disabled")

            # プログレスバー非表示
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

            settings = {
                "enable_retry": self.state.enable_retry.get(),
                "max_retries": self.state.max_retries.get(),
                "enable_individual_download": self.state.enable_individual_download.get(),
                "get_cookies_from_browser": self.state.get_cookies_from_browser.get(),
                "quality_default": self.state.quality_var.get(),
                "last_save_folder": self.state.save_folder_var.get(),
            }

            # Windows専用: %USERPROFILE%\AppData\Local\yt-downloader
            settings_dir = Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "yt-downloader"
            settings_dir.mkdir(exist_ok=True, parents=True)
            settings_file = settings_dir / "settings.json"

            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

            self.show_info("設定保存", "設定を保存しました")

        except Exception as e:
            self.show_error("設定保存エラー", f"設定の保存に失敗しました: {str(e)}")

    def load_settings_on_startup(self) -> None:
        """起動時の設定読み込み"""
        try:

            # Windows専用: %USERPROFILE%\AppData\Local\yt-downloader
            settings_dir = Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "yt-downloader"
            settings_file = settings_dir / "settings.json"

            if settings_file.exists():
                with open(settings_file, "r", encoding="utf-8") as f:
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

            settings = {
                "enable_retry": self.state.enable_retry.get(),
                "max_retries": self.state.max_retries.get(),
                "enable_individual_download": self.state.enable_individual_download.get(),
                "get_cookies_from_browser": self.state.get_cookies_from_browser.get(),
                "quality_default": self.state.quality_var.get(),
                "last_save_folder": self.state.save_folder_var.get(),
            }

            # Windows専用: %USERPROFILE%\AppData\Local\yt-downloader
            settings_dir = Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "yt-downloader"
            settings_dir.mkdir(exist_ok=True, parents=True)
            settings_file = settings_dir / "settings.json"

            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

        except Exception:
            # 終了時は静かに失敗する
            pass
