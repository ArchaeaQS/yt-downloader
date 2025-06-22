"""ダウンロード管理モジュール"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterable, Callable
from concurrent.futures import Future
from pathlib import Path
from threading import Thread

import tool_manager
from download.retry_handler import PlaylistExtractor, RetryConfig, RetryHandler


class DownloadState:
    """ダウンロード状態を管理するクラス"""

    def __init__(self) -> None:
        self.is_downloading = False
        self.stop_requested = False
        self.current_download_task: Future[None] | None = None
        self.process: asyncio.subprocess.Process | None = None
        self.process_pid: int | None = None
        self.current_phase = "video"  # video, audio, merging


class DownloadManager:
    """YouTubeダウンロード管理クラス"""

    def __init__(self) -> None:
        self.state = DownloadState()
        self.tool_manager_instance = tool_manager.ToolManager()

        # プログレス更新コールバック
        self.progress_callback: Callable[[float, str], None] | None = None
        self.status_callback: Callable[[str], None] | None = None
        self.error_callback: Callable[[str], None] | None = None
        self.success_callback: Callable[[], None] | None = None
        self.cookie_refresh_callback: Callable[[], bool] | None = None

        # リトライ機能
        self.retry_config = RetryConfig()
        self.retry_handler = RetryHandler(self.retry_config)
        self.playlist_extractor: PlaylistExtractor | None = None

        # 非同期ループとスレッドの初期化
        self.asyncio_loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._start_asyncio_loop, daemon=True)
        self.thread.start()

        # ツールの初期化
        self._initialize_tools()

        # リトライハンドラーのセットアップ
        self._setup_retry_handler()

    def _start_asyncio_loop(self) -> None:
        """非同期ループの開始"""
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    def _initialize_tools(self) -> None:
        """必要なツールの初期化"""
        self.tool_manager_instance.check_and_download_ffmpeg()
        self.tool_manager_instance.check_and_download_yt_dlp()
        self.tool_manager_instance.check_and_download_atomicparsley()

        # プレイリスト抽出器の初期化
        yt_dlp_path = str(self.tool_manager_instance._get_tool_path("yt-dlp.exe"))
        self.playlist_extractor = PlaylistExtractor(yt_dlp_path)

    def _setup_retry_handler(self) -> None:
        """リトライハンドラーのセットアップ"""
        self.retry_handler.set_callbacks(
            on_retry_attempt=self._on_retry_attempt,
            on_cookie_refresh_request=self._on_cookie_refresh_request,
            on_individual_download=self._on_individual_download,
        )

    def set_callbacks(
        self,
        progress_callback: Callable[[float, str], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
        error_callback: Callable[[str], None] | None = None,
        success_callback: Callable[[], None] | None = None,
        cookie_refresh_callback: Callable[[], bool] | None = None,
    ) -> None:
        """コールバック関数の設定"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.error_callback = error_callback
        self.success_callback = success_callback
        self.cookie_refresh_callback = cookie_refresh_callback

    def start_download(self, url: str, save_folder: str, quality: str, use_browser_cookies: bool) -> bool:
        """ダウンロードの開始"""
        if not self._validate_params(url, save_folder):
            return False

        if self.state.is_downloading:
            if self.error_callback:
                self.error_callback("既にダウンロード中です")
            return False

        self._prepare_download()
        self.state.current_download_task = asyncio.run_coroutine_threadsafe(
            self._download_video_async(url, save_folder, quality, use_browser_cookies), self.asyncio_loop
        )
        return True

    def stop_download(self) -> None:
        """ダウンロードの停止"""
        self.state.stop_requested = True

        # 同期的に即座にプロセスを強制終了
        self._kill_process_immediately()

        # 非同期タスクをキャンセル
        if self.state.current_download_task and not self.state.current_download_task.done():
            self.state.current_download_task.cancel()
            self.state.current_download_task = None

        # 非同期でも停止処理を実行
        asyncio.run_coroutine_threadsafe(self._immediate_force_stop(), self.asyncio_loop)

        self._cleanup_after_stop()

    async def _stop_process_async(self) -> None:
        """非同期でプロセスを停止"""
        if self.state.process and self.state.process.returncode is None:
            try:
                # まず通常の終了を試行
                self.state.process.terminate()

                # 3秒待機
                try:
                    await asyncio.wait_for(self.state.process.wait(), timeout=3.0)
                except asyncio.TimeoutError:
                    # タイムアウトした場合は強制終了
                    try:
                        self.state.process.kill()
                        await self.state.process.wait()
                    except Exception:
                        pass
            except Exception:
                pass

    async def _force_stop_process(self) -> None:
        """プロセスを強制的に停止"""
        if self.state.process and self.state.process.returncode is None:
            try:
                # Windowsの場合、追加のプロセス終了処理
                if sys.platform == "win32":
                    try:
                        # プロセスツリー全体を終了
                        import psutil

                        parent = psutil.Process(self.state.process.pid)
                        for child in parent.children(recursive=True):
                            child.kill()
                        parent.kill()
                    except (ImportError, Exception):
                        # psutilが利用できない場合は通常のkill
                        self.state.process.kill()
                else:
                    # Linux/macOSの場合
                    self.state.process.kill()

                # プロセス終了を待機
                await self.state.process.wait()
            except Exception:
                pass

    async def _immediate_force_stop(self) -> None:
        """即座にプロセスを強制停止（プロセスIDを使用）"""
        # プロセスIDを使用して直接kill
        if self.state.process_pid:
            try:
                if sys.platform == "win32":
                    # Windows: taskkillコマンドでプロセスツリーを強制終了
                    import subprocess

                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.state.process_pid)],
                        check=False,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW,
                    )
                else:
                    # Linux/macOS: killコマンドでプロセスを終了
                    import os
                    import signal

                    try:
                        os.kill(self.state.process_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass  # プロセスが既に終了している
            except Exception:
                pass

        # asyncio.subprocess.Processオブジェクトも停止を試行
        if self.state.process and self.state.process.returncode is None:
            try:
                self.state.process.kill()
                await asyncio.wait_for(self.state.process.wait(), timeout=1.0)
            except Exception:
                pass

        # プロセス情報をクリア
        self.state.process_pid = None

    def _kill_process_immediately(self) -> None:
        """同期的にプロセスを即座に強制終了"""
        import os
        import signal
        import subprocess

        # 1. 保存されたプロセスIDを使用してkill
        if self.state.process_pid:
            try:
                if sys.platform == "win32":
                    # Windows: taskkillで強制終了
                    result = subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(self.state.process_pid)],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if self.status_callback:
                        self.status_callback(f"Taskkill PID {self.state.process_pid}: 戻り値 {result.returncode}")
                else:
                    # Linux/macOS: killコマンド
                    os.kill(self.state.process_pid, signal.SIGKILL)
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"PID kill failed: {e}")

        # 2. プロセス名で検索してyt-dlp関連プロセスをすべてkill
        try:
            if sys.platform == "win32":
                # Windows: yt-dlp.exeプロセスをすべて強制終了
                result1 = subprocess.run(
                    ["taskkill", "/F", "/IM", "yt-dlp.exe"], capture_output=True, text=True, timeout=5
                )

                # ffmpeg.exeも停止
                result2 = subprocess.run(
                    ["taskkill", "/F", "/IM", "ffmpeg.exe"], capture_output=True, text=True, timeout=5
                )

                if self.status_callback:
                    self.status_callback(
                        f"プロセス名によるkill: yt-dlp={result1.returncode}, ffmpeg={result2.returncode}"
                    )
            else:
                # Linux/macOS: pkillコマンド
                subprocess.run(["pkill", "-9", "-f", "yt-dlp"], capture_output=True, timeout=5)

                subprocess.run(["pkill", "-9", "-f", "ffmpeg"], capture_output=True, timeout=5)
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Process name kill failed: {e}")

        # 3. asyncio.subprocess.Processオブジェクトも同期的に停止を試行
        if self.state.process:
            try:
                if hasattr(self.state.process, "kill"):
                    self.state.process.kill()
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"Asyncio process kill failed: {e}")

        # プロセス情報をクリア
        self.state.process_pid = None

        # プロセス停止の確認とフィードバック
        self._verify_process_stopped()

    def _verify_process_stopped(self) -> None:
        """プロセスが実際に停止したかを確認"""
        import subprocess
        import time

        time.sleep(0.5)  # 少し待ってから確認

        try:
            if sys.platform == "win32":
                # Windows: tasklist でyt-dlpプロセスを検索
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq yt-dlp.exe"], capture_output=True, text=True, timeout=3
                )

                if "yt-dlp.exe" in result.stdout:
                    if self.status_callback:
                        self.status_callback("警告: yt-dlpプロセスが残っています。再度停止ボタンを押してください")
                else:
                    if self.status_callback:
                        self.status_callback("プロセスを正常に停止しました")
            else:
                # Linux/macOS: pgrep でプロセス検索
                result = subprocess.run(["pgrep", "-f", "yt-dlp"], capture_output=True, text=True, timeout=3)

                if result.stdout.strip():
                    if self.status_callback:
                        self.status_callback("警告: yt-dlpプロセスが残っています。再度停止ボタンを押してください")
                else:
                    if self.status_callback:
                        self.status_callback("プロセスを正常に停止しました")

        except Exception as e:
            if self.status_callback:
                self.status_callback(f"プロセス確認エラー: {e}")

    def _validate_params(self, url: str, save_folder: str) -> bool:
        """パラメータの検証"""
        if not url.strip():
            if self.error_callback:
                self.error_callback("URLを入力してください")
            return False

        if not save_folder.strip():
            if self.error_callback:
                self.error_callback("保存フォルダを選択してください")
            return False

        if not Path(save_folder).exists():
            if self.error_callback:
                self.error_callback("指定された保存フォルダが存在しません")
            return False

        return True

    def _prepare_download(self) -> None:
        """ダウンロード準備"""
        self.state.is_downloading = True
        self.state.stop_requested = False
        self.state.process = None
        self.state.process_pid = None
        self.state.current_phase = "preparing"  # 初期フェーズを準備中に設定

        if self.status_callback:
            self.status_callback("ダウンロードを開始します...")

    def _cleanup_after_stop(self) -> None:
        """停止後のクリーンアップ"""
        self.state.is_downloading = False
        self.state.process = None
        self.state.process_pid = None

        if self.status_callback:
            self.status_callback("ダウンロードを中止しました")

    def _cleanup_after_completion(self) -> None:
        """完了後のクリーンアップ"""
        self.state.is_downloading = False
        self.state.stop_requested = False
        self.state.process = None
        self.state.process_pid = None

    def get_cookie_file_path(self) -> Path:
        """Cookie ファイルのパスを取得"""
        # Windows専用: %USERPROFILE%\AppData\Local\yt-downloader\cookies.txt
        return Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "yt-downloader" / "cookies.txt"

    async def _download_video_async(self, url: str, save_folder: str, quality: str, use_browser_cookies: bool) -> None:
        """非同期ダウンロード処理"""
        try:
            if self.state.stop_requested:
                return

            # 品質から数値を抽出
            quality_num = quality.split()[0].replace("p", "")

            await self._execute_download(url, save_folder, quality_num, use_browser_cookies)

            if not self.state.stop_requested and self.state.is_downloading:
                if self.success_callback:
                    self.success_callback()
                if self.status_callback:
                    self.status_callback("ダウンロード完了！")

        except asyncio.CancelledError:
            if self.status_callback:
                self.status_callback("ダウンロードがキャンセルされました")
        except Exception as e:
            if not self.state.stop_requested and self.state.is_downloading:
                error_msg = f"ダウンロードエラー: {str(e)}"
                if self.error_callback:
                    self.error_callback(error_msg)
        finally:
            self._cleanup_after_completion()

    async def _execute_download(self, url: str, save_folder: str, quality: str, use_browser_cookies: bool) -> None:
        """ダウンロードの実行"""
        yt_dlp_path = self.tool_manager_instance._get_tool_path("yt-dlp.exe")

        # コマンドライン引数の構築
        cmd = [
            str(yt_dlp_path),
            "--progress",  # プログレス情報を出力
            "--newline",  # 各プログレス更新を新しい行に出力
        ]

        # Cookie設定の検証と適用
        cookie_configured = await self._configure_cookies(cmd, use_browser_cookies, url)
        if not cookie_configured:
            # Cookie設定が必要だが設定されていない場合、ダウンロードを中止
            return

        # サムネイルとメタデータの設定
        cmd.extend(
            [
                "--embed-thumbnail",  # サムネイルを動画に埋め込み（一時ファイルは自動削除）
                "--embed-metadata",  # メタデータを埋め込み
                "--embed-chapters",  # チャプター情報を埋め込み
            ]
        )

        # フォーマットと出力設定
        cmd.extend(
            [
                "-f",
                f"bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best",
                "-o",
                os.path.join(save_folder, "%(title)s.%(ext)s"),
                url,
            ]
        )

        # プロセス実行
        await self._run_download_process(cmd)

    async def _configure_cookies(self, cmd: list[str], use_browser_cookies: bool, url: str) -> bool:
        """Cookie設定の検証と適用"""
        if use_browser_cookies:
            # ブラウザからCookie取得
            cmd.extend(["--cookies-from-browser", "firefox"])
            return True
        else:
            # 手動Cookie設定の確認
            cookie_file = self.get_cookie_file_path()
            if cookie_file.exists() and cookie_file.stat().st_size > 0:
                # Cookieファイルが存在し、空でない場合
                cmd.extend(["--cookies", str(cookie_file)])
                return True
            else:
                # Cookieファイルが存在しないか空の場合、メンバー限定動画かチェック
                return await self._check_if_cookies_needed(url)

    async def _check_if_cookies_needed(self, url: str) -> bool:
        """URLがメンバー限定動画かどうかを事前チェック"""
        try:
            # yt-dlpで情報のみ取得（ダウンロードはしない）
            yt_dlp_path = self.tool_manager_instance._get_tool_path("yt-dlp.exe")

            info_cmd = [str(yt_dlp_path), "--dump-json", "--no-download", url]

            process = await asyncio.create_subprocess_exec(
                *info_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_output = stderr.decode("utf-8", errors="ignore")

                # メンバー限定動画やプライベート動画の典型的なエラーメッセージをチェック
                member_only_errors = [
                    "members-only",
                    "private video",
                    "video is private",
                    "requires authentication",
                    "login required",
                    "this video is only available for",
                    "membership required",
                ]

                if any(error in error_output.lower() for error in member_only_errors):
                    # メンバー限定動画の場合、Cookieが必要であることを通知
                    if self.error_callback:
                        self.error_callback(
                            "このメンバー限定動画をダウンロードするには、Cookieの設定が必要です。\n"
                            "「Cookie設定」ボタンからCookieを設定するか、\n"
                            "「ブラウザからCookieを自動取得する」にチェックを入れてください。"
                        )
                    return False
                else:
                    # その他のエラーの場合は、Cookieなしで続行を試みる
                    if self.status_callback:
                        self.status_callback("警告: 動画情報の事前取得に失敗しましたが、ダウンロードを続行します")
                    return True
            else:
                # 正常に情報取得できた場合はCookieなしで問題なし
                return True

        except Exception as e:
            # 事前チェックでエラーが発生した場合は、ダウンロードを続行
            if self.status_callback:
                self.status_callback(
                    f"動画情報の事前チェックでエラーが発生しましたが、ダウンロードを続行します: {str(e)[:50]}..."
                )
            return True

    async def _run_download_process(self, cmd: list[str]) -> None:
        """ダウンロードプロセスの実行とプログレス監視"""
        try:
            # プロセスを開始
            self.state.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            # プロセスIDを保存
            self.state.process_pid = self.state.process.pid

            if self.status_callback:
                self.status_callback("ダウンロード中...")

            # 出力を監視してプログレスを更新
            async for line in self._read_process_output():
                if self.state.stop_requested:
                    # 停止要求があった場合、プロセスを即座に強制終了
                    await self._force_stop_process()
                    break
                self._parse_progress_line(line)

            # プロセスの完了を待機
            if not self.state.stop_requested:
                await self.state.process.wait()
            else:
                # 停止要求があった場合は強制終了を確認
                await self._force_stop_process()

        except asyncio.CancelledError:
            # キャンセルされた場合はプロセスを停止
            if self.state.process and self.state.process.returncode is None:
                try:
                    self.state.process.terminate()
                    # 少し待ってから強制終了
                    try:
                        await asyncio.wait_for(self.state.process.wait(), timeout=2.0)
                    except asyncio.TimeoutError:
                        self.state.process.kill()
                        await self.state.process.wait()
                except Exception:
                    pass
            raise

    async def _read_process_output(self) -> AsyncIterable[str]:
        """プロセス出力の非同期読み取り"""
        if not self.state.process or not self.state.process.stdout:
            return

        try:
            while True:
                # 停止要求をチェック
                if self.state.stop_requested:
                    # 停止要求があった場合、プロセスを即座に終了
                    await self._force_stop_process()
                    break

                try:
                    # タイムアウト付きで行を読み取り
                    line = await asyncio.wait_for(self.state.process.stdout.readline(), timeout=1.0)
                    if not line:
                        break
                    yield line.decode("utf-8", errors="ignore").strip()
                except asyncio.TimeoutError:
                    # タイムアウトした場合は続行（停止チェックのため）
                    continue
        except Exception:
            pass

    def _parse_progress_line(self, line: str) -> None:
        """プログレス行の解析"""
        try:
            # より詳細なフェーズ判定
            current_phase = self._detect_download_phase(line)
            if current_phase:
                self.state.current_phase = current_phase

            # プログレス情報の抽出
            if "[download]" in line and "%" in line:
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.endswith("%"):
                        try:
                            percent_str = part.replace("%", "")
                            percent = float(percent_str)

                            # 速度情報があれば取得
                            speed_info = ""
                            if i + 1 < len(parts) and ("MiB/s" in parts[i + 1] or "KiB/s" in parts[i + 1]):
                                speed_info = f", 速度: {parts[i + 1]}"

                            # フェーズに応じたステータステキスト
                            status_text = self._get_phase_status_text(percent, speed_info, line)

                            # プログレス更新
                            if self.progress_callback:
                                self.progress_callback(percent, status_text)
                            break
                        except ValueError:
                            continue

            # ffmpegの結合処理を検出
            elif "ffmpeg" in line.lower() or "Merging" in line or "merging" in line.lower():
                self.state.current_phase = "merging"
                if self.status_callback:
                    self.status_callback("動画と音声を結合中...")

            # Cookieエラーの検出
            elif self._is_cookie_error(line):
                if self.error_callback:
                    self.error_callback(
                        "メンバー限定動画のダウンロードにはCookieが必要です。\n"
                        "「Cookie設定」ボタンからCookieを設定するか、\n"
                        "「ブラウザからCookieを自動取得する」にチェックを入れてください。"
                    )
                # ダウンロードを停止
                self.state.stop_requested = True

        except Exception:
            # プログレス解析エラーは無視
            pass

    def _is_cookie_error(self, line: str) -> bool:
        """Cookie関連のエラーかどうかを判定"""
        line_lower = line.lower()
        cookie_error_keywords = [
            "members-only",
            "private video",
            "video is private", 
            "requires authentication",
            "login required",
            "this video is only available for",
            "membership required",
            "sign in to confirm your age",
            "access denied",
        ]
        
        # より具体的なCookie関連エラーパターン
        specific_patterns = [
            "video unavailable" in line_lower and ("private" in line_lower or "member" in line_lower),
            "video unavailable" in line_lower and "sign in" in line_lower,
        ]

        return any(keyword in line_lower for keyword in cookie_error_keywords) or any(specific_patterns)

    def _detect_download_phase(self, line: str) -> str | None:
        """ダウンロードフェーズの詳細判定"""
        line_lower = line.lower()

        # ffmpeg処理の検出
        if any(keyword in line_lower for keyword in ["merging", "ffmpeg", "post-processing"]):
            return "merging"

        # ダウンロード行の詳細解析
        if "[download]" in line:
            # yt-dlpの典型的な出力パターンを判定

            # 1. 明確なファイル拡張子の判定（優先度高）
            if ".m4a" in line or ".aac" in line or ".opus" in line or ".mp3" in line:
                return "audio"
            elif ".mp4" in line or ".webm" in line or ".mkv" in line:
                # mp4でもaudioを含む場合は音声ファイル
                if "audio" in line_lower:
                    return "audio"
                return "video"

            # 2. ダウンロードメッセージの内容判定
            if "downloading video" in line_lower:
                return "video"
            elif "downloading audio" in line_lower:
                return "audio"

            # 3. フォーマットIDパターンの判定
            # 例: [download] 100% of 123.45MiB in 00:30
            # または [download] Downloading item 1 of 1
            if "of" in line and ("mib" in line_lower or "kib" in line_lower or "gib" in line_lower):
                # 現在のフェーズを維持（変更しない）
                return None

            # 4. キーワードベースの判定（最後の手段）
            if "audio" in line_lower:
                return "audio"
            elif "video" in line_lower:
                return "video"

        return None

    def _get_phase_status_text(self, percent: float, speed_info: str, line: str) -> str:
        """フェーズに応じたステータステキストを生成"""
        # 行の内容から直接判定（最優先）
        line_lower = line.lower()

        # 1. ファイル拡張子による判定（最も確実）
        if ".m4a" in line or ".aac" in line or ".opus" in line or ".mp3" in line:
            return f"音声を取得中: {percent:.1f}%{speed_info}"
        elif ".mp4" in line or ".webm" in line or ".mkv" in line:
            if "audio" not in line_lower:  # 音声キーワードがない場合のみ動画として扱う
                return f"動画をダウンロード中: {percent:.1f}%{speed_info}"

        # 2. 明確なキーワードによる判定
        if "downloading audio" in line_lower or (
            ("audio" in line_lower) and ("downloading" in line_lower or "%" in line)
        ):
            return f"音声を取得中: {percent:.1f}%{speed_info}"
        elif "downloading video" in line_lower or (
            ("video" in line_lower) and ("downloading" in line_lower or "%" in line)
        ):
            return f"動画をダウンロード中: {percent:.1f}%{speed_info}"
        elif any(keyword in line_lower for keyword in ["merging", "ffmpeg", "post-processing"]):
            return f"動画と音声を結合中: {percent:.1f}%{speed_info}"

        # 3. 現在のフェーズに基づく判定（フォールバック）
        if self.state.current_phase == "video":
            return f"動画をダウンロード中: {percent:.1f}%{speed_info}"
        elif self.state.current_phase == "audio":
            return f"音声を取得中: {percent:.1f}%{speed_info}"
        elif self.state.current_phase == "merging":
            return f"動画と音声を結合中: {percent:.1f}%{speed_info}"
        else:
            return f"ダウンロード中: {percent:.1f}%{speed_info}"

    def _on_retry_attempt(self, retry_count: int, error_message: str) -> None:
        """リトライ試行時のコールバック"""
        if self.status_callback:
            self.status_callback(f"リトライ中 ({retry_count}回目): {error_message[:50]}...")

    def _on_cookie_refresh_request(self) -> bool:
        """Cookie更新要求時のコールバック"""
        if self.cookie_refresh_callback:
            return self.cookie_refresh_callback()
        return False

    async def _on_individual_download(self, playlist_url: str) -> bool:
        """プレイリスト個別ダウンロード処理"""
        if not self.playlist_extractor:
            return False

        try:
            if self.status_callback:
                self.status_callback("プレイリストから動画リストを取得中...")

            # プレイリストから個別動画URLを取得
            video_info = await self.playlist_extractor.extract_video_info(playlist_url)

            if not video_info:
                if self.error_callback:
                    self.error_callback("プレイリストから動画リストを取得できませんでした")
                return False

            if self.status_callback:
                self.status_callback(f"プレイリストから{len(video_info)}個の動画を検出。個別ダウンロードを開始...")

            success_count = 0
            total_count = len(video_info)

            for i, (video_url, title) in enumerate(video_info, 1):
                if self.state.stop_requested:
                    break

                try:
                    if self.status_callback:
                        self.status_callback(f"動画 {i}/{total_count}: {title[:30]}...")

                    # 個別動画のダウンロード実行
                    await self._execute_download(
                        video_url,
                        # 現在の設定を使用
                        self.state.save_folder if hasattr(self.state, "save_folder") else "",
                        self.state.quality if hasattr(self.state, "quality") else "1080",
                        self.state.use_browser_cookies if hasattr(self.state, "use_browser_cookies") else False,
                    )
                    success_count += 1

                except Exception as e:
                    if self.error_callback:
                        self.error_callback(f"動画 '{title}' のダウンロードに失敗: {str(e)[:50]}...")
                    continue

            if self.status_callback:
                self.status_callback(f"個別ダウンロード完了: {success_count}/{total_count} 成功")

            return success_count > 0

        except Exception as e:
            if self.error_callback:
                self.error_callback(f"個別ダウンロード処理エラー: {str(e)}")
            return False

    def update_retry_config(self, enable_retry: bool, max_retries: int, enable_individual_download: bool) -> None:
        """リトライ設定の更新"""
        self.retry_config.max_retries = max_retries if enable_retry else 0
        self.retry_config.individual_download_on_playlist_fail = enable_individual_download


# 型チェック用のAsyncIterableのインポート
