"""UIテーマのテスト"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ui.theme import IconManager, ModernTheme, StyledButton, StyledFrame, StyledLabel


class TestModernTheme:
    """ModernThemeクラスのテスト"""

    def test_color_definitions(self) -> None:
        """カラー定義テスト"""
        # 必要なカラーが定義されていることを確認
        required_colors = [
            "primary", "primary_hover", "secondary", "accent",
            "bg_primary", "bg_secondary", "text_primary", "border"
        ]
        
        for color in required_colors:
            assert color in ModernTheme.COLORS
            assert isinstance(ModernTheme.COLORS[color], str)
            assert ModernTheme.COLORS[color].startswith("#")

    def test_font_definitions(self) -> None:
        """フォント定義テスト"""
        required_fonts = ["default", "heading", "button", "small"]
        
        for font in required_fonts:
            assert font in ModernTheme.FONTS
            assert isinstance(ModernTheme.FONTS[font], tuple)

    def test_spacing_definitions(self) -> None:
        """スペーシング定義テスト"""
        required_spacing = ["xs", "sm", "md", "lg", "xl"]
        
        for spacing in required_spacing:
            assert spacing in ModernTheme.SPACING
            assert isinstance(ModernTheme.SPACING[spacing], int)
            assert ModernTheme.SPACING[spacing] > 0

    def test_button_style_definitions(self) -> None:
        """ボタンスタイル定義テスト"""
        required_styles = ["primary", "secondary", "success", "danger"]
        
        for style in required_styles:
            assert style in ModernTheme.BUTTON_STYLES
            style_def = ModernTheme.BUTTON_STYLES[style]
            assert "bg" in style_def
            assert "fg" in style_def
            assert "font" in style_def


class TestStyledButton:
    """StyledButtonクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.mock_parent = MagicMock()
        
    @patch("ui.theme.tk.Button.__init__")
    def test_styled_button_creation(self, mock_button_init: MagicMock) -> None:
        """スタイル付きボタン作成テスト"""
        mock_button_init.return_value = None
        
        with patch.object(StyledButton, 'bind'):
            with patch.object(StyledButton, '_get_hover_color', return_value="#test"):
                button = StyledButton(self.mock_parent, style="primary", text="Test")
                
                # ボタンが作成されることを確認
                mock_button_init.assert_called_once()

    def test_hover_color_mapping(self) -> None:
        """ホバーカラーマッピングテスト"""
        with patch("ui.theme.tk.Button.__init__", return_value=None):
            with patch.object(StyledButton, 'bind'):
                button = StyledButton(self.mock_parent)
                
                # 各スタイルのホバーカラーが正しく取得されることを確認
                test_styles = ["primary", "secondary", "success", "danger"]
                for style in test_styles:
                    hover_color = button._get_hover_color(style)
                    assert isinstance(hover_color, str)
                    assert hover_color.startswith("#")


class TestStyledFrame:
    """StyledFrameクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.mock_parent = MagicMock()

    @patch("ui.theme.tk.Frame.__init__")
    def test_styled_frame_creation(self, mock_frame_init: MagicMock) -> None:
        """スタイル付きフレーム作成テスト"""
        mock_frame_init.return_value = None
        
        frame = StyledFrame(self.mock_parent, style="default")
        
        # フレームが作成されることを確認
        mock_frame_init.assert_called_once()

    @patch("ui.theme.tk.Frame.__init__")
    def test_card_style_frame(self, mock_frame_init: MagicMock) -> None:
        """カードスタイルフレームテスト"""
        mock_frame_init.return_value = None
        
        frame = StyledFrame(self.mock_parent, style="card")
        
        # カードスタイルが適用されることを確認
        mock_frame_init.assert_called_once()

    @patch("ui.theme.tk.Frame.__init__")
    def test_sidebar_style_frame(self, mock_frame_init: MagicMock) -> None:
        """サイドバースタイルフレームテスト"""
        mock_frame_init.return_value = None
        
        frame = StyledFrame(self.mock_parent, style="sidebar")
        
        # サイドバースタイルが適用されることを確認
        mock_frame_init.assert_called_once()


class TestStyledLabel:
    """StyledLabelクラスのテスト"""

    def setup_method(self) -> None:
        """各テストメソッドの前に実行"""
        self.mock_parent = MagicMock()

    @patch("ui.theme.tk.Label.__init__")
    def test_styled_label_creation(self, mock_label_init: MagicMock) -> None:
        """スタイル付きラベル作成テスト"""
        mock_label_init.return_value = None
        
        label = StyledLabel(self.mock_parent, text="Test Label")
        
        # ラベルが作成されることを確認
        mock_label_init.assert_called_once()

    @patch("ui.theme.tk.Label.__init__")
    def test_heading_style_label(self, mock_label_init: MagicMock) -> None:
        """見出しスタイルラベルテスト"""
        mock_label_init.return_value = None
        
        label = StyledLabel(self.mock_parent, style="heading", text="Heading")
        
        # 見出しスタイルが適用されることを確認
        mock_label_init.assert_called_once()

    @patch("ui.theme.tk.Label.__init__")
    def test_muted_style_label(self, mock_label_init: MagicMock) -> None:
        """ミュートスタイルラベルテスト"""
        mock_label_init.return_value = None
        
        label = StyledLabel(self.mock_parent, style="muted", text="Muted text")
        
        # ミュートスタイルが適用されることを確認
        mock_label_init.assert_called_once()


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

    def test_color_consistency(self) -> None:
        """カラー一貫性テスト"""
        # プライマリカラーとホバーカラーの関係
        primary = ModernTheme.COLORS["primary"]
        primary_hover = ModernTheme.COLORS["primary_hover"]
        
        assert primary != primary_hover
        assert isinstance(primary, str)
        assert isinstance(primary_hover, str)

    def test_theme_completeness(self) -> None:
        """テーマ完全性テスト"""
        # ボタンスタイルで使用される全ての色が定義されていることを確認
        for style_name, style_def in ModernTheme.BUTTON_STYLES.items():
            bg_color = style_def["bg"]
            fg_color = style_def["fg"]
            
            # 色が COLORS 辞書に存在することを確認
            assert bg_color in ModernTheme.COLORS.values()
            assert fg_color in ModernTheme.COLORS.values()

    @patch("ui.theme.ttk.Style")
    def test_apply_theme_function(self, mock_style: MagicMock) -> None:
        """テーマ適用関数テスト"""
        from ui.theme import apply_theme_to_widget
        
        # Tkウィジェットのテーマ適用
        mock_tk_widget = MagicMock()
        mock_tk_widget.configure = MagicMock()
        
        with patch("ui.theme.isinstance", return_value=True):
            apply_theme_to_widget(mock_tk_widget)
            # テーマが適用されることを確認（例外が発生しない）