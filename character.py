"""Lightweight sprite performance and a procedural cozy night-room stage."""
import math
import random
import time
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
from core import MOODS, OUTFITS, resource

# Mouth landmarks are in the original atlas, not in screen coordinates.
MOUTHS = {
    "morning": [(234, 80), (565, 78), (888, 80), (210, 564), (555, 567), (883, 567), (224, 1052), (566, 1042), (894, 1040)],
    "afternoon": [(227, 83), (548, 80), (863, 84), (223, 555), (541, 560), (893, 565), (235, 1035), (588, 1068), (901, 1061)],
    "evening": [(240, 81), (562, 82), (896, 92), (223, 564), (559, 578), (907, 568), (221, 1050), (559, 1052), (893, 1045)],
    "night": [(233, 83), (558, 83), (885, 90), (222, 568), (559, 560), (883, 578), (226, 1060), (572, 1120), (891, 1055)]}
NO_FACE_ANIMATION = {"tea", "yawn", "thinking", "laughing", "smirk", "pensive", "crying", "self_hug", "peaceful", "sleepy"}


def make_room(width, height):
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / height
        draw.line((0, y, width, y), fill=(int(25 + 19 * ratio), int(20 + 10 * ratio), int(49 + 12 * ratio)))
    window = (int(width * .08), 42, int(width * .91), int(height * .77))
    draw.rounded_rectangle(window, radius=25, fill=(20, 23, 55), outline=(91, 75, 132), width=2)
    rng = random.Random(26)
    for _ in range(70):
        x, y = rng.randint(window[0] + 10, window[2] - 10), rng.randint(50, int(height * .45))
        draw.ellipse((x, y, x + 2, y + 2), fill=(150, 137, 202))
    moon_x, moon_y = int(width * .21), int(height * .16)
    draw.ellipse((moon_x-24, moon_y-24, moon_x+24, moon_y+24), fill=(218, 201, 241))
    draw.ellipse((moon_x-8, moon_y-28, moon_x+27, moon_y+14), fill=(20, 23, 55))
    horizon = int(height * .66)
    for x in range(window[0]+10, window[2]-10, 28):
        top = horizon - rng.randint(30, 135)
        draw.rectangle((x, top, x+22, horizon), fill=(39, 30, 69))
        for yy in range(top+8, horizon, 13):
            for xx in (x+4, x+13):
                if rng.random() > .35:
                    draw.rectangle((xx, yy, xx+3, yy+5), fill=rng.choice([(164, 124, 199), (234, 172, 125), (95, 133, 183)]))
    for x in (int(width*.35), int(width*.65)):
        draw.line((x, 44, x, window[3]), fill=(69, 51, 100), width=8)
    draw.line((window[0], int(height*.46), window[2], int(height*.46)), fill=(69, 51, 100), width=6)
    floor = int(height * .81)
    draw.rectangle((0, floor, width, height), fill=(33, 26, 49))
    draw.ellipse((int(width*.17), height-71, int(width*.83), height-17), fill=(49, 37, 69))
    # Warm lamp and a small plant give the room a calm, lived-in feel.
    draw.line((width-44, floor-100, width-44, floor+6), fill=(123, 87, 89), width=4)
    draw.polygon([(width-68, floor-100), (width-20, floor-100), (width-29, floor-143), (width-59, floor-143)], fill=(234, 169, 120))
    draw.rectangle((21, floor-11, 65, floor+28), fill=(83, 61, 86))
    for i in range(4):
        yy = floor-25-i*23
        draw.line((43, floor, 43, yy), fill=(63, 105, 92), width=3)
        draw.ellipse((17, yy-10, 44, yy+6), fill=(72, 113, 99))
        draw.ellipse((43, yy-19, 72, yy-3), fill=(85, 127, 106))
    return image


class Stage(tk.Canvas):
    def __init__(self, parent, audio, settings, **kwargs):
        super().__init__(parent, bg="#191431", highlightthickness=0, **kwargs)
        self.audio, self.settings = audio, settings
        self.mood = "smile"
        self.cache = {}
        self.frame_cache = None
        self.background = None
        self.last_size = None
        self.next_blink = time.monotonic() + 3.2
        self.blink_until = 0.0
        self.closed = False
        self.photo = None
        self.item = self.create_image(0, 0, anchor="nw")
        self.bind("<Configure>", lambda e: self.invalidate())
        self.after(100, self.animate)

    def invalidate(self):
        self.frame_cache = None

    def set_mood(self, mood):
        if mood in MOODS:
            self.mood = mood
            self.invalidate()

    def sprite(self):
        index = MOODS.index(self.mood)
        outfit, tile = OUTFITS[index // 9], index % 9
        if self.mood not in self.cache:
            with Image.open(resource("assets/" + outfit + ".png")) as sheet:
                w, h = sheet.size
                col, row = tile % 3, tile // 3
                left, top = round(col*w/3), round(row*h/3)
                sprite = sheet.crop((left, top, round((col+1)*w/3), round((row+1)*h/3))).convert("RGBA")
            self.cache[self.mood] = (sprite, (MOUTHS[outfit][tile][0]-left, MOUTHS[outfit][tile][1]-top))
        return self.cache[self.mood]

    def render_frame(self, width, height, now=None):
        now = time.monotonic() if now is None else now
        if self.last_size != (width, height):
            self.background = make_room(width, height)
            self.last_size = (width, height)
            self.invalidate()
        source, mouth = self.sprite()
        if self.frame_cache is None:
            ratio = min((width-40)/source.width, (height-34)/source.height)
            image = source.resize((round(source.width*ratio), round(source.height*ratio)), Image.Resampling.LANCZOS)
            self.frame_cache = (image, (round(mouth[0]*ratio), round(mouth[1]*ratio)), ratio)
        sprite, mouth, scale = self.frame_cache
        sprite = sprite.copy()
        motion = self.settings.get("motion", True)
        if motion and self.mood not in NO_FACE_ANIMATION:
            draw = ImageDraw.Draw(sprite)
            mx, my = mouth
            # Small software facial motion; these sprites are not a Live2D rig.
            if now < self.blink_until:
                for ex in (mx-11*scale, mx+10*scale):
                    ey = my-19*scale
                    skin = sprite.getpixel((max(0,min(sprite.width-1,int(ex))), max(0,min(sprite.height-1,int(ey+7*scale)))))
                    if skin[3] and skin[0] > 120:
                        draw.ellipse((ex-6*scale,ey-4*scale,ex+6*scale,ey+4*scale),fill=skin)
                        draw.arc((ex-6*scale,ey-3*scale,ex+6*scale,ey+3*scale),0,180,fill=(74,44,67,255),width=max(1,round(scale)))
            if self.audio.playing and self.audio.level > .035:
                opening = (1.6 + min(1,self.audio.level)*4.5)*scale
                draw.ellipse((mx-4.2*scale, my-opening, mx+4.2*scale, my+opening), fill=(91,39,60,255))
                draw.ellipse((mx-2.7*scale,my+.5*scale,mx+2.7*scale,my+opening*.8), fill=(194,105,129,255))
        frame = self.background.copy().convert("RGBA")
        bob = round(math.sin(now*1.5)*2.0) if motion else 0
        sway = round(math.sin(now*.75)*1.2) if motion else 0
        x, y = (width-sprite.width)//2+sway, height-sprite.height-17+bob
        frame.alpha_composite(sprite,(x,y))
        return frame.convert("RGB")

    def animate(self):
        if self.closed:
            return
        now = time.monotonic()
        if now > self.next_blink:
            self.blink_until = now+.15
            self.next_blink = now+random.uniform(3.0,5.5)
        width,height = max(200,self.winfo_width()),max(300,self.winfo_height())
        self.photo = ImageTk.PhotoImage(self.render_frame(width,height,now))
        self.itemconfigure(self.item,image=self.photo)
        self.after(round(1000/self.settings.get("fps",16)),self.animate)
