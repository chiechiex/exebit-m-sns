"""毎日実行: schedule.csv の「今日(JST)以前で未投稿」の行を X / Facebook / Instagram に投稿する。
各SNSごとに完了フラグを持つので、一部が失敗しても再実行で重複投稿しません。"""
import csv, os, re, sys, time, datetime, zoneinfo
import requests

JST = zoneinfo.ZoneInfo("Asia/Tokyo")
CSV = "schedule.csv"
GRAPH = f"https://graph.facebook.com/{os.environ.get('GRAPH_VERSION','v23.0')}"
DRY = os.environ.get("DRY_RUN") == "1"
PLATFORMS = [p.strip() for p in os.environ.get("PLATFORMS", "x,facebook,instagram").split(",") if p.strip()]
IG_EXTRA_TAGS = os.environ.get("IG_EXTRA_TAGS", "#健康 #健康習慣 #ヘルスケア #ウェルネス #セルフケア #暮らし #丁寧な暮らし")
FIELD = {"x": "x_done", "facebook": "fb_done", "instagram": "ig_done"}

def today():
    return os.environ.get("TODAY") or datetime.datetime.now(JST).strftime("%Y-%m-%d")

def x_weight(s):  # Xの文字数: 日本語・絵文字は2、半角は1、上限280
    return sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2 for c in s)

def x_text(text):
    body = re.split(r"\s(?=#)", text, maxsplit=1)
    msg, tags = body[0], (body[1].split() if len(body) > 1 else [])
    while tags and x_weight(msg + "\n\n" + " ".join(tags)) > 280:
        tags.pop()  # 長ければ末尾のハッシュタグから削る
    out = msg + ("\n\n" + " ".join(tags) if tags else "")
    while x_weight(out) > 280:
        msg = msg[:-2] + "…"; out = msg
    return out

def post_x(text, img):
    import tweepy
    c = tweepy.Client(consumer_key=os.environ["X_API_KEY"], consumer_secret=os.environ["X_API_SECRET"],
                      access_token=os.environ["X_ACCESS_TOKEN"], access_token_secret=os.environ["X_ACCESS_SECRET"])
    c.create_tweet(text=x_text(text))

def check(r):
    if not r.ok:
        raise RuntimeError(f"{r.status_code} {r.text[:300]}")
    return r.json()

def post_facebook(text, img):
    with open(img, "rb") as f:
        check(requests.post(f"{GRAPH}/{os.environ['FB_PAGE_ID']}/photos",
              data={"caption": text, "access_token": os.environ["FB_PAGE_TOKEN"]}, files={"source": f}, timeout=60))

def post_instagram(text, img):
    url = os.environ["IMAGE_BASE_URL"].rstrip("/") + "/" + os.path.basename(img)
    cap = text + "\n\n" + IG_EXTRA_TAGS
    tok = os.environ["FB_PAGE_TOKEN"]; uid = os.environ["IG_USER_ID"]
    cid = check(requests.post(f"{GRAPH}/{uid}/media", data={"image_url": url, "caption": cap, "access_token": tok}, timeout=60))["id"]
    for _ in range(12):  # コンテナ準備完了を待つ
        st = check(requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code", "access_token": tok}, timeout=30))
        if st.get("status_code") == "FINISHED": break
        if st.get("status_code") == "ERROR": raise RuntimeError("Instagramが画像を処理できませんでした(URL到達可否を確認)")
        time.sleep(5)
    check(requests.post(f"{GRAPH}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60))

SENDERS = {"x": post_x, "facebook": post_facebook, "instagram": post_instagram}

def main():
    with open(CSV, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f)); cols = rows[0].keys()
    t, failed = today(), False
    for r in rows:
        if r["date"] > t: continue
        todo = [p for p in PLATFORMS if not r[FIELD[p]]]
        if not todo: continue
        img = f"images/{r['date']}.png"
        for p in todo:
            try:
                if DRY:
                    print(f"[DRY] {r['date']} -> {p}\n{x_text(r['text']) if p=='x' else r['text']}\n")
                else:
                    SENDERS[p](r["text"], img)
                    r[FIELD[p]] = datetime.datetime.now(JST).strftime("%Y-%m-%d %H:%M")
                    print(f"OK {r['date']} {p}")
            except Exception as e:
                failed = True; print(f"NG {r['date']} {p}: {e}", file=sys.stderr)
        # 取りこぼし救済はするが、1回の実行で投稿するのは1日分だけ(連投防止)
        break
    if not DRY:
        with open(CSV, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    sys.exit(1 if failed else 0)

if __name__ == "__main__":
    main()
