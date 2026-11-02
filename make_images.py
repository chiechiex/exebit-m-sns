# Instagram/Facebook用の画像(1080x1080)をCSVから自動生成
import csv, glob, os
from PIL import Image, ImageDraw, ImageFont
COL = {"食べた方が良い物":("#F59E0B","#B45309"),"食べない方が良い物":("#EF4444","#991B1B"),
       "飲み物":("#14B8A6","#0F766E"),"運動":("#3B82F6","#1E3A8A"),
       "ストレス発散":("#A78BFA","#5B21B6"),"日常気を付ける事":("#22C55E","#166534"),
       "睡眠":("#6366F1","#312E81")}
def font(size):
    for p in os.environ.get("FONT_PATH","").split(",")+glob.glob("/usr/share/fonts/**/NotoSansCJK-Bold.ttc",recursive=True)+glob.glob("/usr/share/fonts/**/*CJK*Bold*",recursive=True):
        if p and os.path.exists(p):
            try: return ImageFont.truetype(p,size,index=0)
            except Exception: pass
    raise SystemExit("日本語フォントが見つかりません (fonts-noto-cjk を入れてください)")
def hexrgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def wrap(d,t,f,maxw):
    lines,cur=[],""
    for ch in t:
        if d.textlength(cur+ch,font=f)>maxw and cur: lines.append(cur);cur=ch
        else: cur+=ch
    return lines+[cur]
def make(date,cat,theme,out):
    c1,c2=map(hexrgb,COL.get(cat,("#64748B","#1E293B")));W=1080
    im=Image.new("RGB",(W,W));px=im.load()
    for y in range(W):
        t=y/W;r=tuple(int(c1[i]*(1-t)+c2[i]*t) for i in range(3))
        for x in range(W): px[x,y]=r
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((80,80,W-80,W-80),40,outline=(255,255,255),width=6)
    fm,fc,ft,fs=font(40),font(64),font(110 if len(theme)<=7 else 88),font(44)
    m,dd=date.split("-")[1:];d.text((W/2,170),f"{int(m)}月{int(dd)}日",font=fm,fill="white",anchor="mm")
    d.rounded_rectangle((200,250,W-200,350),50,fill="white")
    d.text((W/2,300),cat,font=fc if len(cat)<9 else font(54),fill=hexrgb(c2[0:0] or "#000000") if False else c2,anchor="mm")
    lines=wrap(d,theme,ft,W-260);y=540-(len(lines)-1)*70
    for l in lines: d.text((W/2,y),l,font=ft,fill="white",anchor="mm");y+=140
    d.text((W/2,W-170),"EXEBIT-M  健康情報",font=fs,fill="white",anchor="mm")
    im.save(out)
if __name__=="__main__":
    os.makedirs("images",exist_ok=True)
    for r in csv.DictReader(open("schedule.csv",encoding="utf-8-sig")):
        make(r["date"],r["category"],r["theme"],f"images/{r['date']}.png")
    print("images done")
