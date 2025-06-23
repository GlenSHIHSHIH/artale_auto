import customtkinter as ctk
from logic.skill import Skill
from tkinter import filedialog
import json
import keyboard

class SkillEntry:
    def __init__(self, master, container):
        self.master = master
        self.container = container
        self.frame = ctk.CTkFrame(master)
        self.frame.pack(pady=2, fill="x")

        self.name = ctk.StringVar()
        self.key = ctk.StringVar()
        self.hold = ctk.DoubleVar(value=0.8)
        self.interval = ctk.DoubleVar(value=300)

        ctk.CTkLabel(self.frame, text="名稱").pack(side="left", padx=2)
        ctk.CTkEntry(self.frame, textvariable=self.name, width=100, placeholder_text="技能名稱").pack(side="left", padx=2)

        ctk.CTkLabel(self.frame, text="按鍵").pack(side="left", padx=2)
        ctk.CTkEntry(self.frame, textvariable=self.key, width=50, placeholder_text="按鍵").pack(side="left", padx=2)

        ctk.CTkLabel(self.frame, text="按住秒數(預設0.8秒)").pack(side="left", padx=2)
        ctk.CTkEntry(self.frame, textvariable=self.hold, width=70).pack(side="left", padx=2)

        ctk.CTkLabel(self.frame, text="重複時間").pack(side="left", padx=2)
        ctk.CTkEntry(self.frame, textvariable=self.interval, width=70).pack(side="left", padx=2)

        self.remove_btn = ctk.CTkButton(self.frame, text="刪除", command=self.remove)
        self.remove_btn.pack(side="left", padx=2)

    def remove(self):
        self.frame.destroy()
        self.container.remove(self)

    def to_skill(self):
        return Skill(self.name.get(), self.key.get(), self.hold.get(), self.interval.get())

class SkillManager(ctk.CTkFrame):
    def __init__(self, master, toggle_ocr_callback=None):
        super().__init__(master)
        self.entries = []
        self.toggle_ocr_callback = toggle_ocr_callback
        self.skills_running = False  # 技能狀態
        self.pack(padx=10, pady=10, fill="both")

        ctk.CTkLabel(self, text="技能設定").pack(anchor="w")
        self.add_btn = ctk.CTkButton(self, text="新增技能", command=self.add_entry)
        self.add_btn.pack(pady=5)

        self.entries_frame = ctk.CTkFrame(self)
        self.entries_frame.pack(fill="x")

        self.start_btn = ctk.CTkButton(self, text="F7 開始施放", command=self.toggle_skills)
        self.start_btn.pack(pady=5)

        self.register_hotkeys()

    def add_entry(self):
        entry = SkillEntry(self.entries_frame, self)
        self.entries.append(entry)

    def remove(self, entry):
        if entry in self.entries:
            self.entries.remove(entry)

    def toggle_skills(self):
        if self.skills_running:
            self.stop_skills()
        else:
            self.start_skills()

    def start_skills(self):
        for entry in self.entries:
            skill = entry.to_skill()
            entry.skill = skill
            skill.start()
        self.skills_running = True
        self.start_btn.configure(text="F7 停止施放")

    def stop_skills(self):
        for entry in self.entries:
            if hasattr(entry, "skill"):
                entry.skill.stop()
        self.skills_running = False
        self.start_btn.configure(text="F7 開始施放")

    def toggle_all(self):
        self.toggle_skills()
        if self.toggle_ocr_callback:
            self.toggle_ocr_callback()

    def register_hotkeys(self):
        keyboard.add_hotkey("f7", self.toggle_skills)
        if self.toggle_ocr_callback:
            keyboard.add_hotkey("f6", self.toggle_ocr_callback)
            keyboard.add_hotkey("f5", self.toggle_all)

    def export_skills(self):
        data = {
            "skills": [
                {
                    "name": e.name.get(),
                    "key": e.key.get(),
                    "hold": e.hold.get(),
                    "interval": e.interval.get()
                } for e in self.entries
            ]
        }
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file:
            with open(file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

    def import_skills(self):
        file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file:
            return
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "skills" in data:
            for e in self.entries:
                e.frame.destroy()
            self.entries.clear()
            for s in data["skills"]:
                entry = SkillEntry(self.entries_frame, self)
                entry.name.set(s.get("name", ""))
                entry.key.set(s.get("key", ""))
                entry.hold.set(s.get("hold", 0.5))
                entry.interval.set(s.get("interval", 1.0))
                self.entries.append(entry)

        if hasattr(self.master, "load_ocr_settings") and "ocr" in data:
            self.master.load_ocr_settings(data["ocr"])
