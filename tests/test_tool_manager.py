"""ToolManagerのテスト"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from tool_manager import ToolManager


class TestToolManager:
    """ToolManagerクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.temp_dir = tempfile.mkdtemp()
        self.tool_manager = ToolManager(save_dir=self.temp_dir)

    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_with_custom_save_dir(self) -> None:
        """カスタム保存ディレクトリでの初期化テスト"""
        assert self.tool_manager.save_dir == Path(self.temp_dir)

    def test_init_default_save_dir(self) -> None:
        """デフォルト保存ディレクトリでの初期化テスト"""
        import os
        tool_manager = ToolManager()
        # Windows専用: %USERPROFILE%\AppData\Local\yt-downloader\tools
        expected_path = Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "yt-downloader" / "tools"
        assert tool_manager.save_dir == expected_path

    def test_get_tool_path(self) -> None:
        """ツールパスの取得テスト"""
        tool_path = self.tool_manager._get_tool_path("test-tool.exe")
        expected_path = Path(self.temp_dir) / "test-tool.exe"
        assert tool_path == expected_path

    def test_check_tool_exists_local_file(self) -> None:
        """ローカルファイル存在確認テスト"""
        # テスト用ファイルを作成
        test_file = Path(self.temp_dir) / "existing-tool.exe"
        test_file.write_text("dummy tool")

        assert self.tool_manager.check_tool_exists("existing-tool.exe") is True

    def test_check_tool_exists_not_found(self) -> None:
        """存在しないツールの確認テスト"""
        assert self.tool_manager.check_tool_exists("non-existing-tool.exe") is False

    @patch("subprocess.run")
    def test_check_tool_exists_system_path(self, mock_run: MagicMock) -> None:
        """システムパスでのツール確認テスト"""
        mock_run.return_value = MagicMock(returncode=0)

        assert self.tool_manager.check_tool_exists("tool") is True
        mock_run.assert_called_once_with(["tool", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    @patch("requests.get")
    def test_download_file_success(self, mock_get: MagicMock) -> None:
        """ファイルダウンロード成功テスト"""
        # モックレスポンスを設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b"test data"]
        mock_get.return_value = mock_response

        save_path = str(Path(self.temp_dir) / "tool.exe")
        result = self.tool_manager.download_file(
            "https://example.com/tool.exe",
            save_path
        )

        assert result is True

        # ファイルが作成されたことを確認
        downloaded_file = Path(save_path)
        assert downloaded_file.exists()

    @patch("requests.get")
    def test_download_file_network_error(self, mock_get: MagicMock) -> None:
        """ネットワークエラー時のダウンロードテスト"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        save_path = str(Path(self.temp_dir) / "tool.exe")
        result = self.tool_manager.download_file(
            "https://example.com/tool.exe",
            save_path
        )

        assert result is False

    @patch("subprocess.run")
    @patch.object(ToolManager, "_get_tool_path")
    def test_check_and_download_yt_dlp_already_exists(
        self,
        mock_get_path: MagicMock,
        mock_subprocess: MagicMock
    ) -> None:
        """yt-dlpが既に存在する場合のテスト"""
        # ファイルが存在することをモック
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_get_path.return_value = mock_path
        
        result = self.tool_manager.check_and_download_yt_dlp()
        assert result is True
        mock_subprocess.assert_called_once()

    @patch.object(ToolManager, "download_file")
    @patch.object(ToolManager, "_get_tool_path")
    def test_check_and_download_yt_dlp_download_needed(
        self,
        mock_get_path: MagicMock,
        mock_download: MagicMock
    ) -> None:
        """yt-dlpのダウンロードが必要な場合のテスト"""
        # ファイルが存在しないことをモック
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_get_path.return_value = mock_path
        mock_download.return_value = True

        result = self.tool_manager.check_and_download_yt_dlp()
        assert result is True
        mock_download.assert_called_once()

    @patch.object(ToolManager, "download_file")
    @patch.object(ToolManager, "check_tool_exists")
    def test_check_and_download_ffmpeg_success(
        self,
        mock_check: MagicMock,
        mock_download: MagicMock
    ) -> None:
        """ffmpegダウンロード成功テスト"""
        mock_check.return_value = False
        mock_download.return_value = True
        
        # 必要なファイル操作をモック
        with patch("subprocess.run") as mock_run:
            with patch("shutil.rmtree") as mock_rmtree:
                with patch.object(Path, "exists", return_value=True):
                    with patch.object(Path, "rename"):
                        with patch.object(Path, "unlink"):
                            mock_run.return_value = MagicMock(returncode=0)
                            
                            result = self.tool_manager.check_and_download_ffmpeg()
                            assert result is True
                            mock_download.assert_called_once()
                            mock_run.assert_called_once()

    @patch.object(ToolManager, "download_file")
    @patch.object(ToolManager, "check_tool_exists")
    def test_check_and_download_ffmpeg_already_exists(
        self,
        mock_check: MagicMock,
        mock_download: MagicMock
    ) -> None:
        """ffmpegが既に存在する場合のテスト"""
        mock_check.return_value = True
        
        result = self.tool_manager.check_and_download_ffmpeg()
        assert result is True
        mock_download.assert_not_called()

    def test_windows_specific_behavior(self) -> None:
        """Windows固有の動作テスト"""
        import os
        # Windows専用アプリケーションとして、Windows環境でのみ動作することを確認
        if os.name != "nt":
            pytest.skip("Windows専用アプリケーションのため、Windows以外ではスキップ")
        
        # Windows固有のツールパス処理をテスト
        tool_manager = ToolManager()
        tool_path = tool_manager._get_tool_path("test.exe")
        
        # Windows固有の期待される動作を検証
        assert tool_path.suffix == ".exe"
        assert "AppData" in str(tool_path)
        assert os.environ.get("USERPROFILE") in str(tool_path)

    def test_tool_path_management(self) -> None:
        """ツールパス管理テスト"""
        # ツールパスの取得とディレクトリ管理のテスト
        tool_path = self.tool_manager._get_tool_path("test.exe")
        assert tool_path.parent == self.tool_manager.save_dir
        assert tool_path.name == "test.exe"

    @patch("subprocess.run")
    @patch.object(ToolManager, "download_file")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    def test_atomicparsley_download(
        self,
        mock_unlink: MagicMock,
        mock_exists: MagicMock,
        mock_download: MagicMock,
        mock_run: MagicMock
    ) -> None:
        """AtomicParsleyダウンロード成功テスト"""
        # AtomicParsley.exeが存在しない状態をモック
        mock_exists.return_value = False
        mock_download.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        result = self.tool_manager.check_and_download_atomicparsley()
        assert result is True
        mock_download.assert_called_once()
        mock_run.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_atomicparsley_already_exists(
        self,
        mock_exists: MagicMock
    ) -> None:
        """AtomicParsleyが既に存在する場合のテスト"""
        # AtomicParsley.exeが既に存在する状態をモック
        mock_exists.return_value = True
        
        result = self.tool_manager.check_and_download_atomicparsley()
        assert result is True
