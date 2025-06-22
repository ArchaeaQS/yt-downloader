"""メインアプリケーションのテスト"""
from __future__ import annotations

import tkinter as tk
from unittest.mock import MagicMock, patch

import pytest


class TestYouTubeDownloaderApp:
    """YouTubeDownloaderAppクラスのテスト"""
    
    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        # 各種モジュールをモック化
        self.tk_patcher = patch("main.ctk.CTk")
        self.dm_patcher = patch("main.DownloadManager")
        self.cm_patcher = patch("main.CookieManager")
        self.mw_patcher = patch("main.MainWindow")
        
        self.mock_tk = self.tk_patcher.start()
        self.mock_dm = self.dm_patcher.start()
        self.mock_cm = self.cm_patcher.start()
        self.mock_mw = self.mw_patcher.start()
        
        # モックインスタンスを設定
        self.mock_root = MagicMock()
        self.mock_tk.return_value = self.mock_root
        self.mock_download_manager = MagicMock()
        self.mock_dm.return_value = self.mock_download_manager
        self.mock_cookie_manager = MagicMock()
        self.mock_cm.return_value = self.mock_cookie_manager
        self.mock_main_window = MagicMock()
        self.mock_mw.return_value = self.mock_main_window
        
    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""
        self.tk_patcher.stop()
        self.dm_patcher.stop()
        self.cm_patcher.stop()
        self.mw_patcher.stop()

    def test_init_components(self) -> None:
        """コンポーネント初期化テスト"""
        from main import YouTubeDownloaderApp
        
        app = YouTubeDownloaderApp()
        
        assert hasattr(app, "root")
        assert hasattr(app, "download_manager")
        assert hasattr(app, "cookie_manager")
        assert hasattr(app, "main_window")

    def test_main_function(self) -> None:
        """main関数テスト"""
        with patch("main.YouTubeDownloaderApp") as mock_app_class:
            mock_app_instance = MagicMock()
            mock_app_class.return_value = mock_app_instance

            from main import main
            main()

            # アプリケーションが作成され、実行されたことを確認
            mock_app_class.assert_called_once()
            mock_app_instance.run.assert_called_once()

    def test_component_creation(self) -> None:
        """コンポーネント作成テスト"""
        from main import YouTubeDownloaderApp
        
        app = YouTubeDownloaderApp()
        
        # 各コンポーネントが作成されたことを確認
        self.mock_tk.assert_called_once()
        self.mock_dm.assert_called_once()
        self.mock_cm.assert_called_once()
        self.mock_mw.assert_called_once()

    def test_run_method(self) -> None:
        """run メソッドテスト"""
        from main import YouTubeDownloaderApp
        
        app = YouTubeDownloaderApp()
        app.run()
        
        # mainloopが呼ばれることを確認
        self.mock_root.mainloop.assert_called_once()


class TestApplicationConfiguration:
    """アプリケーション設定テスト"""
    
    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        # 各種モジュールをモック化
        self.tk_patcher = patch("main.ctk.CTk")
        self.dm_patcher = patch("main.DownloadManager")
        self.cm_patcher = patch("main.CookieManager")
        self.mw_patcher = patch("main.MainWindow")
        
        self.mock_tk = self.tk_patcher.start()
        self.mock_dm = self.dm_patcher.start()
        self.mock_cm = self.cm_patcher.start()
        self.mock_mw = self.mw_patcher.start()
        
        # モックインスタンスを設定
        self.mock_root = MagicMock()
        self.mock_tk.return_value = self.mock_root
        self.mock_download_manager = MagicMock()
        self.mock_dm.return_value = self.mock_download_manager
        self.mock_cookie_manager = MagicMock()
        self.mock_cm.return_value = self.mock_cookie_manager
        self.mock_main_window = MagicMock()
        self.mock_mw.return_value = self.mock_main_window
        
    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""
        self.tk_patcher.stop()
        self.dm_patcher.stop()
        self.cm_patcher.stop()
        self.mw_patcher.stop()

    def test_default_configuration(self) -> None:
        """デフォルト設定テスト"""
        from main import YouTubeDownloaderApp
        
        app = YouTubeDownloaderApp()
        
        # デフォルト設定値の確認
        assert hasattr(app, "download_manager")
        assert hasattr(app, "cookie_manager")
        assert hasattr(app, "main_window")

    def test_logging_configuration(self) -> None:
        """ログ設定テスト"""
        # 現在のアプリケーションではログ設定は実装されていないため、
        # このテストは不要。削除するか、将来ログ機能が追加された際に実装する。
        pytest.skip("ログ機能は現在未実装のため、テストをスキップ")

    def test_application_metadata(self) -> None:
        """アプリケーションメタデータテスト"""
        from main import YouTubeDownloaderApp
        
        app = YouTubeDownloaderApp()
        
        # Tkが呼ばれることを確認
        self.mock_tk.assert_called_once()


class TestStandaloneFeatures:
    """独立機能のテスト"""

    def test_import_main_module(self) -> None:
        """mainモジュールのインポートテスト"""
        try:
            import main
            assert hasattr(main, "YouTubeDownloaderApp")
            assert hasattr(main, "main")
        except ImportError as e:
            pytest.fail(f"Failed to import main module: {e}")

    def test_application_class_exists(self) -> None:
        """アプリケーションクラス存在テスト"""
        from main import YouTubeDownloaderApp
        assert YouTubeDownloaderApp is not None
        
    def test_main_function_exists(self) -> None:
        """main関数存在テスト"""
        from main import main
        assert main is not None
        assert callable(main)