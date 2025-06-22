"""CookieManagerのテスト"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.cookie_manager import CookieManager


class TestCookieManager:
    """CookieManagerクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.mkdtemp()
        self.cookie_manager = CookieManager()
        
        # テスト用の一時ディレクトリを使用
        self.cookie_manager.cookie_dir = Path(self.temp_dir) / "test-yt-downloader"
        self.cookie_manager.cookie_file = self.cookie_manager.cookie_dir / "cookies.txt"

    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_cookie_file_path(self) -> None:
        """Cookieファイルパスの取得テスト"""
        path = self.cookie_manager.get_cookie_file_path()
        assert isinstance(path, Path)
        assert path.name == "cookies.txt"

    def test_load_cookies_file_not_exists(self) -> None:
        """存在しないCookieファイルの読み込みテスト"""
        result = self.cookie_manager.load_cookies()
        assert result == ""

    def test_save_and_load_cookies(self) -> None:
        """Cookieの保存と読み込みテスト"""
        test_cookies = "# Test cookies\ntest.example.com\tTRUE\t/\tFALSE\t0\ttest_cookie\ttest_value"
        
        # 保存テスト
        result = self.cookie_manager.save_cookies(test_cookies)
        assert result is True
        
        # ファイルが作成されているか確認
        assert self.cookie_manager.cookie_file.exists()
        
        # 読み込みテスト
        loaded_cookies = self.cookie_manager.load_cookies()
        assert loaded_cookies == test_cookies

    def test_save_cookies_creates_directory(self) -> None:
        """Cookieディレクトリが自動作成されるかテスト"""
        # ディレクトリが存在しないことを確認
        assert not self.cookie_manager.cookie_dir.exists()
        
        # Cookie保存
        result = self.cookie_manager.save_cookies("test_cookie_data")
        assert result is True
        
        # ディレクトリが作成されたことを確認
        assert self.cookie_manager.cookie_dir.exists()

    def test_save_empty_cookies(self) -> None:
        """空のCookieの保存テスト"""
        result = self.cookie_manager.save_cookies("")
        assert result is True
        
        loaded_cookies = self.cookie_manager.load_cookies()
        assert loaded_cookies == ""

    def test_file_permissions_on_save(self) -> None:
        """保存時のファイル権限テスト（Unix系のみ）"""
        if os.name != "posix":
            pytest.skip("Unix系OS以外ではスキップ")
            
        self.cookie_manager.save_cookies("test_data")
        
        # ファイル権限を確認（0o600 = user read/write only）
        file_stat = self.cookie_manager.cookie_file.stat()
        assert oct(file_stat.st_mode)[-3:] == "600"

    @patch("pathlib.Path.write_text")
    def test_save_cookies_write_error(self, mock_write: object) -> None:
        """Cookie保存時のエラーハンドリングテスト"""
        mock_write.side_effect = OSError("Permission denied")
        
        result = self.cookie_manager.save_cookies("test_data")
        assert result is False

    @patch("pathlib.Path.read_text")
    @patch("pathlib.Path.exists")
    def test_load_cookies_read_error(self, mock_exists: object, mock_read: object) -> None:
        """Cookie読み込み時のエラーハンドリングテスト"""
        # ファイルが存在するように設定
        mock_exists.return_value = True
        mock_read.side_effect = OSError("Permission denied")
        
        result = self.cookie_manager.load_cookies()
        assert result == ""

    def test_load_cookies_unicode_handling(self) -> None:
        """Unicode文字を含むCookieの処理テスト"""
        unicode_cookies = "# 日本語コメント\nexample.com\tTRUE\t/\tFALSE\t0\t日本語Cookie\t値"
        
        self.cookie_manager.save_cookies(unicode_cookies)
        loaded_cookies = self.cookie_manager.load_cookies()
        
        assert loaded_cookies == unicode_cookies

    def test_cookie_file_validation(self) -> None:
        """Cookieファイルの形式検証テスト"""
        # 有効なNetscape形式のCookie
        valid_cookies = """# Netscape HTTP Cookie File
# This is a generated file! Do not edit.

.youtube.com	TRUE	/	FALSE	1735689600	session_token	abc123
"""
        
        self.cookie_manager.save_cookies(valid_cookies)
        loaded = self.cookie_manager.load_cookies()
        
        assert "session_token" in loaded
        assert "abc123" in loaded