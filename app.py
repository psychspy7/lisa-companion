"""LISA: a standalone Windows companion app. Run app.py or packaged LISA.exe."""
from __future__ import annotations
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from audio import Audio
from character import Stage
from core import Credentials, Store, MOODS, LABELS, OUTFITS, VERSION, outfit_for_hour, parse_repo, resource
from providers import GeminiClient, ElevenLabsClient
import updates
import demo

BG="#141020"
PANEL="#211a32"
SOFT="#2e2341"
FG="#f2eafa"
MUTED="#b5a5cc"
ACCENT="#bd96ef"


def button(parent,text,command,primary=False,**kwargs):
    return tk.Button(parent,text=text,command=command,bg=ACCENT if primary else SOFT,fg="#241534" if primary else FG,
                     activebackground="#d0b2f4",activeforeground="#251633",relief="flat",borderwidth=0,
                     font=("Segoe UI",10,"bold"),cursor="hand2",padx=13,pady=8,**kwargs)


class LisaApp(tk.Tk):
    def __init__(self,test_mode=False):
        super().__init__()
        self.test_mode=test_mode
        self.title("LISA • Your little universe")
        self.iconbitmap(str(resource("assets/lisa.ico")))
        self.geometry("1190x790")
        self.minsize(920,650)
        self.configure(bg=BG)
        self.store=Store()
        self.credentials=Credentials(self.store.directory,"gemini")
        self.voice_credentials=Credentials(self.store.directory,"elevenlabs")
        if test_mode:
            self.store.settings.update(demo_enabled=True,voice_enabled=False,sound_enabled=False)
        self.audio=Audio()
        self.events=queue.Queue()
        self.ticket=0
        self.busy=False
        self.closing=False
        self.update_info=None
        self.record_started=None
        self.last_reply=""
        self.cancel_speech=threading.Event()
        self.last_period=outfit_for_hour(datetime.now().hour)
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW",self.close)
        self.bind("<Escape>",lambda e:self.interrupt())
        self.apply_outfit()
        self.add_chat("Lisa","Hi, Sir. Welcome to our little corner of the universe. What’s on your mind?")
        if self.store.history:
            self.add_chat("System","Your saved conversation is available as context. Use Clear chat to start fresh.")
        self.status.set("Free demo • preset replies • microphone off" if self.demo_var.get() else ("Gemini ready • microphone off" if self.credentials.get() else "Ready • add your Gemini key in Settings"))
        self.after(80,self.poll)

    def build_ui(self):
        top=tk.Frame(self,bg=BG)
        top.pack(fill="x",padx=24,pady=(16,12))
        tk.Label(top,text="LISA",bg=BG,fg=FG,font=("Segoe UI",25,"bold")).pack(side="left")
        tk.Label(top,text="  YOUR LITTLE UNIVERSE",bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(side="left",padx=10)
        button(top,"Settings",self.settings_dialog).pack(side="right",padx=(8,0))
        self.update_button=button(top,"Check for updates",self.check_update)
        self.update_button.pack(side="right")
        body=tk.Frame(self,bg=BG)
        body.pack(fill="both",expand=True,padx=24,pady=(0,16))
        body.grid_columnconfigure(0,weight=12)
        body.grid_columnconfigure(1,weight=10)
        body.grid_rowconfigure(0,weight=1)
        left=tk.Frame(body,bg=PANEL)
        left.grid(row=0,column=0,sticky="nsew",padx=(0,16))
        left.grid_columnconfigure(0,weight=1)
        left.grid_rowconfigure(1,weight=1)
        stage_head=tk.Frame(left,bg=PANEL)
        stage_head.grid(row=0,column=0,sticky="ew",padx=16,pady=12)
        self.pose_label=tk.StringVar(value="Morning • Smile")
        tk.Label(stage_head,text="●  LISA",bg=PANEL,fg=ACCENT,font=("Segoe UI",10,"bold")).pack(side="left")
        tk.Label(stage_head,textvariable=self.pose_label,bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(side="right")
        self.stage=Stage(left,self.audio,self.store.settings,width=560,height=540)
        self.stage.grid(row=1,column=0,sticky="nsew")
        look=tk.Frame(left,bg=PANEL)
        look.grid(row=2,column=0,sticky="ew",padx=12,pady=(10,5))
        tk.Label(look,text="OUTFIT",bg=PANEL,fg=MUTED,font=("Segoe UI",8,"bold")).pack(side="left",padx=(0,8))
        self.outfit_var=tk.StringVar(value=self.store.settings["outfit"].title())
        outfit_box=ttk.Combobox(look,textvariable=self.outfit_var,values=[x.title() for x in OUTFITS],state="readonly",width=12)
        outfit_box.pack(side="left")
        outfit_box.bind("<<ComboboxSelected>>",lambda e:self.choose_outfit())
        self.auto_var=tk.BooleanVar(value=self.store.settings["auto_outfit"])
        tk.Checkbutton(look,text="By time of day",variable=self.auto_var,command=self.toggle_auto,bg=PANEL,fg=MUTED,
                       selectcolor=SOFT,activebackground=PANEL,activeforeground=FG,font=("Segoe UI",9)).pack(side="left",padx=6)
        button(look,"36 poses",self.gallery).pack(side="right")
        reactions=tk.Frame(left,bg=PANEL)
        reactions.grid(row=3,column=0,sticky="ew",padx=12,pady=(4,12))
        for title,mood in [("Smile","smile"),("Sit","sitting"),("Kiss","kiss"),("Angry","angry"),("Command","commanding")]:
            button(reactions,title,lambda m=mood:self.perform(m)).pack(side="left",expand=True,fill="x",padx=2)
        right=tk.Frame(body,bg=PANEL)
        right.grid(row=0,column=1,sticky="nsew")
        right.grid_columnconfigure(0,weight=1)
        right.grid_rowconfigure(2,weight=1)
        tk.Label(right,text="Spend a little time with me",bg=PANEL,fg=FG,font=("Segoe UI",17,"bold"),anchor="w").grid(row=0,column=0,sticky="ew",padx=18,pady=(18,3))
        tk.Label(right,text="English · Hindi · Hinglish",bg=PANEL,fg=MUTED,font=("Segoe UI",10),anchor="w").grid(row=1,column=0,sticky="ew",padx=18,pady=(0,12))
        chat_frame=tk.Frame(right,bg=PANEL)
        chat_frame.grid(row=2,column=0,sticky="nsew",padx=18)
        chat_frame.grid_rowconfigure(0,weight=1)
        chat_frame.grid_columnconfigure(0,weight=1)
        self.chat=tk.Text(chat_frame,bg=PANEL,fg=FG,font=("Segoe UI",11),wrap="word",relief="flat",borderwidth=0,
                          padx=0,pady=5,spacing1=5,spacing3=12,state="disabled",width=40)
        self.chat.grid(row=0,column=0,sticky="nsew")
        scrollbar=ttk.Scrollbar(chat_frame,command=self.chat.yview)
        scrollbar.grid(row=0,column=1,sticky="ns")
        self.chat.configure(yscrollcommand=scrollbar.set)
        self.chat.tag_configure("Lisa",foreground=ACCENT,font=("Segoe UI",10,"bold"))
        self.chat.tag_configure("Lisa · demo",foreground=ACCENT,font=("Segoe UI",10,"bold"))
        self.chat.tag_configure("You",foreground="#a2c9f0",font=("Segoe UI",10,"bold"))
        self.chat.tag_configure("System",foreground=MUTED,font=("Segoe UI",9))
        self.status=tk.StringVar(value="Ready")
        tk.Label(right,textvariable=self.status,bg=PANEL,fg=MUTED,font=("Segoe UI",9),anchor="w",wraplength=400).grid(row=3,column=0,sticky="ew",padx=18,pady=(6,8))
        self.input=tk.Text(right,height=3,bg=SOFT,fg=FG,insertbackground=FG,font=("Segoe UI",11),wrap="word",relief="flat",padx=12,pady=9)
        self.input.grid(row=4,column=0,sticky="ew",padx=18)
        self.input.bind("<Return>",self.enter_send)
        self.input.bind("<Shift-Return>",lambda e:None)
        controls=tk.Frame(right,bg=PANEL)
        controls.grid(row=5,column=0,sticky="ew",padx=18,pady=10)
        self.mic_button=button(controls,"Talk",self.toggle_recording)
        self.mic_button.pack(side="left")
        button(controls,"Stop",self.interrupt).pack(side="left",padx=6)
        self.send_button=button(controls,"Send",self.send,True)
        self.send_button.pack(side="right")
        bottom=tk.Frame(right,bg=PANEL)
        bottom.grid(row=6,column=0,sticky="ew",padx=18,pady=(0,8))
        self.voice_var=tk.BooleanVar(value=self.store.settings["voice_enabled"])
        tk.Checkbutton(bottom,text="Lisa’s voice",variable=self.voice_var,command=self.toggle_voice,bg=PANEL,fg=MUTED,
                       selectcolor=SOFT,activebackground=PANEL,activeforeground=FG,font=("Segoe UI",9)).pack(side="left")
        button(bottom,"Memory",self.memory_dialog).pack(side="right")
        button(bottom,"Clear chat",self.clear_chat).pack(side="right",padx=5)
        self.demo_var=tk.BooleanVar(value=self.store.settings["demo_enabled"])
        tk.Checkbutton(right,text="Free demo · preset replies + Windows voice",variable=self.demo_var,command=self.toggle_demo,bg=PANEL,fg=MUTED,selectcolor=SOFT,activebackground=PANEL,activeforeground=FG,font=("Segoe UI",9)).grid(row=7,column=0,sticky="w",padx=14)
        tk.Label(right,text="Gemini chat · ElevenLabs AI voice · Mic off until Talk",bg=PANEL,fg="#89799d",font=("Segoe UI",8),anchor="w").grid(row=8,column=0,sticky="ew",padx=18,pady=(0,13))

    def add_chat(self,who,text):
        self.chat.configure(state="normal")
        self.chat.insert("end",who.upper()+"\n",who)
        self.chat.insert("end",text+"\n\n")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def enter_send(self,event):
        if event.state & 1:
            return None
        self.send()
        return "break"

    def choose_outfit(self):
        self.auto_var.set(False)
        self.store.settings["auto_outfit"]=False
        self.store.settings["outfit"]=self.outfit_var.get().lower()
        self.apply_outfit()
        self.store.save()

    def toggle_auto(self):
        self.store.settings["auto_outfit"]=self.auto_var.get()
        self.apply_outfit()
        self.store.save()

    def apply_outfit(self):
        outfit=outfit_for_hour(datetime.now().hour) if self.store.settings["auto_outfit"] else self.store.settings["outfit"]
        self.outfit_var.set(outfit.title())
        self.perform({"morning":"smile","afternoon":"proud","evening":"affectionate","night":"goodnight"}[outfit],sound=False)

    def perform(self,mood,sound=True):
        self.stage.set_mood(mood)
        outfit=OUTFITS[MOODS.index(mood)//9]
        self.pose_label.set(outfit.title()+" • "+LABELS[mood])
        self.outfit_var.set(outfit.title())
        if sound and self.store.settings["sound_enabled"] and not self.test_mode:
            cached=self.store.directory/"chime.wav"
            if self.store.settings["custom_chime"] and cached.exists() and not self.audio.playing and not self.audio.recording:
                try:
                    self.audio.play_wav(cached.read_bytes(),0.3)
                except Exception:
                    self.audio.chime()
            else:
                self.audio.chime()

    def toggle_voice(self):
        self.store.settings["voice_enabled"]=self.voice_var.get()
        if not self.voice_var.get():
            self.interrupt()
        self.store.save()

    def toggle_demo(self):
        self.interrupt()
        self.store.settings["demo_enabled"]=self.demo_var.get()
        self.store.save()
        self.status.set("Free demo • preset replies • microphone off" if self.demo_var.get() else "Gemini + ElevenLabs • microphone off")

    def send(self):
        text=self.input.get("1.0","end").strip()
        if not text or self.busy:
            return
        if not self.demo_var.get() and not self.credentials.get():
            self.status.set("Add a Gemini key in Settings first.")
            self.settings_dialog()
            return
        self.interrupt()
        self.ticket+=1
        ticket=self.ticket
        self.input.delete("1.0","end")
        self.add_chat("You",text)
        history=list(self.store.history)
        self.store.history.append({"role":"user","content":text})
        self.store.save()
        self.busy=True
        self.send_button.configure(state="disabled")
        self.status.set("Lisa is thinking…")
        self.perform("thinking",False)
        if self.demo_var.get():
            self.worker("reply",ticket,lambda:demo.reply(text,list(self.store.memories)))
        else:
            client=GeminiClient(self.credentials.get(),self.store.settings)
            self.worker("reply",ticket,lambda:client.chat(text,history,list(self.store.memories)))

    def worker(self,kind,ticket,call):
        def run():
            try:
                result=call()
                self.events.put((kind,ticket,result))
            except Exception as exc:
                self.events.put(("error",ticket,str(exc)))
        threading.Thread(target=run,daemon=True).start()

    def poll(self):
        if self.closing:
            return
        while True:
            try:
                kind,ticket,result=self.events.get_nowait()
            except queue.Empty:
                break
            if kind.startswith("update"):
                self.handle_update(kind,result)
                continue
            if ticket!=self.ticket:
                continue
            if kind=="reply":
                self.busy=False
                self.send_button.configure(state="normal")
                self.last_reply=result["reply"]
                self.add_chat("Lisa · demo" if self.demo_var.get() else "Lisa",result["reply"])
                self.store.history.append({"role":"assistant","content":result["reply"]})
                self.store.save()
                self.perform(result["mood"],False)
                self.status.set("Ready • microphone off")
                if self.store.settings["voice_enabled"]:
                    self.status.set("Preparing Lisa’s voice…")
                    if self.demo_var.get():
                        self.worker("speech",ticket,lambda text=result["reply"], cancel=self.cancel_speech:demo.speech(text,self.store.directory,cancel))
                    else:
                        if not self.voice_credentials.get() or not self.store.settings["eleven_voice_id"]:
                            self.status.set("Reply ready • add ElevenLabs key and choose a voice in Settings to hear Lisa")
                        else:
                            client=ElevenLabsClient(self.voice_credentials.get(),self.store.settings)
                            self.worker("speech",ticket,lambda c=client, text=result["reply"], mood=result["mood"]:c.speech(text,mood))
            elif kind=="speech":
                try:
                    self.audio.play_wav(result,self.store.settings["volume"])
                    self.status.set("Lisa is speaking • Stop or Talk to interrupt")
                except Exception as exc:
                    self.status.set(str(exc))
            elif kind=="transcript":
                self.busy=False
                self.send_button.configure(state="normal")
                if result:
                    self.input.delete("1.0","end")
                    self.input.insert("1.0",result)
                    self.send()
                else:
                    self.status.set("No speech detected. Try again, Sir.")
            elif kind=="error":
                self.busy=False
                self.send_button.configure(state="normal")
                self.status.set(result)
                self.add_chat("System",result)
        if self.audio.recording and self.audio.frames>=16000*30:
            self.toggle_recording()
        if self.status.get().startswith("Lisa is speaking") and not self.audio.playing:
            self.status.set("Ready • microphone off")
        period=outfit_for_hour(datetime.now().hour)
        if period!=self.last_period:
            self.last_period=period
            if self.store.settings["auto_outfit"]:
                self.apply_outfit()
        self.after(80,self.poll)

    def interrupt(self):
        self.ticket+=1
        self.cancel_speech.set()
        demo.cancel()
        self.cancel_speech=threading.Event()
        self.busy=False
        self.audio.stop_playback()
        if self.audio.recording:
            self.audio.stop_recording()
        self.mic_button.configure(text="Talk",bg=SOFT,fg=FG)
        self.send_button.configure(state="normal")
        self.status.set("Ready • microphone off")

    def toggle_recording(self):
        if self.audio.recording:
            wav=self.audio.stop_recording()
            self.mic_button.configure(text="Talk",bg=SOFT,fg=FG)
            self.status.set("Microphone off • transcribing…")
            if len(wav)<8044:
                self.status.set("That was very short. Try a longer phrase.")
                return
            self.busy=True
            self.send_button.configure(state="disabled")
            client=ElevenLabsClient(self.voice_credentials.get(),self.store.settings)
            self.worker("transcript",self.ticket,lambda:client.transcribe(wav))
        else:
            if self.demo_var.get():
                self.status.set("Voice input uses ElevenLabs. Save your keys in Settings and switch off Free demo first.")
                return
            if not self.credentials.get() or not self.voice_credentials.get():
                self.status.set("Add Gemini and ElevenLabs keys before using voice chat.")
                self.settings_dialog()
                return
            self.interrupt()
            try:
                self.audio.start_recording()
                self.mic_button.configure(text="Finish talking",bg="#a3d7c8",fg="#142d26")
                self.status.set("Microphone ON • press Finish talking (30-second limit)")
                self.perform("listening",False)
            except Exception as exc:
                self.status.set(str(exc))

    def clear_chat(self):
        self.interrupt()
        self.store.history=[]
        self.store.save()
        self.chat.configure(state="normal")
        self.chat.delete("1.0","end")
        self.chat.configure(state="disabled")
        self.add_chat("Lisa","A fresh start, Sir. I’m listening.")

    def popup(self,title,size="580x600"):
        popup=tk.Toplevel(self)
        popup.title(title)
        popup.geometry(size)
        popup.configure(bg=PANEL)
        popup.transient(self)
        return popup

    def gallery(self):
        dialog=self.popup("Lisa • 36 illustrated poses","690x550")
        tk.Label(dialog,text="Choose a mood",bg=PANEL,fg=FG,font=("Segoe UI",20,"bold")).pack(anchor="w",padx=22,pady=(20,3))
        tk.Label(dialog,text="Each pose uses its coordinated outfit. Motion and voice work on top of the illustration.",bg=PANEL,fg=MUTED,font=("Segoe UI",9),wraplength=650).pack(anchor="w",padx=22,pady=(0,15))
        tabs=ttk.Notebook(dialog)
        tabs.pack(fill="both",expand=True,padx=22,pady=(0,20))
        for group,outfit in enumerate(OUTFITS):
            page=tk.Frame(tabs,bg=PANEL)
            tabs.add(page,text=outfit.title())
            for col in range(3):
                page.grid_columnconfigure(col,weight=1)
            for i,mood in enumerate(MOODS[group*9:group*9+9]):
                button(page,LABELS[mood],lambda m=mood:self.perform(m)).grid(row=i//3,column=i%3,sticky="nsew",padx=8,pady=14,ipady=22)

    def memory_dialog(self):
        dialog=self.popup("Lisa • Things you choose to save","580x530")
        tk.Label(dialog,text="What should I remember, Sir?",bg=PANEL,fg=FG,font=("Segoe UI",17,"bold")).pack(anchor="w",padx=20,pady=(20,5))
        tk.Label(dialog,text="Only these notes become long-term memory. You can remove them any time.",bg=PANEL,fg=MUTED,font=("Segoe UI",9),wraplength=540).pack(anchor="w",padx=20,pady=(0,10))
        notes=tk.Listbox(dialog,bg=SOFT,fg=FG,font=("Segoe UI",10),selectbackground=ACCENT,selectforeground=BG,relief="flat",height=10)
        notes.pack(fill="both",expand=True,padx=20)
        for note in self.store.memories:
            notes.insert("end",note)
        entry=tk.Text(dialog,height=3,bg=SOFT,fg=FG,insertbackground=FG,font=("Segoe UI",10),relief="flat",padx=8,pady=8)
        entry.pack(fill="x",padx=20,pady=12)
        row=tk.Frame(dialog,bg=PANEL)
        row.pack(fill="x",padx=20,pady=(0,20))
        def add():
            note=entry.get("1.0","end").strip()
            if note:
                self.store.add_memory(note)
                notes.delete(0,"end")
                for item in self.store.memories:
                    notes.insert("end",item)
                entry.delete("1.0","end")
        def remove():
            selection=notes.curselection()
            if selection:
                del self.store.memories[selection[0]]
                notes.delete(selection[0])
                self.store.save()
        button(row,"Remove selected",remove).pack(side="left")
        button(row,"Save note",add,True).pack(side="right")

    def settings_dialog(self):
        dialog=self.popup("Lisa • Settings","660x720")
        dialog.minsize(620,680)
        tk.Label(dialog,text="Make yourself at home",bg=PANEL,fg=FG,font=("Segoe UI",20,"bold")).pack(anchor="w",padx=22,pady=(18,10))
        tabs=ttk.Notebook(dialog)
        tabs.pack(fill="both",expand=True,padx=22)
        connection=tk.Frame(tabs,bg=PANEL)
        personal=tk.Frame(tabs,bg=PANEL)
        tabs.add(connection,text="Chat & voice")
        tabs.add(personal,text="Comfort & updates")
        entries={}
        keys={}
        def label(parent,text):
            tk.Label(parent,text=text,bg=PANEL,fg=MUTED,font=("Segoe UI",9),wraplength=570,justify="left").pack(anchor="w",pady=5)
        def field(parent,name,title,masked=False,value=""):
            label(parent,title)
            var=tk.StringVar(value=value)
            tk.Entry(parent,textvariable=var,show="●" if masked else "",bg=SOFT,fg=FG,insertbackground=FG,relief="flat",font=("Segoe UI",10)).pack(fill="x",ipady=6)
            (keys if masked else entries)[name]=var
        for page in (connection,personal):
            page.configure(padx=16,pady=10)
        field(connection,"gemini","Gemini API key • "+("saved" if self.credentials.get() else "needed"),True)
        field(connection,"elevenlabs","ElevenLabs API key • "+("saved" if self.voice_credentials.get() else "needed"),True)
        label(connection,"Blank keeps the saved key. Keys are encrypted for this Windows account. Enter them here, never in chat.")
        models=tk.Frame(connection,bg=PANEL)
        models.pack(fill="x",pady=4)
        models.grid_columnconfigure(1,weight=1)
        for row,(name,title) in enumerate([("gemini_model","Gemini model"),("eleven_model","Voice model"),("eleven_stt_model","Listening model")]):
            tk.Label(models,text=title,bg=PANEL,fg=MUTED,font=("Segoe UI",9)).grid(row=row,column=0,sticky="w",padx=(0,12),pady=6)
            var=tk.StringVar(value=self.store.settings[name])
            entries[name]=var
            tk.Entry(models,textvariable=var,bg=SOFT,fg=FG,insertbackground=FG,relief="flat",font=("Segoe UI",10)).grid(row=row,column=1,sticky="ew",ipady=5)
        field(connection,"eleven_voice_id","ElevenLabs Voice ID",value=self.store.settings["eleven_voice_id"])
        voice_selection=tk.StringVar(value="Load voices, then choose Lisa’s voice")
        voice_box=ttk.Combobox(connection,textvariable=voice_selection,state="readonly")
        voice_box.pack(fill="x",pady=(8,3))
        available={}
        voice_box.bind("<<ComboboxSelected>>",lambda event:entries["eleven_voice_id"].set(available.get(voice_selection.get(),"")))
        operations=tk.Frame(connection,bg=PANEL)
        operations.pack(fill="x",pady=6)
        feedback=tk.StringVar(value="Tests and previews use your API allowance. Voice replies are optional.")
        tk.Label(connection,textvariable=feedback,bg=PANEL,fg=FG,font=("Segoe UI",9),wraplength=570,justify="left").pack(anchor="w",pady=5)
        job_buttons=[]
        jobs=queue.Queue()
        active=[False]
        def settings_snapshot():
            values=dict(self.store.settings)
            values.update({k:v.get().strip() for k,v in entries.items()})
            return values
        def get_key(provider):
            credential=self.credentials if provider=="gemini" else self.voice_credentials
            value=keys[provider].get().strip() or credential.get()
            if not value:
                raise ValueError("Enter your "+provider+" key first.")
            credential.validate(value)
            return value
        def job(title,call,success):
            if active[0]:
                return
            self.interrupt()
            job_ticket=self.ticket
            active[0]=True
            feedback.set(title+"…")
            for item in job_buttons:
                item.configure(state="disabled")
            def run():
                try:
                    jobs.put((True,call()))
                except Exception as exc:
                    jobs.put((False,str(exc)))
            threading.Thread(target=run,daemon=True).start()
            def poll_job():
                if self.closing or not dialog.winfo_exists():
                    return
                try:
                    ok,result=jobs.get_nowait()
                except queue.Empty:
                    dialog.after(80,poll_job)
                    return
                active[0]=False
                for item in job_buttons:
                    item.configure(state="normal")
                if job_ticket!=self.ticket:
                    feedback.set("Cancelled. The result was discarded.")
                    return
                if ok:
                    try:
                        success(result)
                    except Exception as exc:
                        feedback.set(str(exc))
                else:
                    feedback.set(result)
            dialog.after(80,poll_job)
        def test_chat():
            try:
                client=GeminiClient(get_key("gemini"),settings_snapshot())
                job("Testing Gemini",lambda:client.chat("Say a short hello to Sir.",[],[]),lambda result:feedback.set("Gemini connected • "+result["reply"]))
            except Exception as exc:
                feedback.set(str(exc))
        def load_voices():
            try:
                client=ElevenLabsClient(get_key("elevenlabs"),settings_snapshot())
                def loaded(voices):
                    available.clear()
                    available.update({v["name"]+" • "+v["voice_id"]:v["voice_id"] for v in voices})
                    voice_box.configure(values=list(available))
                    feedback.set("Choose a voice from the list, then Preview voice." if voices else "No voices found. Add a voice in your ElevenLabs library or enter its Voice ID.")
                job("Loading your voices",client.voices,loaded)
            except Exception as exc:
                feedback.set(str(exc))
        def preview_voice():
            try:
                client=ElevenLabsClient(get_key("elevenlabs"),settings_snapshot())
                def play(data):
                    self.audio.play_wav(data,self.store.settings["volume"])
                    self.status.set("Lisa is speaking • Stop to interrupt")
                    feedback.set("Voice connected • hearing Lisa’s preview")
                job("Preparing voice preview",lambda:client.speech("Hello, Sir. I’m Lisa. Ready for a little chat?"),play)
            except Exception as exc:
                feedback.set(str(exc))
        for title,call in [("Test chat",test_chat),("Load voices",load_voices),("Preview voice",preview_voice)]:
            item=button(operations,title,call)
            item.pack(side="left",padx=(0,6))
            job_buttons.append(item)
        language=tk.StringVar(value=self.store.settings["language"])
        label(personal,"Conversation language")
        ttk.Combobox(personal,textvariable=language,values=["Auto","English","Hindi","Hinglish"],state="readonly",width=15).pack(anchor="w",pady=(0,12))
        motion=tk.BooleanVar(value=self.store.settings["motion"])
        sounds=tk.BooleanVar(value=self.store.settings["sound_enabled"])
        history=tk.BooleanVar(value=self.store.settings["save_history"])
        custom=tk.BooleanVar(value=self.store.settings["custom_chime"])
        for title,var in [("Animate breathing, blinking and speech",motion),("Soft interface sounds",sounds),("Use my generated chime",custom),("Save chat history on this PC",history)]:
            tk.Checkbutton(personal,text=title,variable=var,bg=PANEL,fg=FG,selectcolor=SOFT,activebackground=PANEL,activeforeground=FG,font=("Segoe UI",10)).pack(anchor="w",pady=4)
        label(personal,"Optional: generate one short ElevenLabs chime. It uses your sound-effects allowance once, then plays from this PC.")
        def generate_chime():
            try:
                client=ElevenLabsClient(get_key("elevenlabs"),settings_snapshot())
                def generated(data):
                    (self.store.directory/"chime.wav").write_bytes(data)
                    custom.set(True)
                    self.audio.play_wav(data,0.3)
                    feedback.set("Chime saved on this PC. Save Settings to use it.")
                tabs.select(connection)
                job("Generating one chime",client.sound_effect,generated)
            except Exception as exc:
                tabs.select(connection)
                feedback.set(str(exc))
        chime_button=button(personal,"Generate a chime",generate_chime)
        chime_button.pack(anchor="w",pady=6)
        job_buttons.append(chime_button)
        field(personal,"repository","Update repository",value=self.store.settings["repository"])
        label(personal,f"LISA {VERSION} • Test build\nCamera stays off. Closing the window quits Lisa and releases the microphone. Chat and saved notes go to Gemini; submitted recordings go to ElevenLabs. Providers may retain requests under their account policies.")
        def forget_keys():
            self.credentials.forget()
            self.voice_credentials.forget()
            for var in keys.values():
                var.set("")
            feedback.set("Saved keys removed. Environment-provided keys, if any, remain available.")
            self.status.set("Saved API keys removed")
        button(personal,"Remove saved API keys",forget_keys).pack(anchor="w",pady=8)
        row=tk.Frame(dialog,bg=PANEL)
        row.pack(fill="x",padx=22,pady=16)
        def save(use_ai=False):
            if active[0]:
                feedback.set("Wait for the current test to finish before saving.")
                tabs.select(connection)
                return
            try:
                values={k:v.get().strip() for k,v in entries.items()}
                if values["repository"]:
                    values["repository"]=parse_repo(values["repository"])
                if not all(values[k] for k in ("gemini_model","eleven_model","eleven_stt_model")):
                    raise ValueError("Model fields cannot be empty.")
                for provider,credential in [("gemini",self.credentials),("elevenlabs",self.voice_credentials)]:
                    if keys[provider].get().strip():
                        credential.validate(keys[provider].get())
                if use_ai:
                    get_key("gemini")
                for provider,credential in [("gemini",self.credentials),("elevenlabs",self.voice_credentials)]:
                    if keys[provider].get().strip():
                        credential.save(keys[provider].get())
                self.interrupt()
                self.store.settings.update(values)
                self.store.settings.update(motion=motion.get(),sound_enabled=sounds.get(),save_history=history.get(),language=language.get(),custom_chime=custom.get())
                if use_ai:
                    self.demo_var.set(False)
                    self.store.settings["demo_enabled"]=False
                self.store.save()
                self.status.set("Gemini ready • microphone off" if not self.demo_var.get() and self.credentials.get() else "Settings saved • Free demo")
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror("Settings",str(exc),parent=dialog)
        button(row,"Voice library",lambda:webbrowser.open("https://elevenlabs.io/app/voice-library")).pack(side="left")
        button(row,"Save & use AI",lambda:save(True),True).pack(side="right")
        button(row,"Save",save).pack(side="right",padx=6)

    def check_update(self):
        repo=self.store.settings["repository"]
        if not repo:
            messagebox.showinfo("Updates","Add the GitHub update repository in Settings. Future releases need LISA.exe and SHA256SUMS.txt.",parent=self)
            return
        self.update_button.configure(state="disabled",text="Checking…")
        def run():
            try:
                self.events.put(("update_check",0,updates.latest_release(repo)))
            except Exception as exc:
                self.events.put(("update_error",0,str(exc)))
        threading.Thread(target=run,daemon=True).start()

    def handle_update(self,kind,result):
        self.update_button.configure(state="normal",text="Check for updates")
        if kind=="update_error":
            messagebox.showinfo("Updates",result,parent=self)
        elif kind=="update_check":
            if not result:
                messagebox.showinfo("Updates","You’re using the latest available version, Sir.",parent=self)
            elif messagebox.askyesno("Lisa update",f"Version {result['version']} is available. Download and install it?\n\nYour settings and saved memory will be kept.",parent=self):
                self.update_button.configure(state="disabled",text="Downloading…")
                def run():
                    try:
                        self.events.put(("update_download",0,updates.download_release(result,self.store.directory/"updates")))
                    except Exception as exc:
                        self.events.put(("update_error",0,str(exc)))
                threading.Thread(target=run,daemon=True).start()
        elif kind=="update_download":
            try:
                updates.install_update(result,self.store.directory)
                self.close()
            except Exception as exc:
                messagebox.showerror("Updates",str(exc),parent=self)

    def close(self):
        if self.closing:
            return
        self.closing=True
        self.ticket+=1
        self.cancel_speech.set()
        demo.cancel()
        self.stage.closed=True
        self.audio.close()
        try:
            self.store.save()
        finally:
            self.destroy()


def main():
    if os.name=="nt":
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    app=LisaApp(test_mode="--self-test" in sys.argv)
    if "--self-test" in sys.argv:
        def check():
            report={"version":VERSION,"poses":len(MOODS),"outfits":len(OUTFITS),"microphone_open":bool(app.audio.input_stream),"key_configured":bool(app.credentials.get())}
            for mood in MOODS:
                app.stage.set_mood(mood)
                frame=app.stage.render_frame(560,610)
                assert frame.size==(560,610)
            app.stage.set_mood("smile")
            app.stage.render_frame(560,610).save(app.store.directory/"stage-preview.png")
            app.input.insert("1.0","Hello Lisa")
            app.send()
            assert app.busy
            app.interrupt()
            assert not app.busy and not app.audio.recording
            report["interruption_checked"]=True
            app.store.write("self-test.json",report)
            app.close()
        app.after(500,check)
    app.mainloop()


if __name__=="__main__":
    main()
