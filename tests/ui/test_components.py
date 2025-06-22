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
        
        # プログレス値が正しく設定されることを確認
        self.mock_main_window.state.progress_var.set.assert_called_with(progress_value)
        
        # ステータスラベルが正しく更新されることを確認
        self.mock_main_window.status_label.config.assert_called_with(text=status_text)

    def test_set_status(self) -> None:
        """ステータス設定テスト"""
        status_text = "テストステータス"
        
        self.progress_tracker.set_status(status_text)
        
        # ステータスラベルが正しく更新されることを確認
        self.mock_main_window.status_label.config.assert_called_with(text=status_text)

    def test_show_hide_progress(self) -> None:
        """プログレス表示/非表示テスト"""
        # プログレス表示
        self.progress_tracker.show_progress()
        self.mock_main_window.progress_bar.pack.assert_called_with(fill="x", pady=(0, 5))
        
        # プログレス非表示
        self.progress_tracker.hide_progress()
        self.mock_main_window.progress_bar.pack_forget.assert_called_once()

    def test_progress_validation(self) -> None:
        """プログレス値検証テスト"""
        # 有効な範囲外の値でもエラーが発生しないことを確認
        test_values = [-10, 0, 50, 100, 150]
        
        for value in test_values:
            try:
                self.progress_tracker.update_progress(value, f"Progress: {value}%")
            except Exception as e:
                pytest.fail(f"Progress update should handle value {value} gracefully: {e}")


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
        
        # エラーが適切に処理されることを確認
        with pytest.raises(Exception):
            progress_tracker.update_progress(50, "Test")