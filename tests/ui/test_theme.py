"""UIテーマのテスト"""
from __future__ import annotations

from ui.theme import IconManager, ModernTheme


class TestModernTheme:
    """ModernThemeクラスのテスト"""

    def test_ctk_color_definitions(self) -> None:
        """CustomTkinterカラー定義テスト"""
        # 必要なカラーが定義されていることを確認
        required_colors = [
            "button_primary", "button_primary_hover", "button_secondary",
            "button_danger", "bg_dark", "progress_bar", "text_muted"
        ]

        for color in required_colors:
            assert color in ModernTheme.CTK_COLORS
            assert isinstance(ModernTheme.CTK_COLORS[color], str)


    def test_spacing_definitions(self) -> None:
        """スペーシング定義テスト"""
        required_spacing = ["xs", "sm", "md", "lg", "xl", "card_padding", "section_padding"]

        for spacing in required_spacing:
            assert spacing in ModernTheme.SPACING
            assert isinstance(ModernTheme.SPACING[spacing], int)
            assert ModernTheme.SPACING[spacing] > 0

    def test_window_size_definitions(self) -> None:
        """ウィンドウサイズ定義テスト"""
        required_sizes = ["width", "height", "min_width", "min_height", "tabview_width", "tabview_height"]

        for size in required_sizes:
            assert size in ModernTheme.WINDOW_SIZE
            assert isinstance(ModernTheme.WINDOW_SIZE[size], int)
            assert ModernTheme.WINDOW_SIZE[size] > 0




class TestIconManager:
    """IconManagerクラスのテスト"""

    def test_icon_definitions(self) -> None:
        """アイコン定義テスト"""
        # 必要なアイコンが定義されていることを確認
        required_icons = [
            "download", "settings", "folder", "play", "pause",
            "stop", "refresh", "check", "error", "warning"
        ]

        for icon in required_icons:
            assert icon in IconManager.ICONS
            assert isinstance(IconManager.ICONS[icon], str)
            assert len(IconManager.ICONS[icon]) > 0

    def test_get_icon_method(self) -> None:
        """アイコン取得メソッドテスト"""
        # 存在するアイコンの取得
        download_icon = IconManager.get("download")
        assert isinstance(download_icon, str)
        assert download_icon == IconManager.ICONS["download"]

        # 存在しないアイコンの取得（デフォルト値）
        unknown_icon = IconManager.get("unknown_icon")
        assert isinstance(unknown_icon, str)
        assert unknown_icon == "•"

    def test_all_icons_are_strings(self) -> None:
        """全アイコンが文字列であることのテスト"""
        for icon_name, icon_value in IconManager.ICONS.items():
            assert isinstance(icon_value, str), f"Icon {icon_name} is not a string"
            assert len(icon_value) > 0, f"Icon {icon_name} is empty"


class TestThemeIntegration:
    """テーマ統合テスト"""

    def test_ctk_color_consistency(self) -> None:
        """CustomTkinterカラー一貫性テスト"""
        # プライマリカラーとホバーカラーの関係
        primary = ModernTheme.CTK_COLORS["button_primary"]
        primary_hover = ModernTheme.CTK_COLORS["button_primary_hover"]

        assert primary != primary_hover
        assert isinstance(primary, str)
        assert isinstance(primary_hover, str)

    def test_theme_completeness(self) -> None:
        """テーマ完全性テスト"""
        # 必要な設定項目が全て定義されていることを確認
        assert hasattr(ModernTheme, 'CTK_COLORS')
        assert hasattr(ModernTheme, 'WINDOW_SIZE')
        assert hasattr(ModernTheme, 'SPACING')

        # 各辞書が空でないことを確認
        assert len(ModernTheme.CTK_COLORS) > 0
        assert len(ModernTheme.WINDOW_SIZE) > 0
        assert len(ModernTheme.SPACING) > 0
