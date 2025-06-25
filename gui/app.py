import customtkinter as ctk
from gui.ocr_region_selector import get_region_by_mouse
from logic.ocr_monitor import HealthMonitor
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
        self.skills_running = False
        self.pack(padx=10, pady=10, fill="both")

        ctk.CTkLabel(self, text="技能設定").pack(anchor="w")
        self.add_btn = ctk.CTkButton(self, text="新增技能", command=self.add_entry)
        self.add_btn.pack(pady=5)

        self.entries_frame = ctk.CTkFrame(self)
        self.entries_frame.pack(fill="x")

        self.start_btn = ctk.CTkButton(self, text="F8 開/關 技能", command=self.toggle_skills)
        self.start_btn.pack(pady=5)

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
        self.start_btn.configure(text="F8 停止技能")

    def stop_skills(self):
        for entry in self.entries:
            if hasattr(entry, "skill"):
                entry.skill.stop()
        self.skills_running = False
        self.start_btn.configure(text="F8 開/關 技能")

    def toggle_all(self):
        self.toggle_skills()
        if self.toggle_ocr_callback:
            self.toggle_ocr_callback()

    def export_skills(self):
        master = self.master
        data = {
            "skills": [
                {
                    "name": e.name.get(),
                    "key": e.key.get(),
                    "hold": e.hold.get(),
                    "interval": e.interval.get()
                } for e in self.entries
            ],
            "ocr": {
                "pref_var": master.pref_var.get(),
                "region": master.region,
                "th_var": master.th_var.get(),
                "target_var": master.target_var.get(),
                "key_var": master.key_var.get(),
                "heal_value_var": master.heal_value_var.get(),

                "mana_region": master.mana_region,
                "mana_th_var": master.mana_th_var.get(),
                "mana_target_var": master.mana_target_var.get(),
                "mana_key_var": master.mana_key_var.get(),
                "mana_value_var": master.mana_value_var.get()
            }
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

class SkillCasterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.all_running = False  # F5 狀態記憶
        self.title("技能 + OCR 補血補魔器")
        self.geometry("600x850")

        self.monitor = None
        self.mana_monitor = None
        self.region = (0, 0, 200, 50)
        self.mana_region = (0, 60, 200, 110)

        self.skill_manager = SkillManager(self, toggle_ocr_callback=self.toggle_monitor_all)

        frame_main = ctk.CTkFrame(self)
        frame_main.pack(padx=10, pady=10, fill="both", expand=True)

        ctk.CTkLabel(frame_main, text="視窗名稱前綴").pack(anchor="w")
        self.pref_var = ctk.StringVar(value="Maple")
        ctk.CTkEntry(frame_main, textvariable=self.pref_var, placeholder_text="視窗名稱前綴").pack(fill="x", pady=2)

        frm1 = ctk.CTkFrame(frame_main)
        frm1.pack(side="left", padx=10, fill="both", expand=True)

        ctk.CTkLabel(frm1, text="OCR 補血設定").pack(anchor="w")

        self.region_btn = ctk.CTkButton(frm1, text="設定補血截圖區域", command=self.pick_region)
        self.region_btn.pack(anchor="w", pady=2)

        self.th_var = ctk.DoubleVar(value=50.0)
        self.target_var = ctk.DoubleVar(value=80.0)
        self.key_var = ctk.StringVar(value="Delete")
        self.heal_value_var = ctk.IntVar(value=300)

        ctk.CTkLabel(frm1, text="血量低於百分比時補血").pack(anchor="w")
        ctk.CTkEntry(frm1, textvariable=self.th_var, placeholder_text="血量門檻（%）").pack(fill="x", pady=2)

        ctk.CTkLabel(frm1, text="補血至百分比").pack(anchor="w")
        ctk.CTkEntry(frm1, textvariable=self.target_var, placeholder_text="補血至（%）").pack(fill="x", pady=2)

        ctk.CTkLabel(frm1, text="補血鍵").pack(anchor="w")
        ctk.CTkEntry(frm1, textvariable=self.key_var, placeholder_text="補血鍵").pack(fill="x", pady=2)

        ctk.CTkLabel(frm1, text="每次補血數值（估算）").pack(anchor="w")
        ctk.CTkEntry(frm1, textvariable=self.heal_value_var, placeholder_text="例如 300").pack(fill="x", pady=2)

        self.status_var = ctk.StringVar(value="血量: N/A")
        ctk.CTkLabel(frm1, textvariable=self.status_var).pack(anchor="w", pady=5)

        frm2 = ctk.CTkFrame(frame_main)
        frm2.pack(side="right", padx=10, fill="both", expand=True)
        ctk.CTkLabel(frm2, text="OCR 補魔設定").pack(anchor="w")

        self.mana_region_btn = ctk.CTkButton(frm2, text="設定補魔截圖區域", command=self.pick_mana_region)
        self.mana_region_btn.pack(anchor="w", pady=2)

        self.mana_th_var = ctk.DoubleVar(value=40.0)
        self.mana_target_var = ctk.DoubleVar(value=85.0)
        self.mana_key_var = ctk.StringVar(value="End")
        self.mana_value_var = ctk.IntVar(value=200)

        ctk.CTkLabel(frm2, text="魔力低於百分比時補魔").pack(anchor="w")
        ctk.CTkEntry(frm2, textvariable=self.mana_th_var, placeholder_text="魔力門檻（%）").pack(fill="x", pady=2)

        ctk.CTkLabel(frm2, text="補魔至百分比").pack(anchor="w")
        ctk.CTkEntry(frm2, textvariable=self.mana_target_var, placeholder_text="補魔至（%）").pack(fill="x", pady=2)

        ctk.CTkLabel(frm2, text="補魔鍵").pack(anchor="w")
        ctk.CTkEntry(frm2, textvariable=self.mana_key_var, placeholder_text="補魔鍵").pack(fill="x", pady=2)

        ctk.CTkLabel(frm2, text="每次補魔數值（估算）").pack(anchor="w")
        ctk.CTkEntry(frm2, textvariable=self.mana_value_var, placeholder_text="例如 200").pack(fill="x", pady=2)

        self.mana_status_var = ctk.StringVar(value="魔力: N/A")
        ctk.CTkLabel(frm2, textvariable=self.mana_status_var).pack(anchor="w", pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", pady=10)

        self.toggle_btn = ctk.CTkButton(btn_frame, text="F6 開/關 OCR 補血", command=self.toggle_monitor)
        self.toggle_btn.pack(side="left", padx=5)

        self.toggle_mana_btn = ctk.CTkButton(btn_frame, text="F7 開/關 OCR 補魔", command=self.toggle_mana_monitor)
        self.toggle_mana_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(btn_frame, text="F5 開/關 技能+補血+補魔", command=self.toggle_monitor_all)
        self.stop_btn.pack(side="left", padx=5)

        btn_setting_frame = ctk.CTkFrame(self)
        btn_setting_frame.pack(fill="x", pady=10)

        ctk.CTkButton(btn_setting_frame, text="匯入設定", command=self.skill_manager.import_skills).pack(side="right", padx=5)
        ctk.CTkButton(btn_setting_frame, text="儲存設定", command=self.skill_manager.export_skills).pack(side="right", padx=5)
        self.register_hotkeys()

    def register_hotkeys(self):
        keyboard.add_hotkey("f8", self.skill_manager.toggle_skills)
        keyboard.add_hotkey("f5", self.toggle_monitor_all)
        keyboard.add_hotkey("f6", self.toggle_monitor)
        keyboard.add_hotkey("f7", self.toggle_mana_monitor)

    def pick_region(self):
        get_region_by_mouse(lambda region: self.set_region(region, is_mana=False))

    def pick_mana_region(self):
        get_region_by_mouse(lambda region: self.set_region(region, is_mana=True))

    def set_region(self, region, is_mana):
        if is_mana:
            self.mana_region = region
            self.mana_status_var.set(f"座標: {region}")
        else:
            self.region = region
            self.status_var.set(f"座標: {region}")

    def update_status(self, text):
        coord_text = f"座標: {self.region}"
        self.status_var.set(f"{coord_text} \n血量: {text}")

    def update_mana_status(self, text):
        coord_text = f"座標: {self.mana_region}"
        self.mana_status_var.set(f"{coord_text} \n魔力: {text}")

    def toggle_monitor(self):
        if self.monitor and self.monitor.running:
            self.monitor.stop()
            self.toggle_btn.configure(text="F6 開/關 OCR 補血")
        else:
            self.start_monitor()

    def toggle_mana_monitor(self):
        if self.mana_monitor and self.mana_monitor.running:
            self.mana_monitor.stop()
            self.toggle_mana_btn.configure(text="F7 開/關 OCR 補魔")
        else:
            self.start_mana_monitor()

    def toggle_monitor_all(self):
        if self.all_running:
            # 全部關閉
            if self.monitor and self.monitor.running:
                self.monitor.stop()
                self.toggle_btn.configure(text="F6 開/關 OCR 補血")

            if self.mana_monitor and self.mana_monitor.running:
                self.mana_monitor.stop()
                self.toggle_mana_btn.configure(text="F7 開/關 OCR 補魔")

            if self.skill_manager.skills_running:
                self.skill_manager.stop_skills()

            self.stop_btn.configure(text="F5 啟動 技能+補血+補魔")
            self.all_running = False
        else:
            # 全部開啟
            self.start_monitor()
            self.start_mana_monitor()
            self.skill_manager.start_skills()

            self.stop_btn.configure(text="F5 停止 技能+補血+補魔")
            self.all_running = True

    def start_monitor(self):
        self.monitor = HealthMonitor(
            self.pref_var.get(), self.region,
            self.th_var.get(),self.target_var.get(),
            self.key_var.get(),self.update_status,
            self.heal_value_var.get()
        )
        self.monitor.start()
        self.toggle_btn.configure(text="F6 停止 OCR 補血")

    def start_mana_monitor(self):
        self.mana_monitor = HealthMonitor(
            self.pref_var.get(),self.mana_region,
            self.mana_th_var.get(),self.mana_target_var.get(),
            self.mana_key_var.get(),self.update_mana_status,
            self.mana_value_var.get()
        )
        self.mana_monitor.start()
        self.toggle_mana_btn.configure(text="F7 停止 OCR 補魔")

    def load_ocr_settings(self, ocr_data):
        self.pref_var.set(ocr_data.get("pref_var", "Maple"))
        self.region = tuple(ocr_data.get("region", (0, 0, 200, 50)))
        self.th_var.set(ocr_data.get("th_var", 50.0))
        self.target_var.set(ocr_data.get("target_var", 80.0))
        self.key_var.set(ocr_data.get("key_var", "Delete"))
        self.heal_value_var.set(ocr_data.get("heal_value_var", 300))

        self.mana_region = tuple(ocr_data.get("mana_region", (0, 60, 200, 110)))
        self.mana_th_var.set(ocr_data.get("mana_th_var", 40.0))
        self.mana_target_var.set(ocr_data.get("mana_target_var", 85.0))
        self.mana_key_var.set(ocr_data.get("mana_key_var", "End"))
        self.mana_value_var.set(ocr_data.get("mana_value_var", 200))

        self.status_var.set(f"座標: {self.region}")
        self.mana_status_var.set(f"座標: {self.mana_region}")
