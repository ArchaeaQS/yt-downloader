"""メインウィンドウのUI管理"""

from __future__ import annotations

import json
import os
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import config
from ui.components import ProgressTracker, UIState
from ui.theme import (
    AnimatedProgressbar,
    IconManager,
    ModernTheme,
    StyledButton,
    StyledFrame,
    StyledLabel,
    apply_theme_to_widget,
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

        # モダンテーマを適用
        apply_theme_to_widget(self.cookie_window)
        self.cookie_window.configure(bg=ModernTheme.COLORS["bg_primary"])

        # メインコンテナ
        main_container = StyledFrame(self.cookie_window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING["md"], pady=ModernTheme.SPACING["md"])

        # タイトルと説明
        title_label = StyledLabel(main_container, text=f"{IconManager.get('cookie')} Cookie設定", style="heading")
        title_label.pack(anchor="w", pady=(0, ModernTheme.SPACING["sm"]))

        info_label = StyledLabel(
            main_container, text="メンバー限定動画をダウンロードするためのCookieを設定してください", style="muted"
        )
        info_label.pack(anchor="w", pady=(0, ModernTheme.SPACING["md"]))

        # テキストエリア用フレーム
        text_frame = StyledFrame(main_container, style="card")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, ModernTheme.SPACING["md"]))

        # スクロールバー付きテキストエリア
        text_container = tk.Frame(text_frame, bg=ModernTheme.COLORS["bg_primary"])
        text_container.pack(fill=tk.BOTH, expand=True, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"])

        self.text_area = tk.Text(
            text_container,
            font=ModernTheme.FONTS["default"],
            bg=ModernTheme.COLORS["bg_primary"],
            fg=ModernTheme.COLORS["text_primary"],
            insertbackground=ModernTheme.COLORS["primary"],
            selectbackground=ModernTheme.COLORS["primary_light"],
            relief="flat",
            wrap=tk.WORD,
        )

        # スクロールバー
        scrollbar = tk.Scrollbar(text_container, command=self.text_area.yview)
        self.text_area.config(yscrollcommand=scrollbar.set)

        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_area.insert("1.0", current_cookies)

        # ボタンフレーム
        button_frame = StyledFrame(main_container)
        button_frame.pack(fill=tk.X)

        # ボタンを右寄せ
        button_container = StyledFrame(button_frame)
        button_container.pack(side=tk.RIGHT)

        # スタイル付きボタン
        cancel_btn = StyledButton(
            button_container, text=f"{IconManager.get('error')} キャンセル", style="secondary", command=self._cancel
        )
        cancel_btn.pack(side=tk.LEFT, padx=(0, ModernTheme.SPACING["sm"]))

        save_btn = StyledButton(
            button_container, text=f"{IconManager.get('check')} 保存", style="primary", command=self._save_cookies
        )
        save_btn.pack(side=tk.LEFT)

        # フォーカスを設定
        self.text_area.focus_set()

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
        self.root.title("🎥 YouTube Downloader")
        self.root.resizable(width=True, height=True)
        self.root.minsize(600, 500)

        # テーマの適用
        apply_theme_to_widget(self.root)
        self.root.configure(bg=ModernTheme.COLORS["bg_primary"])

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
        """ノートブック（タブコンテナ）の作成"""
        # カスタムスタイルを適用
        style = ttk.Style()
        style.theme_use("clam")

        # タブのスタイルをカスタマイズ
        style.configure("Custom.TNotebook", background=ModernTheme.COLORS["bg_primary"], borderwidth=0)
        style.configure(
            "Custom.TNotebook.Tab",
            background=ModernTheme.COLORS["bg_secondary"],
            foreground=ModernTheme.COLORS["text_primary"],
            padding=[20, 12],
            font=ModernTheme.FONTS["default"],
        )
        style.map(
            "Custom.TNotebook.Tab",
            background=[("selected", ModernTheme.COLORS["primary"]), ("active", ModernTheme.COLORS["primary_light"])],
            foreground=[
                ("selected", ModernTheme.COLORS["text_white"]),
                ("active", ModernTheme.COLORS["text_primary"]),
            ],
        )

        self.notebook = ttk.Notebook(self.root, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=ModernTheme.SPACING["md"], pady=ModernTheme.SPACING["md"])

        # タブフレームの作成（スタイル付き）
        self.download_tab = StyledFrame(self.notebook, style="card")
        self.settings_tab = StyledFrame(self.notebook, style="card")

        # タブを追加（アイコン付き）
        self.notebook.add(self.download_tab, text=f"{IconManager.get('download')} ダウンロード")
        self.notebook.add(self.settings_tab, text=f"{IconManager.get('settings')} 設定")

    def _create_download_tab(self) -> None:
        """ダウンロードタブの作成"""
        # メインコンテナ
        main_container = StyledFrame(self.download_tab)
        main_container.pack(fill="both", expand=True, padx=ModernTheme.SPACING["lg"], pady=ModernTheme.SPACING["lg"])

        # タイトル
        title_label = StyledLabel(
            main_container, text=f"{IconManager.get('download')} 動画ダウンロード", style="heading"
        )
        title_label.pack(anchor="w", pady=(0, ModernTheme.SPACING["lg"]))

        # 設定カード
        settings_card = self._create_card(main_container, "基本設定")

        # フレームの作成
        self.setting_frame = StyledFrame(settings_card)
        self.cookies_frame = StyledFrame(main_container)
        self.button_frame = StyledFrame(main_container)

        self.setting_frame.pack(fill="x", padx=ModernTheme.SPACING["md"], pady=ModernTheme.SPACING["md"])
        self.cookies_frame.pack(fill="x", pady=(ModernTheme.SPACING["lg"], ModernTheme.SPACING["md"]))
        self.button_frame.pack(fill="x", pady=ModernTheme.SPACING["md"])

        # セクションの作成
        self._create_save_folder_section()
        self._create_url_section()
        self._create_quality_section()
        self._create_cookies_section()
        self._create_progress_section()
        self._create_button_section()

    def _create_card(self, parent, title: str) -> tk.Frame:
        """カードレイアウトの作成"""
        card_frame = StyledFrame(parent, style="card")
        card_frame.pack(fill="x", pady=ModernTheme.SPACING["md"])

        # カードヘッダー
        header_frame = StyledFrame(card_frame, bg=ModernTheme.COLORS["bg_secondary"])
        header_frame.pack(fill="x")

        title_label = StyledLabel(header_frame, text=title, style="heading", bg=ModernTheme.COLORS["bg_secondary"])
        title_label.pack(anchor="w", padx=ModernTheme.SPACING["md"], pady=ModernTheme.SPACING["sm"])

        return card_frame

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
        # ラベル
        label = StyledLabel(self.setting_frame, text=f"{IconManager.get('folder')} 保存フォルダ:")
        label.grid(row=0, column=0, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"], sticky="w")

        # エントリ（スタイル付き）
        entry = tk.Entry(
            self.setting_frame,
            textvariable=self.state.save_folder_var,
            width=45,
            font=ModernTheme.FONTS["default"],
            relief="solid",
            bd=1,
            bg=ModernTheme.COLORS["bg_primary"],
            fg=ModernTheme.COLORS["text_primary"],
        )
        entry.grid(row=0, column=1, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"], sticky="ew")

        # ボタン（スタイル付き）
        folder_btn = StyledButton(
            self.setting_frame,
            text=f"{IconManager.get('folder')} 選択",
            style="secondary",
            command=self._choose_save_folder,
        )
        folder_btn.grid(row=0, column=2, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"])

        # グリッドの設定
        self.setting_frame.grid_columnconfigure(1, weight=1)

    def _create_url_section(self) -> None:
        """URL入力セクションの作成"""
        # ラベル
        label = StyledLabel(self.setting_frame, text="🔗 動画URL:")
        label.grid(row=1, column=0, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"], sticky="w")

        # エントリ（スタイル付き）
        entry = tk.Entry(
            self.setting_frame,
            textvariable=self.state.url_var,
            width=45,
            font=ModernTheme.FONTS["default"],
            relief="solid",
            bd=1,
            bg=ModernTheme.COLORS["bg_primary"],
            fg=ModernTheme.COLORS["text_primary"],
        )
        entry.grid(
            row=1, column=1, columnspan=2, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"], sticky="ew"
        )

    def _create_quality_section(self) -> None:
        """画質選択セクションの作成"""
        # ラベル
        label = StyledLabel(self.setting_frame, text="🎬 画質:")
        label.grid(row=2, column=0, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"], sticky="w")

        # コンボボックス（スタイル付き）
        style = ttk.Style()
        style.configure(
            "Quality.TCombobox",
            fieldbackground=ModernTheme.COLORS["bg_primary"],
            background=ModernTheme.COLORS["bg_secondary"],
            foreground=ModernTheme.COLORS["text_primary"],
            arrowcolor=ModernTheme.COLORS["primary"],
        )

        self.quality_combobox = ttk.Combobox(
            self.setting_frame,
            textvariable=self.state.quality_var,
            values=config.quality_options,
            state="readonly",
            width=42,
            style="Quality.TCombobox",
            font=ModernTheme.FONTS["default"],
        )
        self.quality_combobox.set(config.quality_options[config.quality_default_idx])
        self.quality_combobox.grid(
            row=2, column=1, columnspan=2, padx=ModernTheme.SPACING["sm"], pady=ModernTheme.SPACING["sm"], sticky="ew"
        )

    def _create_cookies_section(self) -> None:
        """Cookie設定セクションの作成"""
        # Cookieカード
        cookie_card = self._create_card(self.cookies_frame.master, f"{IconManager.get('cookie')} Cookie設定")

        cookie_content = StyledFrame(cookie_card)
        cookie_content.pack(fill="x", padx=ModernTheme.SPACING["md"], pady=ModernTheme.SPACING["md"])

        # 上段: Cookie設定ボタンと説明
        top_row = StyledFrame(cookie_content)
        top_row.pack(fill="x", pady=(0, ModernTheme.SPACING["sm"]))

        # Cookie設定ボタン
        cookie_btn = StyledButton(
            top_row, text=f"{IconManager.get('cookie')} Cookie設定", style="secondary", command=self._on_set_cookies
        )
        cookie_btn.pack(side="left", padx=ModernTheme.SPACING["sm"])

        # 説明ラベル
        info_label = StyledLabel(
            top_row, text="メンバー限定動画をダウンロードするにはCookieの設定が必要です", style="muted"
        )
        info_label.pack(side="left", padx=(ModernTheme.SPACING["lg"], 0))

        # 下段: ブラウザからCookie取得設定
        bottom_row = StyledFrame(cookie_content)
        bottom_row.pack(fill="x")

        # ブラウザCookie取得チェックボックス
        browser_cookie_check = tk.Checkbutton(
            bottom_row,
            variable=self.state.get_cookies_from_browser,
            text=f"{IconManager.get('refresh')} ブラウザ（Firefox）からCookieを自動取得する",
            font=ModernTheme.FONTS["default"],
            bg=ModernTheme.COLORS["bg_primary"],
            fg=ModernTheme.COLORS["text_primary"],
            selectcolor=ModernTheme.COLORS["bg_primary"],
            activebackground=ModernTheme.COLORS["bg_primary"],
            activeforeground=ModernTheme.COLORS["text_primary"],
        )
        browser_cookie_check.pack(anchor="w", padx=ModernTheme.SPACING["sm"])

        # ブラウザCookie設定の説明
        browser_info_label = StyledLabel(
            bottom_row, text="※ この設定を有効にすると、手動でCookieを設定する必要がありません", style="muted"
        )
        browser_info_label.pack(
            anchor="w",
            padx=(ModernTheme.SPACING["lg"], ModernTheme.SPACING["sm"]),
            pady=(ModernTheme.SPACING["xs"], 0),
        )

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
        retry_spinbox = tk.Spinbox(retry_count_frame, from_=1, to=10, width=5, textvariable=self.state.max_retries)
        retry_spinbox.pack(side="left", padx=(5, 0))
        tk.Label(retry_count_frame, text="回").pack(side="left", padx=(2, 0))

        # プレイリスト個別ダウンロード設定
        tk.Checkbutton(
            retry_group,
            variable=self.state.enable_individual_download,
            text="プレイリストでエラーが発生した場合、個別動画として再ダウンロードを試行する",
            wraplength=400,
        ).pack(anchor="w", pady=2)

    def _create_advanced_settings_section(self, parent: tk.Widget) -> None:
        """詳細設定セクションの作成"""
        # 詳細設定グループ
        advanced_group = ttk.LabelFrame(parent, text="詳細設定", padding=10)
        advanced_group.pack(fill="x", pady=(0, 10))

        # 設定保存ボタン
        save_button = StyledButton(
            advanced_group,
            text=f"{IconManager.get('save')} 設定を保存",
            style="secondary",
            command=self._save_settings,
        )
        save_button.pack(anchor="w", pady=(10, 0))

        # 説明文
        info_label = tk.Label(
            advanced_group, text="※ 設定はアプリケーション終了時に自動保存されます", font=("", 8), fg="gray"
        )
        info_label.pack(anchor="w", pady=(5, 0))

    def _create_progress_section(self) -> None:
        """プログレスセクションの作成"""
        # プログレスカード
        progress_card = self._create_card(self.button_frame.master, f"{IconManager.get('info')} ダウンロード状況")

        progress_content = StyledFrame(progress_card)
        progress_content.pack(fill="x", padx=ModernTheme.SPACING["md"], pady=ModernTheme.SPACING["md"])

        # アニメーション付きプログレスバー
        self.progress_bar = AnimatedProgressbar(
            progress_content, variable=self.state.progress_var, maximum=100, mode="determinate", length=400
        )
        self.progress_bar.pack(fill="x", pady=(0, ModernTheme.SPACING["sm"]))
        self.progress_bar.pack_forget()  # 初期は非表示

        # ステータスラベル
        self.status_label = StyledLabel(
            progress_content, text="ダウンロード開始ボタンを押してください", style="status"
        )
        self.status_label.pack(fill="x")

    def _create_button_section(self) -> None:
        """ボタンセクションの作成"""
        # ボタン用フレーム
        button_container = StyledFrame(self.button_frame)
        button_container.pack(fill="x", pady=ModernTheme.SPACING["lg"])

        # ボタンを中央に配置
        button_frame = StyledFrame(button_container)
        button_frame.pack()

        # ダウンロードボタン（大きなプライマリボタン）
        self.download_button = StyledButton(
            button_frame,
            text=f"{IconManager.get('play')} ダウンロード開始",
            style="primary",
            command=self._on_start_download,
            padx=30,
            pady=12,
            font=("Segoe UI", 11, "bold"),
        )
        self.download_button.pack(side="left", padx=ModernTheme.SPACING["sm"])

        # 停止ボタン
        self.stop_button = StyledButton(
            button_frame,
            text=f"{IconManager.get('stop')} 停止",
            style="danger",
            command=self._on_stop_download,
            state=tk.DISABLED,
        )
        self.stop_button.pack(side="left", padx=ModernTheme.SPACING["sm"])

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
            self.download_button.config(state=tk.DISABLED)
            self.download_button.config(text=f"{IconManager.get('pause')} ダウンロード中...")
            self.stop_button.config(state=tk.NORMAL)

            # プログレスバー表示
            self.progress_tracker.show_progress()
            self.state.progress_var.set(0)
        else:
            # ボタン状態の復元
            self.download_button.config(state=tk.NORMAL)
            self.download_button.config(text=f"{IconManager.get('play')} ダウンロード開始")
            self.stop_button.config(state=tk.DISABLED)

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

            settings_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
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

            settings_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
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

            settings_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
            settings_dir.mkdir(exist_ok=True, parents=True)
            settings_file = settings_dir / "settings.json"

            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)

        except Exception:
            # 終了時は静かに失敗する
            pass
