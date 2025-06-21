"""UIテーマとスタイル定義"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ModernTheme:
    """モダンなUIテーマクラス"""

    # カラーパレット
    COLORS = {
        # プライマリーカラー
        "primary": "#007ACC",
        "primary_hover": "#005a9e",
        "primary_light": "#e6f3ff",
        # セカンダリーカラー
        "secondary": "#6c757d",
        "secondary_hover": "#545b62",
        # アクセントカラー
        "accent": "#28a745",
        "accent_hover": "#1e7e34",
        "danger": "#dc3545",
        "danger_hover": "#c82333",
        "warning": "#ffc107",
        "warning_hover": "#e0a800",
        # 背景色
        "bg_primary": "#ffffff",
        "bg_secondary": "#f8f9fa",
        "bg_dark": "#343a40",
        "bg_light": "#f1f3f4",
        # テキストカラー
        "text_primary": "#212529",
        "text_secondary": "#6c757d",
        "text_muted": "#868e96",
        "text_white": "#ffffff",
        # ボーダーカラー
        "border": "#dee2e6",
        "border_light": "#e9ecef",
        "border_dark": "#adb5bd",
    }

    # フォント設定
    FONTS = {
        "default": ("Segoe UI", 9),
        "heading": ("Segoe UI", 12, "bold"),
        "small": ("Segoe UI", 8),
        "button": ("Segoe UI", 9, "bold"),
        "status": ("Segoe UI", 8),
    }

    # スペーシング
    SPACING = {
        "xs": 2,
        "sm": 5,
        "md": 10,
        "lg": 15,
        "xl": 20,
    }

    # ボタンスタイル
    BUTTON_STYLES = {
        "primary": {
            "bg": COLORS["primary"],
            "fg": COLORS["text_white"],
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 8,
            "font": FONTS["button"],
            "cursor": "hand2",
        },
        "secondary": {
            "bg": COLORS["secondary"],
            "fg": COLORS["text_white"],
            "relief": "flat",
            "bd": 0,
            "padx": 15,
            "pady": 6,
            "font": FONTS["default"],
            "cursor": "hand2",
        },
        "success": {
            "bg": COLORS["accent"],
            "fg": COLORS["text_white"],
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 8,
            "font": FONTS["button"],
            "cursor": "hand2",
        },
        "danger": {
            "bg": COLORS["danger"],
            "fg": COLORS["text_white"],
            "relief": "flat",
            "bd": 0,
            "padx": 20,
            "pady": 8,
            "font": FONTS["button"],
            "cursor": "hand2",
        },
    }


class StyledButton(tk.Button):
    """スタイル付きボタンクラス"""

    def __init__(self, parent, style="primary", **kwargs):
        # スタイルを適用
        button_style = ModernTheme.BUTTON_STYLES.get(style, ModernTheme.BUTTON_STYLES["primary"])

        # kwargsとスタイルをマージ
        config = {**button_style, **kwargs}

        super().__init__(parent, **config)

        # ホバーエフェクトを追加
        self.original_bg = config["bg"]
        self.hover_bg = self._get_hover_color(style)

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _get_hover_color(self, style: str) -> str:
        """スタイルに応じたホバーカラーを取得"""
        hover_map = {
            "primary": ModernTheme.COLORS["primary_hover"],
            "secondary": ModernTheme.COLORS["secondary_hover"],
            "success": ModernTheme.COLORS["accent_hover"],
            "danger": ModernTheme.COLORS["danger_hover"],
        }
        return hover_map.get(style, ModernTheme.COLORS["primary_hover"])

    def _on_enter(self, event):
        """マウスホバー時"""
        if self["state"] != "disabled":
            self.config(bg=self.hover_bg)

    def _on_leave(self, event):
        """マウスリーブ時"""
        if self["state"] != "disabled":
            self.config(bg=self.original_bg)

    def _on_click(self, event):
        """クリック時"""
        if self["state"] != "disabled":
            # クリック時の視覚効果
            darker_color = self._darken_color(self.hover_bg)
            self.config(bg=darker_color)

    def _on_release(self, event):
        """クリック解放時"""
        if self["state"] != "disabled":
            self.config(bg=self.hover_bg)

    def _darken_color(self, color: str) -> str:
        """色を暗くする"""
        # 簡易的な色変更
        if color == ModernTheme.COLORS["primary_hover"]:
            return "#003d6b"
        elif color == ModernTheme.COLORS["accent_hover"]:
            return "#155724"
        elif color == ModernTheme.COLORS["danger_hover"]:
            return "#721c24"
        else:
            return color


class StyledFrame(tk.Frame):
    """スタイル付きフレームクラス"""

    def __init__(self, parent, style="default", **kwargs):
        # デフォルトスタイル
        default_config = {
            "bg": ModernTheme.COLORS["bg_primary"],
            "relief": "flat",
            "bd": 0,
        }

        # スタイル別設定
        if style == "card":
            default_config.update(
                {
                    "bg": ModernTheme.COLORS["bg_primary"],
                    "relief": "solid",
                    "bd": 1,
                    "highlightbackground": ModernTheme.COLORS["border_light"],
                }
            )
        elif style == "sidebar":
            default_config.update(
                {
                    "bg": ModernTheme.COLORS["bg_secondary"],
                }
            )

        config = {**default_config, **kwargs}
        super().__init__(parent, **config)


class StyledLabel(tk.Label):
    """スタイル付きラベルクラス"""

    def __init__(self, parent, style="default", **kwargs):
        # デフォルトスタイル
        default_config = {
            "bg": ModernTheme.COLORS["bg_primary"],
            "fg": ModernTheme.COLORS["text_primary"],
            "font": ModernTheme.FONTS["default"],
        }

        # スタイル別設定
        if style == "heading":
            default_config.update(
                {
                    "font": ModernTheme.FONTS["heading"],
                    "fg": ModernTheme.COLORS["text_primary"],
                }
            )
        elif style == "muted":
            default_config.update(
                {
                    "fg": ModernTheme.COLORS["text_muted"],
                    "font": ModernTheme.FONTS["small"],
                }
            )
        elif style == "status":
            default_config.update(
                {
                    "font": ModernTheme.FONTS["status"],
                    "fg": ModernTheme.COLORS["text_secondary"],
                }
            )

        config = {**default_config, **kwargs}
        super().__init__(parent, **config)


class AnimatedProgressbar(ttk.Progressbar):
    """アニメーション付きプログレスバー"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.style = ttk.Style()
        self._setup_style()

    def _setup_style(self):
        """プログレスバーのスタイル設定"""
        self.style.theme_use("clam")

        # カスタムスタイルを作成
        self.style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor=ModernTheme.COLORS["bg_light"],
            background=ModernTheme.COLORS["primary"],
            lightcolor=ModernTheme.COLORS["primary"],
            darkcolor=ModernTheme.COLORS["primary"],
            borderwidth=0,
            relief="flat",
        )

        self.configure(style="Modern.Horizontal.TProgressbar")

    def animate_to(self, target_value: float, duration: int = 500):
        """指定値まで滑らかにアニメーション"""
        current = self["value"]
        steps = 20
        step_value = (target_value - current) / steps
        step_duration = duration // steps

        def update_step(step: int):
            if step <= steps:
                new_value = current + (step_value * step)
                self["value"] = new_value
                self.after(step_duration, lambda: update_step(step + 1))

        update_step(1)


def apply_theme_to_widget(widget, theme_class=None):
    """ウィジェットにテーマを適用"""
    if isinstance(widget, tk.Tk) or isinstance(widget, tk.Toplevel):
        widget.configure(bg=ModernTheme.COLORS["bg_primary"])
    elif isinstance(widget, ttk.Notebook):
        style = ttk.Style()
        style.configure("TNotebook", background=ModernTheme.COLORS["bg_primary"])
        style.configure("TNotebook.Tab", padding=[20, 10])


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
