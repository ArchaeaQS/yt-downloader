@echo off
echo テストを実行中...

:: uvでテスト実行（Windows）
uv run python run_tests.py %*

pause