"""ダウンロードリトライとエラーハンドリング"""
from __future__ import annotations

import asyncio
import re
from collections.abc import Callable


class RetryConfig:
    """リトライ設定クラス"""

    def __init__(self) -> None:
        self.max_retries = 3
        self.retry_delay = 5.0  # 秒
        self.cookie_refresh_enabled = True
        self.individual_download_on_playlist_fail = True


class CookieExpiryDetector:
    """Cookie期限切れ検出クラス"""

    # Cookie期限切れを示すエラーパターン
    COOKIE_EXPIRY_PATTERNS = [
        r"HTTP Error 403.*Forbidden",
        r"Sign in to confirm your age",
        r"This video is only available to Music Premium members",
        r"Members-only content",
        r"This video is private",
        r"Video unavailable.*members",
        r"Cookies.*expired",
        r"Authentication.*failed",
        r"Login.*required",
    ]

    @classmethod
    def is_cookie_expired(cls, error_message: str) -> bool:
        """エラーメッセージからCookie期限切れを判定"""
        for pattern in cls.COOKIE_EXPIRY_PATTERNS:
            if re.search(pattern, error_message, re.IGNORECASE):
                return True
        return False

    @classmethod
    def is_playlist_url(cls, url: str) -> bool:
        """URLがプレイリストかどうかを判定"""
        playlist_patterns = [
            r"[?&]list=",
            r"playlist\?",
            r"/playlist/",
        ]
        for pattern in playlist_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False


class RetryHandler:
    """ダウンロードリトライ処理クラス"""

    def __init__(self, config: RetryConfig) -> None:
        self.config = config
        self.retry_count = 0
        self.last_error = ""

        # コールバック関数
        self.on_retry_attempt: Callable[[int, str], None] | None = None
        self.on_cookie_refresh_request: Callable[[], bool] | None = None
        self.on_individual_download: Callable[[str], bool] | None = None

    def set_callbacks(self,
                     on_retry_attempt: Callable[[int, str], None] | None = None,
                     on_cookie_refresh_request: Callable[[], bool] | None = None,
                     on_individual_download: Callable[[str], bool] | None = None) -> None:
        """コールバック関数の設定"""
        self.on_retry_attempt = on_retry_attempt
        self.on_cookie_refresh_request = on_cookie_refresh_request
        self.on_individual_download = on_individual_download

    async def execute_with_retry(self,
                               download_func: Callable[[], asyncio.Task[None]],
                               url: str) -> bool:
        """リトライ機能付きダウンロード実行"""
        self.retry_count = 0

        while self.retry_count <= self.config.max_retries:
            try:
                await download_func()
                return True  # 成功

            except Exception as e:
                self.last_error = str(e)

                # Cookie期限切れエラーの検出
                if CookieExpiryDetector.is_cookie_expired(self.last_error):
                    return await self._handle_cookie_expiry(url, download_func)

                # 一般的なエラーの場合
                if self.retry_count < self.config.max_retries:
                    self.retry_count += 1
                    if self.on_retry_attempt:
                        self.on_retry_attempt(self.retry_count, self.last_error)

                    await asyncio.sleep(self.config.retry_delay)
                else:
                    # 最大リトライ回数に達した
                    return False

        return False

    async def _handle_cookie_expiry(self,
                                  url: str,
                                  download_func: Callable[[], asyncio.Task[None]]) -> bool:
        """Cookie期限切れエラーの処理"""
        # プレイリストの場合は個別ダウンロードを試行
        if (CookieExpiryDetector.is_playlist_url(url) and
            self.config.individual_download_on_playlist_fail):

            if self.on_individual_download:
                return self.on_individual_download(url)

        # Cookie更新を試行
        if self.config.cookie_refresh_enabled and self.on_cookie_refresh_request:
            cookie_refreshed = self.on_cookie_refresh_request()

            if cookie_refreshed and self.retry_count < self.config.max_retries:
                self.retry_count += 1
                if self.on_retry_attempt:
                    self.on_retry_attempt(self.retry_count, "Cookie更新後の再試行")

                await asyncio.sleep(self.config.retry_delay)
                try:
                    await download_func()
                    return True
                except Exception as e:
                    self.last_error = str(e)

        return False


class PlaylistExtractor:
    """プレイリストから個別動画URL抽出クラス"""

    def __init__(self, yt_dlp_path: str) -> None:
        self.yt_dlp_path = yt_dlp_path

    def _is_valid_youtube_url(self, url: str) -> bool:
        """YouTube URLの有効性を検証"""
        # より包括的で重複のないパターン
        youtube_pattern = r'https?://(?:(?:www|music|gaming)\.)?youtube\.com/|https?://youtu\.be/'
        return bool(re.match(youtube_pattern, url))

    async def extract_video_urls(self, playlist_url: str) -> list[str]:
        """プレイリストから個別動画URLリストを取得"""
        try:

            # yt-dlpでプレイリストから動画URLのみを抽出
            cmd = [
                self.yt_dlp_path,
                "--flat-playlist",
                "--get-url",
                playlist_url
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                urls = stdout.decode('utf-8', errors='ignore').strip().split('\n')
                valid_urls = []
                for url in urls:
                    url = url.strip()
                    # 有効なYouTube URLのみをフィルタリング
                    if url and self._is_valid_youtube_url(url):
                        valid_urls.append(url)
                return valid_urls
            else:
                # エラーの場合は空リストを返す
                return []

        except Exception:
            return []

    async def extract_video_info(self, playlist_url: str) -> list[tuple[str, str]]:
        """プレイリストから動画情報（URL, タイトル）を取得"""
        try:

            cmd = [
                self.yt_dlp_path,
                "--flat-playlist",
                "--print", "%(url)s|%(title)s",
                playlist_url
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                lines = stdout.decode('utf-8', errors='ignore').strip().split('\n')
                video_info = []

                for line in lines:
                    if '|' in line:
                        url, title = line.split('|', 1)
                        video_info.append((url.strip(), title.strip()))

                return video_info
            else:
                return []

        except Exception:
            return []
