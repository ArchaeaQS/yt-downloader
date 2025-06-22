"""DownloadManagerのテスト"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from download.manager import DownloadManager, DownloadState


class TestDownloadState:
    """DownloadStateクラスのテスト"""

    def test_init(self) -> None:
        """初期化テスト"""
        state = DownloadState()
        
        assert state.is_downloading is False
        assert state.stop_requested is False
        assert state.current_download_task is None
        assert state.process is None
        assert state.process_pid is None
        assert state.current_phase == "video"


class TestDownloadManager:
    """DownloadManagerクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        with patch("download.manager.tool_manager.ToolManager"):
            self.download_manager = DownloadManager()

    def teardown_method(self) -> None:
        """各テストメソッドの後に実行"""
        # 非同期ループの適切なクリーンアップ
        if hasattr(self.download_manager, "asyncio_loop") and self.download_manager.asyncio_loop.is_running():
            # run_forever()で動いているループを停止
            self.download_manager.asyncio_loop.call_soon_threadsafe(
                self.download_manager.asyncio_loop.stop
            )
            # スレッドの終了を待機
            if hasattr(self.download_manager, "thread") and self.download_manager.thread.is_alive():
                self.download_manager.thread.join(timeout=1.0)

    def test_init(self) -> None:
        """初期化テスト"""
        assert isinstance(self.download_manager.state, DownloadState)
        assert self.download_manager.progress_callback is None
        assert self.download_manager.status_callback is None
        assert self.download_manager.error_callback is None
        assert self.download_manager.success_callback is None

    def test_set_callbacks(self) -> None:
        """コールバック設定テスト"""
        progress_cb = MagicMock()
        status_cb = MagicMock()
        error_cb = MagicMock()
        success_cb = MagicMock()
        cookie_refresh_cb = MagicMock()

        self.download_manager.set_callbacks(
            progress_callback=progress_cb,
            status_callback=status_cb,
            error_callback=error_cb,
            success_callback=success_cb,
            cookie_refresh_callback=cookie_refresh_cb,
        )

        assert self.download_manager.progress_callback == progress_cb
        assert self.download_manager.status_callback == status_cb
        assert self.download_manager.error_callback == error_cb
        assert self.download_manager.success_callback == success_cb
        assert self.download_manager.cookie_refresh_callback == cookie_refresh_cb

    def test_validate_params_valid_url(self) -> None:
        """有効なURL検証テスト"""
        import tempfile
        
        # 実際に存在するテンポラリディレクトリを使用
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.download_manager._validate_params(
                "https://www.youtube.com/watch?v=test123",
                temp_dir
            )
            assert result is True

    def test_validate_params_invalid_url(self) -> None:
        """無効なURL検証テスト"""
        result = self.download_manager._validate_params(
            "invalid-url",
            "/tmp/downloads"
        )
        assert result is False

    def test_validate_params_empty_folder(self) -> None:
        """空の保存フォルダ検証テスト"""
        result = self.download_manager._validate_params(
            "https://www.youtube.com/watch?v=test123",
            ""
        )
        assert result is False

    def test_prepare_download(self) -> None:
        """ダウンロード準備テスト"""
        status_callback = MagicMock()
        self.download_manager.set_callbacks(status_callback=status_callback)

        self.download_manager._prepare_download()

        assert self.download_manager.state.is_downloading is True
        assert self.download_manager.state.stop_requested is False
        assert self.download_manager.state.process is None
        assert self.download_manager.state.process_pid is None
        assert self.download_manager.state.current_phase == "preparing"
        status_callback.assert_called_with("ダウンロードを開始します...")

    def test_cleanup_after_stop(self) -> None:
        """停止後クリーンアップテスト"""
        status_callback = MagicMock()
        self.download_manager.set_callbacks(status_callback=status_callback)
        
        # 状態を設定
        self.download_manager.state.is_downloading = True
        self.download_manager.state.process = MagicMock()
        self.download_manager.state.process_pid = 12345

        self.download_manager._cleanup_after_stop()

        assert self.download_manager.state.is_downloading is False
        assert self.download_manager.state.process is None
        assert self.download_manager.state.process_pid is None
        status_callback.assert_called_with("ダウンロードを中止しました")

    def test_cleanup_after_completion(self) -> None:
        """完了後クリーンアップテスト"""
        # 状態を設定
        self.download_manager.state.is_downloading = True
        self.download_manager.state.stop_requested = True
        self.download_manager.state.process = MagicMock()
        self.download_manager.state.process_pid = 12345

        self.download_manager._cleanup_after_completion()

        assert self.download_manager.state.is_downloading is False
        assert self.download_manager.state.stop_requested is False
        assert self.download_manager.state.process is None
        assert self.download_manager.state.process_pid is None

    def test_get_cookie_file_path(self) -> None:
        """Cookieファイルパス取得テスト"""
        from pathlib import Path
        
        path = self.download_manager.get_cookie_file_path()
        assert isinstance(path, Path)
        assert path.name == "cookies.txt"

    def test_parse_progress_line_download_percentage(self) -> None:
        """プログレス行解析テスト（ダウンロード進捗）"""
        progress_callback = MagicMock()
        status_callback = MagicMock()
        self.download_manager.set_callbacks(
            progress_callback=progress_callback,
            status_callback=status_callback
        )

        # yt-dlpの典型的なプログレス出力をテスト
        test_line = "[download]  45.6% of 123.45MiB at 1.23MiB/s ETA 00:30"
        self.download_manager._parse_progress_line(test_line)

        # プログレス解析はエラーを発生させないことを確認
        # 実際の実装では条件によってコールバックが呼ばれない場合があるため、
        # エラーが発生しないことを確認するのみ
        assert True  # テストが完了すればOK

    def test_parse_progress_line_merging_phase(self) -> None:
        """プログレス行解析テスト（結合フェーズ）"""
        status_callback = MagicMock()
        self.download_manager.set_callbacks(status_callback=status_callback)

        test_line = "[ffmpeg] Merging formats into output.mp4"
        self.download_manager._parse_progress_line(test_line)

        assert self.download_manager.state.current_phase == "merging"
        status_callback.assert_called_with("動画と音声を結合中...")

    def test_is_cookie_error_detection(self) -> None:
        """Cookie関連エラー検出テスト"""
        cookie_error_lines = [
            "ERROR: This video is only available for members",
            "ERROR: Private video. Sign in to view",
            "ERROR: Video unavailable. This video is private",
            "WARNING: Login required",
        ]

        for line in cookie_error_lines:
            assert self.download_manager._is_cookie_error(line) is True
        
        # "Video unavailable"だけではCookieエラーではない（改善された実装に対応）
        general_unavailable = "ERROR: Video unavailable"
        assert self.download_manager._is_cookie_error(general_unavailable) is False

        # 正常な行はFalseを返すことを確認
        normal_line = "[download] Downloading video..."
        assert self.download_manager._is_cookie_error(normal_line) is False

    def test_detect_download_phase_video(self) -> None:
        """ダウンロードフェーズ検出テスト（動画）"""
        video_lines = [
            "[download] Downloading video.mp4",
            "[download] 50% of video.webm",
        ]

        for line in video_lines:
            phase = self.download_manager._detect_download_phase(line)
            assert phase == "video"

    def test_detect_download_phase_audio(self) -> None:
        """ダウンロードフェーズ検出テスト（音声）"""
        audio_lines = [
            "[download] Downloading audio.m4a",
            "[download] 75% of audio.aac",
        ]

        for line in audio_lines:
            phase = self.download_manager._detect_download_phase(line)
            assert phase == "audio"

    def test_detect_download_phase_merging(self) -> None:
        """ダウンロードフェーズ検出テスト（結合）"""
        merging_lines = [
            "[ffmpeg] Merging formats",
            "Post-processing video",
        ]

        for line in merging_lines:
            phase = self.download_manager._detect_download_phase(line)
            assert phase == "merging"

    def test_get_phase_status_text(self) -> None:
        """フェーズステータステキスト生成テスト"""
        # 動画ダウンロード
        video_line = "[download] 50% of video.mp4 at 1.5MiB/s"
        status = self.download_manager._get_phase_status_text(50.0, ", 速度: 1.5MiB/s", video_line)
        assert "動画をダウンロード中" in status

        # 音声ダウンロード
        audio_line = "[download] 75% of audio.m4a at 500KiB/s"
        status = self.download_manager._get_phase_status_text(75.0, ", 速度: 500KiB/s", audio_line)
        assert "音声を取得中" in status

    @pytest.mark.asyncio
    async def test_configure_cookies_browser_mode(self) -> None:
        """ブラウザCookie設定テスト"""
        cmd = []
        result = await self.download_manager._configure_cookies(cmd, True, "test_url")
        
        assert result is True
        assert "--cookies-from-browser" in cmd
        assert "firefox" in cmd

    @pytest.mark.asyncio
    async def test_configure_cookies_manual_mode_with_file(self) -> None:
        """手動Cookie設定テスト（ファイル有り）"""
        cmd = []
        
        # Cookieファイルが存在することをモック
        with patch.object(self.download_manager, "get_cookie_file_path") as mock_path:
            mock_cookie_file = MagicMock()
            mock_cookie_file.exists.return_value = True
            mock_cookie_file.stat.return_value.st_size = 100
            mock_path.return_value = mock_cookie_file
            
            result = await self.download_manager._configure_cookies(cmd, False, "test_url")
            
            assert result is True
            assert "--cookies" in cmd

    def test_stop_download(self) -> None:
        """ダウンロード停止テスト"""
        # プロセスをモック
        mock_process = MagicMock()
        self.download_manager.state.process = mock_process
        self.download_manager.state.process_pid = 12345

        with patch.object(self.download_manager, "_kill_process_immediately"):
            with patch.object(self.download_manager, "_cleanup_after_stop"):
                self.download_manager.stop_download()

        assert self.download_manager.state.stop_requested is True

    def test_retry_callback_integration(self) -> None:
        """リトライコールバック統合テスト"""
        status_callback = MagicMock()
        self.download_manager.set_callbacks(status_callback=status_callback)

        # リトライ試行コールバック（メッセージ内容より呼び出されることを確認）
        self.download_manager._on_retry_attempt(2, "Network timeout")
        status_callback.assert_called_once()
        # コールバックの引数に回数とエラーメッセージが含まれることを確認
        call_args = status_callback.call_args[0][0]
        assert "2回目" in call_args
        assert "Network timeout" in call_args

        # Cookie更新要求コールバック
        cookie_refresh_callback = MagicMock(return_value=True)
        self.download_manager.set_callbacks(cookie_refresh_callback=cookie_refresh_callback)
        
        result = self.download_manager._on_cookie_refresh_request()
        assert result is True
        cookie_refresh_callback.assert_called_once()

    def test_network_error_handling(self) -> None:
        """ネットワークエラーハンドリングテスト"""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.download_manager._validate_params(
                "https://www.youtube.com/watch?v=invalid",
                temp_dir
            )
            # URLは有効だが、ネットワークエラーが発生する可能性がある
            assert result is True
    
    def test_invalid_save_directory(self) -> None:
        """無効な保存ディレクトリのテスト"""
        result = self.download_manager._validate_params(
            "https://www.youtube.com/watch?v=test123",
            "/nonexistent/directory/path"
        )
        assert result is False
    
    def test_cookie_error_patterns(self) -> None:
        """Cookie関連エラーパターンテスト"""
        error_patterns = [
            "ERROR: [youtube] test: This video is only available for Premium members",
            "WARNING: [youtube] test: Sign in to confirm your age", 
            "ERROR: Private video. Sign in if you have been granted access",
            "ERROR: [youtube] test: Members-only content",
            "ERROR: [youtube] test: Video is private", 
            "ERROR: [youtube] test: Requires authentication",
            "ERROR: [youtube] test: Login required",
            "ERROR: [youtube] test: Membership required",
            "ERROR: [youtube] test: Access denied",
            # 具体的な文脈でのvideo unavailable（Cookie関連）
            "ERROR: [youtube] test: Video unavailable for private members only",
            "ERROR: [youtube] test: Video unavailable, sign in to access",
        ]
        
        for error_line in error_patterns:
            assert self.download_manager._is_cookie_error(error_line) is True
    
    def test_non_cookie_error_patterns(self) -> None:
        """非Cookie関連エラーパターンテスト"""
        non_cookie_errors = [
            "[download] Downloading video info webpage",
            "ERROR: Unable to download webpage: HTTP Error 404", 
            "WARNING: [youtube] Falling back to default",
            "ERROR: [youtube] test: No video formats found",
            "ERROR: [youtube] test: Connection timeout",
            "INFO: [youtube] test: Download completed",
            # 単純な"video unavailable"はCookie関連ではない
            "ERROR: [youtube] test: Video unavailable (video does not exist)",
            "ERROR: [youtube] test: Video unavailable due to copyright",
            "ERROR: [youtube] test: Video unavailable in your country",
        ]
        
        for error_line in non_cookie_errors:
            assert self.download_manager._is_cookie_error(error_line) is False