"""RetryHandlerのテスト"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from download.retry_handler import CookieExpiryDetector, PlaylistExtractor, RetryConfig, RetryHandler


class TestRetryConfig:
    """RetryConfigクラスのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値テスト"""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.retry_delay == 5.0
        assert config.cookie_refresh_enabled is True
        assert config.individual_download_on_playlist_fail is True


class TestCookieExpiryDetector:
    """CookieExpiryDetectorクラスのテスト"""

    def test_is_cookie_expired_true(self) -> None:
        """Cookie期限切れ検出テスト（True）"""
        error_messages = [
            "HTTP Error 403 Forbidden",
            "Sign in to confirm your age",
            "This video is only available to Music Premium members",
            "Members-only content",
            "This video is private",
            "Video unavailable for members",
            "Cookies have expired",
            "Authentication failed",
            "Login required"
        ]
        
        for message in error_messages:
            assert CookieExpiryDetector.is_cookie_expired(message) is True

    def test_is_cookie_expired_false(self) -> None:
        """Cookie期限切れ検出テスト（False）"""
        error_messages = [
            "Connection timeout",
            "Network error",
            "Video not found",
            "Invalid URL"
        ]
        
        for message in error_messages:
            assert CookieExpiryDetector.is_cookie_expired(message) is False

    def test_is_playlist_url_true(self) -> None:
        """プレイリストURL判定テスト（True）"""
        playlist_urls = [
            "https://www.youtube.com/playlist?list=PLtest123",
            "https://www.youtube.com/watch?v=test&list=PLtest123",
            "https://music.youtube.com/playlist/PLtest123"
        ]
        
        for url in playlist_urls:
            assert CookieExpiryDetector.is_playlist_url(url) is True

    def test_is_playlist_url_false(self) -> None:
        """プレイリストURL判定テスト（False）"""
        single_urls = [
            "https://www.youtube.com/watch?v=test123",
            "https://youtu.be/test123",
            "https://music.youtube.com/watch?v=test123"
        ]
        
        for url in single_urls:
            assert CookieExpiryDetector.is_playlist_url(url) is False


class TestRetryHandler:
    """RetryHandlerクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.config = RetryConfig()
        self.retry_handler = RetryHandler(self.config)

    def test_init(self) -> None:
        """初期化テスト"""
        assert self.retry_handler.config == self.config
        assert self.retry_handler.retry_count == 0
        assert self.retry_handler.last_error == ""
        assert self.retry_handler.on_retry_attempt is None
        assert self.retry_handler.on_cookie_refresh_request is None
        assert self.retry_handler.on_individual_download is None

    def test_set_callbacks(self) -> None:
        """コールバック設定テスト"""
        retry_cb = MagicMock()
        cookie_cb = MagicMock()
        individual_cb = MagicMock()

        self.retry_handler.set_callbacks(
            on_retry_attempt=retry_cb,
            on_cookie_refresh_request=cookie_cb,
            on_individual_download=individual_cb
        )

        assert self.retry_handler.on_retry_attempt == retry_cb
        assert self.retry_handler.on_cookie_refresh_request == cookie_cb
        assert self.retry_handler.on_individual_download == individual_cb

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_try(self) -> None:
        """リトライ機能テスト（初回成功）"""
        async def successful_operation() -> None:
            pass

        result = await self.retry_handler.execute_with_retry(successful_operation, "test_url")
        assert result is True
        assert self.retry_handler.retry_count == 0

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retry(self) -> None:
        """リトライ機能テスト（リトライ後成功）"""
        call_count = 0

        async def flaky_operation() -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Connection timeout")

        retry_callback = MagicMock()
        self.retry_handler.set_callbacks(on_retry_attempt=retry_callback)

        result = await self.retry_handler.execute_with_retry(flaky_operation, "test_url")
        assert result is True
        assert self.retry_handler.retry_count == 1
        retry_callback.assert_called_once_with(1, "Connection timeout")

    @pytest.mark.asyncio
    async def test_execute_with_retry_cookie_expiry(self) -> None:
        """リトライ機能テスト（Cookie期限切れ）"""
        async def cookie_error_operation() -> None:
            raise Exception("HTTP Error 403 Forbidden")

        cookie_refresh_callback = MagicMock(return_value=True)
        self.retry_handler.set_callbacks(on_cookie_refresh_request=cookie_refresh_callback)

        # Cookie期限切れエラーの場合
        result = await self.retry_handler.execute_with_retry(cookie_error_operation, "test_url")
        # Cookie更新を試行するが、再度失敗するので False が返される
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_with_retry_playlist_individual_download(self) -> None:
        """リトライ機能テスト（プレイリスト個別ダウンロード）"""
        async def cookie_error_operation() -> None:
            raise Exception("Members-only content")

        individual_download_callback = MagicMock(return_value=True)
        self.retry_handler.set_callbacks(on_individual_download=individual_download_callback)

        playlist_url = "https://www.youtube.com/playlist?list=test123"
        result = await self.retry_handler.execute_with_retry(cookie_error_operation, playlist_url)
        
        # プレイリストのCookie期限切れの場合は個別ダウンロードが呼ばれる
        individual_download_callback.assert_called_once_with(playlist_url)

    @pytest.mark.asyncio
    async def test_execute_with_retry_max_retries_exceeded(self) -> None:
        """リトライ機能テスト（最大リトライ数超過）"""
        async def always_failing_operation() -> None:
            raise Exception("Connection timeout")

        result = await self.retry_handler.execute_with_retry(always_failing_operation, "test_url")
        assert result is False
        assert self.retry_handler.retry_count == 3  # max_retries


class TestPlaylistExtractor:
    """PlaylistExtractorクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.extractor = PlaylistExtractor("/fake/path/to/yt-dlp")

    def test_init(self) -> None:
        """初期化テスト"""
        assert self.extractor.yt_dlp_path == "/fake/path/to/yt-dlp"

    @pytest.mark.asyncio
    async def test_extract_video_urls_success(self) -> None:
        """動画URL抽出成功テスト"""
        from unittest.mock import AsyncMock, Mock, patch
        
        mock_output = "https://youtube.com/watch?v=1\nhttps://youtube.com/watch?v=2\n"

        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.extractor.extract_video_urls("https://youtube.com/playlist?list=test")

            assert len(result) == 2
            assert "https://youtube.com/watch?v=1" in result
            assert "https://youtube.com/watch?v=2" in result

    @pytest.mark.asyncio
    async def test_extract_video_urls_process_error(self) -> None:
        """動画URL抽出プロセスエラーテスト"""
        from unittest.mock import AsyncMock, Mock, patch
        
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"", b"Error occurred"))
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.extractor.extract_video_urls("https://youtube.com/playlist?list=test")

            assert result == []

    @pytest.mark.asyncio
    async def test_extract_video_urls_empty_output(self) -> None:
        """動画URL抽出空出力テスト"""
        from unittest.mock import AsyncMock, Mock, patch
        
        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.extractor.extract_video_urls("https://youtube.com/playlist?list=test")

            assert result == []

    @pytest.mark.asyncio
    async def test_extract_video_urls_exception_handling(self) -> None:
        """動画URL抽出例外処理テスト"""
        from unittest.mock import patch
        
        with patch("asyncio.create_subprocess_exec", side_effect=Exception("Process error")):
            result = await self.extractor.extract_video_urls("https://youtube.com/playlist?list=test")

            assert result == []

    @pytest.mark.asyncio
    async def test_extract_video_urls_filtering(self) -> None:
        """動画URL抽出フィルタリングテスト"""
        from unittest.mock import AsyncMock, Mock, patch
        
        # 空行や無効なURLを含む出力
        mock_output = "https://youtube.com/watch?v=1\n\ninvalid-url\nhttps://youtube.com/watch?v=2\nhttp://example.com/not-youtube\n"

        mock_process = Mock()
        mock_process.communicate = AsyncMock(return_value=(mock_output.encode(), b""))
        mock_process.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            result = await self.extractor.extract_video_urls("https://youtube.com/playlist?list=test")

            # 有効なYouTube URLのみが抽出される
            assert len(result) == 2
            assert "https://youtube.com/watch?v=1" in result
            assert "https://youtube.com/watch?v=2" in result
            # 無効なURLは除外される
            assert "invalid-url" not in result
            assert "http://example.com/not-youtube" not in result
    
    def test_is_valid_youtube_url(self) -> None:
        """YouTube URL検証テスト"""
        valid_urls = [
            "https://youtube.com/watch?v=test",
            "https://www.youtube.com/watch?v=test", 
            "https://music.youtube.com/watch?v=test",
            "https://gaming.youtube.com/watch?v=test",
            "https://youtu.be/test",
            "http://youtube.com/watch?v=test",
            "http://www.youtube.com/playlist?list=test",
            "https://music.youtube.com/playlist?list=test",
            "https://gaming.youtube.com/playlist?list=test",
        ]
        
        invalid_urls = [
            "invalid-url",
            "http://example.com",
            "https://vimeo.com/test",
            "https://dailymotion.com/video/test",
            "https://youtube.example.com/watch",  # サブドメインが違う
            "https://example.youtube.com/watch",  # ドメインが違う
            "not-a-url-at-all",
            "",
            "ftp://youtube.com/watch",  # プロトコルが違う
        ]
        
        for url in valid_urls:
            assert self.extractor._is_valid_youtube_url(url) is True, f"Should be valid: {url}"
            
        for url in invalid_urls:
            assert self.extractor._is_valid_youtube_url(url) is False, f"Should be invalid: {url}"