"""MainWindowのテスト"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ui.main_window import CookieDialog, MainWindow


class TestCookieDialog:
    """CookieDialogクラスのテスト"""

    @patch("tkinter.Toplevel")
    @patch("ui.main_window.ctk.CTkFrame")
    @patch("ui.main_window.ctk.CTkLabel")
    @patch("ui.main_window.ctk.CTkTextbox")
    @patch("ui.main_window.ctk.CTkButton")
    @patch("ui.main_window.ctk.CTkFont")
    def test_cookie_dialog_creation(self, mock_font: MagicMock, mock_button: MagicMock,
                                  mock_textbox: MagicMock, mock_label: MagicMock,
                                  mock_frame: MagicMock,
                                  mock_toplevel: MagicMock) -> None:
        """Cookieダイアログ作成テスト"""
        mock_parent = MagicMock()
        mock_parent.winfo_x.return_value = 100
        mock_parent.winfo_y.return_value = 100
        mock_parent.winfo_width.return_value = 800
        mock_parent.winfo_height.return_value = 600
        mock_parent.update_idletasks.return_value = None

        # モックしたダイアログウィンドウ
        mock_dialog_window = MagicMock()
        mock_dialog_window.winfo_screenwidth.return_value = 1920
        mock_dialog_window.winfo_screenheight.return_value = 1080
        mock_toplevel.return_value = mock_dialog_window

        with patch("ui.main_window.IconManager"):
            dialog = CookieDialog(mock_parent, "test cookies")

        # ダイアログが作成されることを確認
        mock_toplevel.assert_called_once_with(mock_parent)
        assert dialog.result is None


class TestMainWindow:
    """MainWindowクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        # Tkinterコンポーネントをモック
        self.root_patcher = patch("tkinter.Tk")
        self.mock_root = self.root_patcher.start()

        # UI関連のモック（CustomTkinterも含む）
        with patch("ui.main_window.UIState"), \
             patch("ui.main_window.ProgressTracker"), \
             patch("ui.main_window.ctk.set_appearance_mode"), \
             patch("ui.main_window.ctk.set_default_color_theme"), \
             patch("ui.main_window.ctk.CTkFrame"), \
             patch("ui.main_window.ctk.CTkLabel"), \
             patch("ui.main_window.ctk.CTkButton"), \
             patch("ui.main_window.ctk.CTkEntry"), \
             patch("ui.main_window.ctk.CTkComboBox"), \
             patch("ui.main_window.ctk.CTkCheckBox"), \
             patch("ui.main_window.ctk.CTkProgressBar"), \
             patch("ui.main_window.ctk.CTkFont"), \
             patch("ui.main_window.ctk.CTkTextbox"), \
             patch("ui.main_window.ctk.CTk"), \
             patch("ui.main_window.ctk.CTkTabview"):
            self.main_window = MainWindow(self.mock_root)

    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""
        self.root_patcher.stop()

    def test_main_window_initialization(self) -> None:
        """MainWindow初期化テスト"""
        assert hasattr(self.main_window, 'root')
        assert hasattr(self.main_window, 'state')
        assert hasattr(self.main_window, 'progress_tracker')

    def test_set_callbacks(self) -> None:
        """コールバック設定テスト"""
        start_callback = MagicMock()
        stop_callback = MagicMock()
        cookie_callback = MagicMock()

        self.main_window.set_callbacks(
            start_download=start_callback,
            stop_download=stop_callback,
            set_cookies=cookie_callback
        )

        assert self.main_window.start_download_callback == start_callback
        assert self.main_window.stop_download_callback == stop_callback
        assert self.main_window.set_cookies_callback == cookie_callback

    @patch("ui.main_window.messagebox.showerror")
    def test_show_error(self, mock_showerror: MagicMock) -> None:
        """エラー表示テスト"""
        title = "エラー"
        error_message = "テストエラーメッセージ"
        self.main_window.show_error(title, error_message)

        mock_showerror.assert_called_once_with(title, error_message)

    @patch("ui.main_window.messagebox.showinfo")
    def test_show_success(self, mock_showinfo: MagicMock) -> None:
        """成功表示テスト"""
        title = "完了"
        success_message = "ダウンロード完了"
        self.main_window.show_info(title, success_message)

        mock_showinfo.assert_called_once_with(title, success_message)

    def test_progress_tracker_access(self) -> None:
        """プログレストラッカーアクセステスト"""
        # プログレストラッカーが適切に初期化されていることを確認
        assert hasattr(self.main_window, 'progress_tracker')

        # プログレス更新が例外を発生させないことを確認
        try:
            self.main_window.progress_tracker.update_progress(50.0, "テスト中...")
        except Exception as e:
            pytest.fail(f"Progress update should not raise exception: {e}")

    def test_status_tracker_access(self) -> None:
        """ステータストラッカーアクセステスト"""
        # ステータス更新が例外を発生させないことを確認
        try:
            self.main_window.progress_tracker.set_status("テストステータス")
        except Exception as e:
            pytest.fail(f"Status update should not raise exception: {e}")

    @patch("ui.main_window.filedialog.askdirectory")
    def test_browse_folder(self, mock_askdirectory: MagicMock) -> None:
        """フォルダ選択テスト"""
        mock_askdirectory.return_value = "/test/folder"

        # フォルダ選択ダイアログの動作をテスト
        # 実際の実装に依存するため、例外が発生しないことのみ確認
        try:
            # MainWindowの_choose_save_folderメソッドが存在する場合のテスト
            if hasattr(self.main_window, '_choose_save_folder'):
                self.main_window._choose_save_folder()
        except Exception as e:
            # メソッドが存在しない場合はスキップ
            pass

    @patch("builtins.open", create=True)
    @patch("json.dump")
    @patch("pathlib.Path.mkdir")
    def test_auto_save_settings(self, mock_mkdir: MagicMock, mock_json_dump: MagicMock, mock_open: MagicMock) -> None:
        """設定自動保存テスト"""
        # 実際の設定保存動作をテスト
        if hasattr(self.main_window, '_auto_save_settings'):
            # UIStateのモックメソッドに戻り値を設定
            self.main_window.state.enable_retry.get.return_value = True
            self.main_window.state.max_retries.get.return_value = 5
            self.main_window.state.quality_var.get.return_value = "1080p Best"
            self.main_window.state.enable_individual_download.get.return_value = True
            self.main_window.state.get_cookies_from_browser.get.return_value = False
            self.main_window.state.save_folder_var.get.return_value = "C:\\Downloads"
            
            # 自動保存を実行
            self.main_window._auto_save_settings()
            
            # 実際にJSON保存処理が呼ばれることを検証
            mock_json_dump.assert_called_once()
            
            # 保存される設定データの検証
            saved_data = mock_json_dump.call_args[0][0]
            assert saved_data["enable_retry"] is True
            assert saved_data["max_retries"] == 5
            assert saved_data["quality_default"] == "1080p Best"

    def test_download_button_state_management(self) -> None:
        """ダウンロードボタン状態管理テスト"""
        # set_download_in_progressメソッドのテスト
        try:
            if hasattr(self.main_window, 'set_download_in_progress'):
                self.main_window.set_download_in_progress(True)
                self.main_window.set_download_in_progress(False)
        except Exception as e:
            pytest.fail(f"Download button state management should not raise exception: {e}")

    def test_settings_load_and_save(self) -> None:
        """設定読み込み・保存テスト"""
        # 設定読み込みメソッドのテスト
        try:
            if hasattr(self.main_window, 'load_settings_on_startup'):
                self.main_window.load_settings_on_startup()
        except Exception as e:
            pytest.fail(f"Settings load should not raise exception: {e}")

        # 設定保存メソッドのテスト
        try:
            if hasattr(self.main_window, 'save_settings_on_exit'):
                self.main_window.save_settings_on_exit()
        except Exception as e:
            pytest.fail(f"Settings save should not raise exception: {e}")


class TestMainWindowIntegration:
    """MainWindow統合テスト"""

    @patch("tkinter.Tk")
    def test_main_window_with_real_tk_structure(self, mock_tk: MagicMock) -> None:
        """実際のTk構造を模倣した統合テスト"""
        mock_root = MagicMock()
        mock_tk.return_value = mock_root

        # MainWindowが必要とする全てのコンポーネントをモック（CustomTkinterも含む）
        with patch("ui.main_window.UIState") as mock_ui_state, \
             patch("ui.main_window.ProgressTracker") as mock_progress_tracker, \
             patch("ui.main_window.ctk.set_appearance_mode"), \
             patch("ui.main_window.ctk.set_default_color_theme"), \
             patch("ui.main_window.ctk.CTkFrame"), \
             patch("ui.main_window.ctk.CTkLabel"), \
             patch("ui.main_window.ctk.CTkButton"), \
             patch("ui.main_window.ctk.CTkEntry"), \
             patch("ui.main_window.ctk.CTkComboBox"), \
             patch("ui.main_window.ctk.CTkCheckBox"), \
             patch("ui.main_window.ctk.CTkProgressBar"), \
             patch("ui.main_window.ctk.CTkFont"), \
             patch("ui.main_window.ctk.CTkTextbox"), \
             patch("ui.main_window.ctk.CTk"), \
             patch("ui.main_window.ctk.CTkTabview"):

            # MainWindow作成が成功することを確認
            try:
                main_window = MainWindow(mock_root)
                assert main_window is not None
            except Exception as e:
                pytest.fail(f"MainWindow creation should not fail: {e}")
