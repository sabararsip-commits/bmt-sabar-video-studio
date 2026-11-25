#!/usr/bin/env python3
"""Create a 30-second vertical BMT SABAR promotional video."""
import asyncio
import math
import os
import subprocess
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DURATION = 720, 1280, 12, 30
OUT = Path("output")
FRAMES = OUT / "frames"
OUT.mkdir(exist_ok=True)
FRAMES.mkdir(exist_ok=True)

NAVY = (9, 24, 52)
BLUE = (22, 66, 126)
GOLD = (226, 183, 91)
CREAM = (248, 244, 231)
WHITE = (255, 255, 255)
MUTED = (197, 211, 229)

def font(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)

def wrap(draw, text, fnt, max_width):
    words, lines, line = text.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0, 0), test, font=fnt)[2] <= max_width:
            line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
    return lines

def centered_text(draw, text, y, fnt, fill, max_width=610, spacing=18):
    lines = wrap(draw, text, fnt, max_width)
    heights = [draw.textbbox((0,0), line, font=fnt)[3] for line in lines]
    total = sum(heights) + spacing * (len(lines)-1)
    yy = y - total/2
    for line, hh in zip(lines, heights):
        box = draw.textbbox((0,0), line, font=fnt)
        draw.text(((W-(box[2]-box[0]))/2, yy), line, font=fnt, fill=fill)
        yy += hh + spacing

def rounded(draw, box, radius, fill, outline=None, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def scene_for(t):
    if t < 6: return 0
    if t < 12: return 1
    if t < 18: return 2
    if t < 24: return 3
    return 4

def draw_frame(t, idx):
    im = Image.new("RGB", (W,H))
    px = im.load()
    pulse = 0.5 + 0.5*math.sin(t*0.8)
    for y in range(H):
        k = y/H
        col = tuple(int(NAVY[c]*(1-k)+BLUE[c]*k) for c in range(3))
        for x in range(W): px[x,y] = col
    d = ImageDraw.Draw(im, "RGBA")
    # Soft decorative orbital shapes
    for n in range(7):
        x = int(80 + n*105 + 14*math.sin(t*0.7+n))
        y = int(170 + (n%3)*410 + 18*math.cos(t+n))
        r = 28 + int(9*pulse)
        d.ellipse((x-r,y-r,x+r,y+r), outline=(*GOLD,48), width=2)
    d.line((52,110,668,110), fill=(*GOLD,160), width=2)
    d.text((58,65), "BMT SABAR", font=font(28,True), fill=CREAM)
    d.text((505,72), "SYARIAH", font=font(17,True), fill=GOLD)
    s = scene_for(t)
    alpha = min(1.0, (t % 6)/0.65, (6-(t%6))/0.65)
    alpha = max(0.2, alpha)
    gold = tuple(int(v*alpha) for v in GOLD)
    if s == 0:
        centered_text(d, "Rencanakan masa depan", 430, font(49,True), WHITE)
        centered_text(d, "dengan hati yang lebih tenang", 510, font(31), CREAM)
        rounded(d,(150,650,570,820),32,(255,255,255,20),outline=(*GOLD,190),width=3)
        centered_text(d,"DEPOSITO BERHADIAH",710,font(28,True),GOLD)
        centered_text(d,"BMT SABAR",770,font(42,True),WHITE)
    elif s == 1:
        centered_text(d, "Menabung dengan", 405, font(43,True), WHITE)
        centered_text(d, "prinsip syariah", 485, font(53,True), GOLD)
        centered_text(d, "Akad dan nisbah dijelaskan secara transparan.", 630, font(27), CREAM, 590)
        rounded(d,(105,760,615,875),24,(255,255,255,22),outline=(*GOLD,160))
        centered_text(d,"Pahami ketentuan sebelum memilih",817,font(23),WHITE,470)
    elif s == 2:
        centered_text(d, "Hadiah istimewa", 400, font(48,True), WHITE)
        centered_text(d, "untuk rencana berharga", 475, font(34), GOLD)
        # Original gift-box illustration
        d.ellipse((235,690,485,940), fill=(*GOLD,35), outline=(*GOLD,210), width=4)
        rounded(d,(285,720,435,875),18,(226,183,91,235),outline=CREAM,width=3)
        d.rectangle((347,720,373,875),fill=CREAM)
        d.rectangle((285,785,435,812),fill=CREAM)
        d.arc((310,660,365,755),180,350,fill=CREAM,width=12)
        d.arc((355,660,410,755),190,360,fill=CREAM,width=12)
        centered_text(d,"Detail hadiah mengikuti ketentuan program.",1040,font(22),MUTED,590)
    elif s == 3:
        centered_text(d, "Kenali detailnya", 390, font(49,True), WHITE)
        items = ["Jangka waktu deposito", "Nisbah dan mekanisme bagi hasil", "Syarat hadiah dan pencairan"]
        yy = 570
        for item in items:
            rounded(d,(82,yy,638,yy+105),22,(255,255,255,22),outline=(*GOLD,150))
            d.ellipse((108,yy+34,145,yy+71),fill=GOLD)
            d.text((166,yy+31),item,font=font(22,True),fill=WHITE)
            yy += 135
    else:
        centered_text(d, "Saatnya bertanya", 420, font(48,True), WHITE)
        centered_text(d, "dan kenali pilihan syariah", 500, font(32), CREAM)
        rounded(d,(95,665,625,850),28,(226,183,91,245))
        centered_text(d,"DEPOSITO BERHADIAH",730,font(28,True),NAVY)
        centered_text(d,"BMT SABAR",790,font(42,True),NAVY)
        centered_text(d,"Hubungi kantor BMT SABAR untuk informasi resmi",960,font(22),MUTED,590)
    # Bottom timeline and footer
    d.rounded_rectangle((54,1190,666,1198),radius=4,fill=(255,255,255,65))
    d.rounded_rectangle((54,1190,54+int(612*t/DURATION),1198),radius=4,fill=GOLD)
    d.text((55,1220),"Bersama membangun ketenangan finansial",font=font(17),fill=MUTED)
    return im

async def make_voice():
    narration = (
        "Merencanakan masa depan bisa dimulai dengan pilihan yang lebih tenang. "
        "Kenali Deposito Berhadiah BMT SABAR, produk simpanan berjangka dengan prinsip syariah. "
        "Pelajari akad, nisbah, jangka waktu, serta ketentuan hadiah secara terbuka sebelum memutuskan. "
        "Setiap rencana perlu dipahami dengan baik, termasuk syarat pencairan dan ketentuan program. "
        "Ingin tahu lebih lanjut? Hubungi BMT SABAR dan dapatkan informasi resmi. "
        "BMT SABAR. Tumbuh bersama dalam keberkahan."
    )
    communicate = edge_tts.Communicate(narration, "id-ID-ArdiNeural", rate="-4%", volume="+0%")
    await communicate.save(str(OUT / "voice.mp3"))

def main():
    print("Membuat narasi suara pria Indonesia...")
    asyncio.run(make_voice())
    total = FPS * DURATION
    print(f"Menggambar {total} frame video...")
    for i in range(total):
        t = i/FPS
        draw_frame(t, i).save(FRAMES / f"frame_{i:04d}.jpg", quality=88)
    print("Menggabungkan video dan audio dengan FFmpeg...")
    voice = OUT / "voice.mp3"
    cmd = [
        "ffmpeg","-y","-hide_banner","-loglevel","error",
        "-framerate",str(FPS),"-i",str(FRAMES/"frame_%04d.jpg"),
        "-i",str(voice),
        "-f","lavfi","-i","sine=frequency=196:duration=30",
        "-filter_complex",
        "[1:a]volume=1.0,apad=pad_dur=30[vo];[2:a]volume=0.035,lowpass=f=900,afade=t=out:st=26:d=4[bed];[vo][bed]amix=inputs=2:duration=longest, loudnorm=I=-16:TP=-1.5:LRA=11[a]",
        "-map","0:v:0","-map","[a]","-t",str(DURATION),
        "-vf","scale=720:1280,format=yuv420p",
        "-c:v","libx264","-preset","medium","-crf","23",
        "-c:a","aac","-b:a","160k","-movflags","+faststart",
        str(OUT/"BMT_SABAR_Deposito_Berhadiah_30s.mp4")
    ]
    subprocess.run(cmd, check=True)
    print("Selesai: output/BMT_SABAR_Deposito_Berhadiah_30s.mp4")

if __name__ == "__main__":
    main()
