import customtkinter as ctk
from gui.ocr_region_selector import get_region_by_mouse
from logic.ocr_monitor import HealthMonitor
from gui.skill_gui import SkillManager

class SkillCasterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("技能 + OCR 補血器")
        self.geometry("800x850")
        self.monitor = None
        self.region = (0, 0, 200, 50)

        self.skill_manager = SkillManager(self, toggle_ocr_callback=self.toggle_monitor)

        frm = ctk.CTkFrame(self)
        frm.pack(padx=10, pady=10, fill="x")
        ctk.CTkLabel(frm, text="OCR 補血設定").pack(anchor="w")

        self.pref_var = ctk.StringVar(value="Maple")
        ctk.CTkEntry(frm, textvariable=self.pref_var, placeholder_text="視窗名稱前綴").pack(fill="x", pady=2)

        self.region_btn = ctk.CTkButton(frm, text="設定截圖區域", command=self.pick_region)
        self.region_btn.pack(anchor="w", pady=2)

        self.mode_var = ctk.StringVar(value="%_below")

        ctk.CTkLabel(frm, text="血量低於百分比時補血").pack(anchor="w")
        self.th_var = ctk.DoubleVar(value=50.0)
        ctk.CTkEntry(frm, textvariable=self.th_var, placeholder_text="血量門檻（%）").pack(fill="x", pady=2)

        ctk.CTkLabel(frm, text="補血至百分比").pack(anchor="w")
        self.target_var = ctk.DoubleVar(value=80.0)
        ctk.CTkEntry(frm, textvariable=self.target_var, placeholder_text="補血至（%）").pack(fill="x", pady=2)

        ctk.CTkLabel(frm, text="補血鍵").pack(anchor="w")
        self.key_var = ctk.StringVar(value="Delete")
        ctk.CTkEntry(frm, textvariable=self.key_var, placeholder_text="補血鍵").pack(fill="x", pady=2)

        ctk.CTkLabel(frm, text="每次補血數值（估算）").pack(anchor="w")
        self.heal_value_var = ctk.IntVar(value=300)
        ctk.CTkEntry(frm, textvariable=self.heal_value_var, placeholder_text="例如 2").pack(fill="x", pady=2)

        self.status_var = ctk.StringVar(value="血量: N/A")
        ctk.CTkLabel(frm, textvariable=self.status_var).pack(anchor="w", pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", pady=10)

        self.toggle_btn = ctk.CTkButton(btn_frame, text="F6 開/關 OCR", command=self.toggle_monitor)
        self.toggle_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(btn_frame, text="F5 開/關 OCR+技能", command=self.skill_manager.toggle_all)
        self.stop_btn.pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="匯入設定", command=self.skill_manager.import_skills).pack(side="right", padx=5)
        ctk.CTkButton(btn_frame, text="儲存設定", command=self.skill_manager.export_skills).pack(side="right", padx=5)

    def pick_region(self):
        def region_callback(region):
            self.region = region
            print(f"已設定範圍: {region}")
            self.status_var.set(f"座標: {region}")
        get_region_by_mouse(region_callback)

    def update_status(self, text):
        coord_text = f"座標: {self.region}"
        self.status_var.set(f"{coord_text}｜血量: {text}")

    def toggle_monitor(self):
        if self.monitor and self.monitor.running:
            self.monitor.stop()
            self.toggle_btn.configure(text="F6 開/關 OCR")
        else:
            self.start_monitor()

    def start_monitor(self):
        prefix = self.pref_var.get().strip()
        monitor = HealthMonitor(
            prefix, self.region,
            self.mode_var.get(), self.th_var.get(),
            self.target_var.get(), self.key_var.get(),
            self.update_status,
            heal_value=self.heal_value_var.get()
        )
        monitor.start()
        self.monitor = monitor
        self.toggle_btn.configure(text="F6 停止 OCR 補血")

    def load_ocr_settings(self, ocr_data):
        self.pref_var.set(ocr_data.get("window_prefix", ""))
        self.region = tuple(ocr_data.get("region", (0, 0, 200, 50)))
        self.th_var.set(ocr_data.get("threshold", 50))
        self.target_var.set(ocr_data.get("target", 80))
        self.key_var.set(ocr_data.get("key", "f"))
        self.heal_value_var.set(ocr_data.get("heal_value", 2))
