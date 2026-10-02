"""Vidu jobs and private local motion cache. Generations only start on a click."""
import base64
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
from PIL import Image
from core import ApiError, MOODS, OUTFITS
from providers import request, decode_json, identifier
from actions import public_https


def stage_image(path):
    with Image.open(path) as source:
        source=source.convert("RGBA")
        source.thumbnail((720,1280),Image.Resampling.LANCZOS)
        image=Image.new("RGB",(720,1280),(24,23,43))
        image.paste(source,((720-source.width)//2,(1280-source.height)//2),source)
        output=io.BytesIO(); image.save(output,"PNG")
    return "data:image/png;base64,"+base64.b64encode(output.getvalue()).decode()


def motion_prompt(mood):
    gestures={"kiss":"blows one gentle flying kiss with her hand", "commanding":"confidently points forward then puts a hand on her hip", "angry":"folds her arms with playful mock anger", "sitting":"sits calmly and gently moves her hands", "tea":"holds her tea cup and brings it near her lips", "wave":"gently waves hello", "crying":"wipes a tear gently", "sad":"looks down softly then toward the viewer"}
    return "A clearly adult anime woman, same identity, face, hair and clothes as image. "+gestures.get(mood,"shows a subtle "+mood.replace("_"," ")+" expression")+". Gentle natural breathing, occasional blinks, small hair motion. Smooth coherent anatomy, detailed crisp anime artwork. Locked camera and background, no zoom or cuts, no text, no extra people. Return to starting pose for a seamless short loop."


class ViduClient:
    def __init__(self,key,settings): self.key,self.settings=key,dict(settings)

    def submit(self,image,mood):
        model=identifier(self.settings["vidu_model"],"Vidu model")
        response=decode_json(request("Vidu","https://api.vidu.com/ent/v2/img2video",self.key,
            {"model":model,"images":[stage_image(image)],"prompt":motion_prompt(mood),"duration":4,"resolution":"1080p","audio":False,"bgm":False,"is_rec":False}),"Vidu")
        return identifier(str(response.get("task_id","")),"Vidu task ID")

    def result(self,task_id):
        task_id=identifier(task_id,"Vidu task ID")
        return decode_json(request("Vidu",f"https://api.vidu.com/ent/v2/tasks/{task_id}/creations",self.key),"Vidu")


class MotionCache:
    def __init__(self,directory):
        self.directory=Path(directory)/"motion"; self.directory.mkdir(exist_ok=True)
        self.manifest=self.directory/"clips.json"
        try: self.clips=json.loads(self.manifest.read_text())
        except (OSError,ValueError): self.clips={}

    def get(self,outfit,mood):
        value=self.clips.get(outfit+":"+mood,"")
        path=self.directory/value
        return path if value and path.is_file() and path.resolve().parent==self.directory.resolve() else None

    def import_clip(self,source,outfit,mood):
        if outfit not in OUTFITS or mood not in MOODS: raise ValueError("Invalid clip selection.")
        source=Path(source)
        if source.suffix.lower() not in (".mp4",".webm") or source.stat().st_size>500_000_000:
            raise ValueError("Choose an MP4 or WebM under 500 MB.")
        target=self.directory/(outfit+"-"+mood+source.suffix.lower())
        if source.resolve()!=target.resolve():
            with source.open("rb") as read,target.open("wb") as write:
                while block:=read.read(1024*1024): write.write(block)
        self.clips[outfit+":"+mood]=target.name
        self.manifest.write_text(json.dumps(self.clips,indent=2))
        return target

    def download(self,url,outfit,mood):
        public_https(url)
        temp=self.directory/"download.part"
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"LISA-Companion"})
            with urllib.request.urlopen(req,timeout=60) as response,temp.open("wb") as writer:
                public_https(response.geturl())
                size=0
                while block:=response.read(1024*1024):
                    size+=len(block)
                    if size>500_000_000: raise ApiError("The generated video exceeded 500 MB.")
                    writer.write(block)
            if size<32: raise ApiError("The generated video is incomplete.")
            with temp.open("rb") as header:data=header.read(32)
            if b"ftyp" not in data: raise ApiError("Vidu returned an unsupported video format.")
            video=self.directory/"download.mp4";temp.replace(video)
            return self.import_clip(video,outfit,mood)
        finally:
            temp.unlink(missing_ok=True)
