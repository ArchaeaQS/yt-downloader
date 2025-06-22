"""UIテーマとスタイル定義"""

from __future__ import annotations



class ModernTheme:
    """モダンなUIテーマクラス"""


    # CustomTkinter専用カラー定数
    CTK_COLORS = {
        # プライマリーボタンカラー
        "button_primary": "#1f8af0",
        "button_primary_hover": "#1565c0",
        # セカンダリボタンカラー  
        "button_secondary": "gray",
        "button_secondary_hover": "#555555",
        # 危険ボタンカラー
        "button_danger": "#d32f2f", 
        "button_danger_hover": "#b71c1c",
        # 背景色
        "bg_dark": "#212121",
        # プログレスバーカラー
        "progress_bar": "#1f8af0",
        # テキストカラー
        "text_muted": "gray",
    }

    # ウィンドウサイズ定数
    WINDOW_SIZE = {
        "width": 950,
        "height": 900,
        "min_width": 950,
        "min_height": 900,
        "tabview_width": 900,
        "tabview_height": 800,
    }

    # パディング/マージン定数
    SPACING = {
        "xs": 2,
        "sm": 5,
        "md": 10,
        "lg": 15,
        "xl": 20,
        "card_padding": 15,
        "section_padding": 20,
    }















class IconManager:
    """アイコン管理クラス（Unicode絵文字を使用）"""

    ICONS = {
        "download": "⬇️",
        "settings": "⚙️",
        "folder": "📁",
        "play": "▶️",
        "pause": "⏸️",
        "stop": "⏹️",
        "refresh": "🔄",
        "check": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "cookie": "🍪",
        "retry": "🔁",
        "list": "📋",
        "save": "💾",
        "load": "📂",
    }

    @classmethod
    def get(cls, name: str) -> str:
        """アイコンを取得"""
        return cls.ICONS.get(name, "•")
