#!/usr/bin/env python3
"""テスト実行スクリプト"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_tests() -> int:
    """pytestを実行してテスト結果を返す"""
    project_root = Path(__file__).parent
    
    # pytestコマンドを構築
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(project_root / "tests"),
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    print("🧪 テストを実行中...")
    print(f"実行コマンド: {' '.join(pytest_cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(pytest_cmd, cwd=project_root)
        return result.returncode
    except FileNotFoundError:
        print("❌ pytestが見つかりません。以下のコマンドでインストールしてください:")
        print("uv sync --dev")
        return 1
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return 1


def run_tests_with_coverage() -> int:
    """カバレッジ付きでテストを実行"""
    project_root = Path(__file__).parent
    
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(project_root / "tests"),
        "--cov=.",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v"
    ]
    
    print("🧪 カバレッジ付きテストを実行中...")
    print(f"実行コマンド: {' '.join(pytest_cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(pytest_cmd, cwd=project_root)
        if result.returncode == 0:
            print("\n📊 カバレッジレポートが htmlcov/ ディレクトリに生成されました")
        return result.returncode
    except FileNotFoundError:
        print("❌ pytest-covが見つかりません。以下のコマンドでインストールしてください:")
        print("uv add --dev pytest-cov")
        return 1


def run_specific_test(test_path: str) -> int:
    """特定のテストファイルまたはテストクラスを実行"""
    project_root = Path(__file__).parent
    
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        test_path,
        "-v",
        "--tb=short"
    ]
    
    print(f"🧪 特定のテスト '{test_path}' を実行中...")
    print(f"実行コマンド: {' '.join(pytest_cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(pytest_cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"❌ テスト実行中にエラーが発生しました: {e}")
        return 1


def main() -> None:
    """メイン関数"""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "coverage":
            exit_code = run_tests_with_coverage()
        elif command == "specific" and len(sys.argv) > 2:
            test_path = sys.argv[2]
            exit_code = run_specific_test(test_path)
        elif command == "help":
            print("📖 使用方法:")
            print("  python run_tests.py          # 全テストを実行")
            print("  python run_tests.py coverage # カバレッジ付きテスト実行")
            print("  python run_tests.py specific <path> # 特定テスト実行")
            print("  python run_tests.py help     # このヘルプを表示")
            print("\n📝 テストファイル例:")
            print("  tests/test_tool_manager.py")
            print("  tests/utils/test_cookie_manager.py")
            print("  tests/download/test_manager.py")
            exit_code = 0
        else:
            print("❌ 無効なコマンドです。'python run_tests.py help' でヘルプを確認してください。")
            exit_code = 1
    else:
        exit_code = run_tests()
    
    # 結果の表示
    print("-" * 50)
    if exit_code == 0:
        print("✅ すべてのテストが成功しました！")
    else:
        print("❌ テストが失敗しました。")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()