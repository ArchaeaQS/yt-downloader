# yt-downloader

YouTubeの動画をダウンロードするためのシンプルなデスクトップアプリケーションです

## 機能

- YouTubeの動画をMP4形式でダウンロード
- 動画の画質を選択可能(360p～8K)
- サムネイルの自動埋め込み
- ダウンロード進捗のリアルタイム表示
- Cookie設定によるメンバーシップ限定動画のダウンロードに対応
- プレイリストの一括ダウンロードに対応
- ダウンロードの一時停止機能
- 必要なツール(ffmpeg, yt-dlp, AtomicParsley)の自動ダウンロード

## 使い方

1. .exeファイルを起動
2. 「フォルダ選択」ボタンをクリックして動画を保存するフォルダを選択
3. 「動画URL」欄にYouTube動画のURLもしくはプレイリストのURLを貼り付け
4. 希望する画質を選択
5. 「ダウンロード開始」ボタンをクリック

### メンバーシップ限定動画をダウンロードする場合

1. Chrome拡張機能 "Get cookies.txt LOCALLY" (https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) を追加
2. YouTubeにログインする
3. "Get cookies.txt LOCALLY"拡張機能を起動し「Copy」を押す
4. アプリの「Cookie設定」ボタンをクリックし、コピーしたcookieを貼り付けて保存する

### メンバーシップ限定動画を全てダウンロードしたい場合

Chrome拡張機能 "メン限動画プレイリストView" (https://chromewebstore.google.com/detail/%E3%83%A1%E3%83%B3%E9%99%90%E5%8B%95%E7%94%BB%E3%83%97%E3%83%AC%E3%82%A4%E3%83%AA%E3%82%B9%E3%83%88view/alipjbeolhembeklphfcehbkgncdlnom) の活用をお勧めします

## 注意事項

- 著作権法を遵守してご利用ください
- ダウンロードした動画は個人使用の範囲内でご利用ください
- メンバーシップ限定動画のダウンロードには、該当チャンネルのメンバーシップに加入している必要があります

## トラブルシューティング

### ダウンロードに失敗する場合

1. URLが正しいか確認
2. メンバーシップ限定動画の場合、cookieを設定し直す
3. アプリを再起動して再試行
