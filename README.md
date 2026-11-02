# SNS自動投稿 (X / Facebookページ / Instagram)

毎朝7:00(JST)に GitHub Actions が起動し、`schedule.csv` の今日分を3つのSNSへ投稿します。
画像(1080x1080)は `make_images.py` で自動生成済み (`images/`)。

## セットアップ
1. GitHubに **公開(Public)リポジトリ** を作り、このフォルダ一式をpush
   (Instagramは公開URLの画像が必要なため。画像と投稿文に秘密情報は含まれません。キーはSecretsに入れます)
2. Settings > Secrets and variables > Actions に登録:
   - X: `X_API_KEY` `X_API_SECRET` `X_ACCESS_TOKEN` `X_ACCESS_SECRET` (Read and Write権限)
   - Meta: `FB_PAGE_ID` `FB_PAGE_TOKEN` (長期ページアクセストークン) `IG_USER_ID` (InstagramビジネスのユーザーID)
   - Metaの権限: pages_manage_posts, pages_read_engagement, instagram_basic, instagram_content_publish
3. Actions > daily-post > Run workflow で `dry_run=1` を実行し、内容を確認
4. 1つのSNSだけで試す場合は Variables ではなく workflow の env に `PLATFORMS: x` などを追加

## 運用
- 文面修正は `schedule.csv` を直接編集 (Excelで開く場合は UTF-8 のまま保存)
- 途中のSNSだけ失敗した場合、次回実行で失敗分のみ再投稿 (重複しません)
- 来月分: `build_schedule.py` のデータを差し替えて実行 → `python make_images.py`
- Xは280字(日本語約140字)を超えると末尾のハッシュタグから自動で削ります
- Instagramには共通ハッシュタグ(`IG_EXTRA_TAGS`)を自動追加します

## ローカルテスト
    TODAY=2026-11-02 DRY_RUN=1 python post.py
