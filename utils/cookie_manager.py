"""Cookie管理ユーティリティ"""
from __future__ import annotations

import os
from pathlib import Path


class CookieManager:
    """Cookie管理クラス"""
    
    def __init__(self) -> None:
        self.cookie_dir = Path.home() / "AppData" / "Local" / "yt-downloader"
        self.cookie_file = self.cookie_dir / "cookies.txt"
    
    def get_cookie_file_path(self) -> Path:
        """Cookieファイルのパスを取得"""
        return self.cookie_file
    
    def load_cookies(self) -> str:
        """保存されたCookieを読み込み"""
        try:
            if self.cookie_file.exists():
                return self.cookie_file.read_text(encoding="utf-8")
            return ""
        except Exception:
            return ""
    
    def save_cookies(self, cookies: str) -> bool:
        """Cookieを保存"""
        try:
            # ディレクトリが存在しない場合は作成
            self.cookie_dir.mkdir(exist_ok=True, parents=True)
            
            # Cookieファイルに保存
            self.cookie_file.write_text(cookies, encoding="utf-8")
            
            # セキュリティのためファイル権限を設定（Windowsでは効果が限定的）
            try:
                os.chmod(str(self.cookie_file), 0o600)
            except Exception:
                # Windows等で権限設定に失敗した場合は無視
                pass
            
            return True
        except Exception:
            return False
    
    def cookie_file_exists(self) -> bool:
        """Cookieファイルが存在するかチェック"""
        return self.cookie_file.exists()