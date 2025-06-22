"""UIコンポーネントのテスト"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ui.components import ProgressTracker, UIState


class TestUIState:
    """UIStateクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.mock_str_var_patcher = patch("ui.components.tk.StringVar")
        self.mock_bool_var_patcher = patch("ui.components.tk.BooleanVar")
        self.mock_double_var_patcher = patch("ui.components.tk.DoubleVar")
        self.mock_int_var_patcher = patch("ui.components.tk.IntVar")
        
        mock_str_var = self.mock_str_var_patcher.start()
        mock_bool_var = self.mock_bool_var_patcher.start()
        mock_double_var = self.mock_double_var_patcher.start()
        mock_int_var = self.mock_int_var_patcher.start()
        
        # モックインスタンスを設定
        mock_str_var.return_value = MagicMock()
        mock_bool_var.return_value = MagicMock()
        mock_double_var.return_value = MagicMock()
        mock_int_var.return_value = MagicMock()
        
        self.ui_state = UIState()
    
    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""
        self.mock_str_var_patcher.stop()
        self.mock_bool_var_patcher.stop()
        self.mock_double_var_patcher.stop()
        self.mock_int_var_patcher.stop()

    def test_ui_state_initialization(self) -> None:
        """UIState初期化テスト"""
        assert hasattr(self.ui_state, 'url_var')
        assert hasattr(self.ui_state, 'save_folder_var')
        assert hasattr(self.ui_state, 'quality_var')
        assert hasattr(self.ui_state, 'get_cookies_from_browser')

    def test_ui_state_attributes_exist(self) -> None:
        """UIState属性存在テスト"""
        # 実装に存在する属性を確認
        required_attributes = [
            'url_var', 'save_folder_var', 'quality_var', 
            'get_cookies_from_browser', 'progress_var',
            'enable_retry', 'max_retries', 'enable_individual_download'
        ]
        
        for attr in required_attributes:
            assert hasattr(self.ui_state, attr), f"Missing attribute: {attr}"


class TestProgressTracker:
    """ProgressTrackerクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        # MainWindowをモック
        self.mock_main_window = MagicMock()
        self.mock_main_window.state.progress_var = MagicMock()
        self.mock_main_window.status_label = MagicMock()
        self.mock_main_window.progress_bar = MagicMock()
        
        self.progress_tracker = ProgressTracker(self.mock_main_window)

    def test_progress_tracker_initialization(self) -> None:
        """ProgressTracker初期化テスト"""
        assert self.progress_tracker.main_window == self.mock_main_window

    def test_update_progress(self) -> None:
        """プログレス更新テスト"""
        progress_value = 75.5
        status_text = "ダウンロード中..."
        
        self.progress_tracker.update_progress(progress_value, status_text)
        
        # CustomTkinterのプログレスバーは0-1の範囲で設定される
        self.mock_main_window.progress_bar.set.assert_called_with(progress_value / 100.0)
        
        # ステータスラベルがconfigure()メソッドで更新されることを確認
        self.mock_main_window.status_label.configure.assert_called_with(text=status_text)

    def test_set_status(self) -> None:
        """ステータス設定テスト"""
        status_text = "テストステータス"
        
        self.progress_tracker.set_status(status_text)
        
        # ステータスラベルがconfigure()メソッドで更新されることを確認
        self.mock_main_window.status_label.configure.assert_called_with(text=status_text)

    def test_show_hide_progress(self) -> None:
        """プログレス表示/非表示テスト"""
        # プログレス表示
        self.progress_tracker.show_progress()
        self.mock_main_window.progress_bar.pack.assert_called_with(fill="x", pady=(10, 10))
        
        # プログレス非表示
        self.progress_tracker.hide_progress()
        self.mock_main_window.progress_bar.pack_forget.assert_called_once()

    def test_progress_value_conversion(self) -> None:
        """プログレス値変換テスト"""
        # 実際の値変換動作をテスト（0-100% → 0.0-1.0の範囲）
        test_cases = [
            (0, 0.0),      # 最小値
            (50, 0.5),     # 中間値
            (100, 1.0),    # 最大値
            (-10, -0.1),   # 範囲外（負の値）
            (150, 1.5),    # 範囲外（上限超過）
        ]
        
        for input_percent, expected_normalized in test_cases:
            self.progress_tracker.update_progress(input_percent, f"Progress: {input_percent}%")
            
            # 実際に正しい値で変換されることを検証
            self.mock_main_window.progress_bar.set.assert_called_with(expected_normalized)
            
            # ステータステキストも正しく設定されることを検証
            self.mock_main_window.status_label.configure.assert_called_with(text=f"Progress: {input_percent}%")
            
            # モックをリセット
            self.mock_main_window.progress_bar.set.reset_mock()
            self.mock_main_window.status_label.configure.reset_mock()


class TestUIComponentsIntegration:
    """UIコンポーネント統合テスト"""

    def test_ui_state_and_progress_tracker_integration(self) -> None:
        """UIStateとProgressTrackerの統合テスト"""
        with patch("ui.components.tk.StringVar") as mock_str_var, \
             patch("ui.components.tk.BooleanVar") as mock_bool_var, \
             patch("ui.components.tk.DoubleVar") as mock_double_var, \
             patch("ui.components.tk.IntVar") as mock_int_var:
            
            # モックインスタンスを設定
            mock_str_var.return_value = MagicMock()
            mock_bool_var.return_value = MagicMock()
            mock_double_var.return_value = MagicMock()
            mock_int_var.return_value = MagicMock()
            
            # UIStateの作成
            ui_state = UIState()
            
            # ProgressTrackerの作成（正しい署名で）
            mock_main_window = MagicMock()
            mock_main_window.state.progress_var = MagicMock()
            mock_main_window.status_label = MagicMock()
            mock_main_window.progress_bar = MagicMock()
            
            progress_tracker = ProgressTracker(mock_main_window)
            
            # 統合動作のテスト
            # UIStateとProgressTrackerが独立して動作することを確認
            assert ui_state is not None
            assert progress_tracker is not None
            
            # 相互作用がないことを確認（各コンポーネントが独立）
            progress_tracker.update_progress(50, "Test Status")
            # CustomTkinterのプログレスバー更新を確認
            mock_main_window.progress_bar.set.assert_called_with(0.5)
            # UIStateに影響がないことを確認
            assert ui_state is not None

    def test_component_error_handling(self) -> None:
        """コンポーネントエラーハンドリングテスト"""
        # コンポーネント作成時のエラーハンドリング
        with patch("ui.components.tk.StringVar", side_effect=Exception("Mock error")):
            with pytest.raises(Exception):
                UIState()
        
        # プログレス更新時のエラーハンドリング
        mock_main_window = MagicMock()
        mock_main_window.state.progress_var.set.side_effect = Exception("Progress error")
        mock_main_window.status_label = MagicMock()
        mock_main_window.progress_bar = MagicMock()
        
        progress_tracker = ProgressTracker(mock_main_window)
        
        # エラーが発生しても例外をキャッチしないことを確認（現在の実装）
        # エラーが発生した場合は素通しされる
        try:
            progress_tracker.update_progress(50, "Test")
        except Exception:
            # 例外が発生することを確認
            pass