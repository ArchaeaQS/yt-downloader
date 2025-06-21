"""ダウンロード管理モジュール"""

import asyncio
import os
import subprocess
import sys
from concurrent.futures import Future
from pathlib import Path
from threading import Thread
from typing import AsyncIterable, Callable, Optional

import tool_manager


class DownloadState:
    """ダウンロード状態を管理するクラス"""

    def __init__(self) -> None:
        self.is_downloading = False
        self.stop_requested = False
        self.current_download_task: Optional[Future[None]] = None
        self.process: Optional[subprocess.Popen[bytes]] = None
        self.current_phase = "video"  # video, audio, merging


class DownloadManager:
    """YouTubeダウンロード管理クラス"""

    def __init__(self) -> None:
        self.state = DownloadState()
        self.tool_manager_instance = tool_manager.ToolManager()

        # プログレス更新コールバック
        self.progress_callback: Optional[Callable[[float, str], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None
        self.error_callback: Optional[Callable[[str], None]] = None
        self.success_callback: Optional[Callable[[], None]] = None

        # 非同期ループとスレッドの初期化
        self.asyncio_loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._start_asyncio_loop, daemon=True)
        self.thread.start()

        # ツールの初期化
        self._initialize_tools()

    def _start_asyncio_loop(self) -> None:
        """非同期ループの開始"""
        asyncio.set_event_loop(self.asyncio_loop)
        self.asyncio_loop.run_forever()

    def _initialize_tools(self) -> None:
        """必要なツールの初期化"""
        self.tool_manager_instance.check_and_download_ffmpeg()
        self.tool_manager_instance.check_and_download_yt_dlp()
        self.tool_manager_instance.check_and_download_atomicparsley()

    def set_callbacks(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None,
        error_callback: Optional[Callable[[str], None]] = None,
        success_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """コールバック関数の設定"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.error_callback = error_callback
        self.success_callback = success_callback

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

        # プロセスを終了
        if self.state.process and self.state.process.poll() is None:
            try:
                self.state.process.terminate()
                # 少し待ってから強制終了
                try:
                    self.state.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.state.process.kill()
            except Exception:
                pass

        # 非同期タスクをキャンセル
        if self.state.current_download_task and not self.state.current_download_task.done():
            self.state.current_download_task.cancel()
            self.state.current_download_task = None

        self._cleanup_after_stop()

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
        self.state.current_phase = "video"

        if self.status_callback:
            self.status_callback("ダウンロードを開始します...")

    def _cleanup_after_stop(self) -> None:
        """停止後のクリーンアップ"""
        self.state.is_downloading = False
        self.state.process = None

        if self.status_callback:
            self.status_callback("ダウンロードを中止しました")

    def _cleanup_after_completion(self) -> None:
        """完了後のクリーンアップ"""
        self.state.is_downloading = False
        self.state.stop_requested = False
        self.state.process = None

    def get_cookie_file_path(self) -> Path:
        """Cookie ファイルのパスを取得"""
        return Path.home() / "AppData" / "Local" / "yt-downloader" / "cookies.txt"

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

        # Cookie設定
        if use_browser_cookies:
            cmd.extend(["--cookies-from-browser", "firefox"])
        else:
            cookie_file = self.get_cookie_file_path()
            if cookie_file.exists():
                cmd.extend(["--cookies", str(cookie_file)])

        # サムネイルとメタデータの設定
        cmd.extend([
            "--embed-thumbnail",        # サムネイルを動画に埋め込み（一時ファイルは自動削除）
            "--embed-metadata",         # メタデータを埋め込み
            "--embed-chapters",         # チャプター情報を埋め込み
        ])

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

            if self.status_callback:
                self.status_callback("ダウンロード中...")

            # 出力を監視してプログレスを更新
            async for line in self._read_process_output():
                if self.state.stop_requested:
                    break
                self._parse_progress_line(line)

            # プロセスの完了を待機
            if not self.state.stop_requested:
                await self.state.process.wait()

        except asyncio.CancelledError:
            if self.state.process:
                self.state.process.terminate()
            raise

    async def _read_process_output(self) -> AsyncIterable[str]:
        """プロセス出力の非同期読み取り"""
        if not self.state.process or not self.state.process.stdout:
            return

        try:
            while True:
                line = await self.state.process.stdout.readline()
                if not line:
                    break
                yield line.decode("utf-8", errors="ignore").strip()
        except Exception:
            pass

    def _parse_progress_line(self, line: str) -> None:
        """プログレス行の解析"""
        try:
            # フェーズ変更の検出
            if "[download]" in line:
                if "Downloading video" in line or ("video" in line.lower() and self.state.current_phase == "video"):
                    self.state.current_phase = "video"
                elif "Downloading audio" in line or ("audio" in line.lower() and self.state.current_phase != "merging"):
                    self.state.current_phase = "audio"
                elif "Merging formats" in line or "Post-processing" in line:
                    self.state.current_phase = "merging"

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
                            if self.state.current_phase == "video":
                                status_text = f"動画をダウンロード中: {percent:.1f}%{speed_info}"
                            elif self.state.current_phase == "audio":
                                status_text = f"音声を取得中: {percent:.1f}%{speed_info}"
                            else:
                                status_text = f"処理中: {percent:.1f}%{speed_info}"

                            # プログレス更新
                            if self.progress_callback:
                                self.progress_callback(percent, status_text)
                            break
                        except ValueError:
                            continue

            # ffmpegの結合処理を検出
            elif "ffmpeg" in line.lower() or "Merging" in line:
                self.state.current_phase = "merging"
                if self.status_callback:
                    self.status_callback("動画と音声を結合中...")

        except Exception:
            # プログレス解析エラーは無視
            pass


# 型チェック用のAsyncIterableのインポート
