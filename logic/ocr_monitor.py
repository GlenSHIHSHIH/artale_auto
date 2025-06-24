import threading, time, pytesseract, pyautogui, logging, math, re
from PIL import ImageGrab, ImageEnhance, ImageOps
import pygetwindow as gw

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logging.basicConfig(level=logging.INFO, filename="ocr_heal.log", format="%(asctime)s %(message)s")

class HealthMonitor:
    def __init__(self, win_prefix, region, mode, threshold, target, key, update_callback, heal_value):
        self.win_prefix = win_prefix
        self.region = region
        self.mode = mode
        self.threshold = threshold
        self.target = target
        self.key = key
        self.update_callback = update_callback
        self.heal_value = heal_value
        self.running = False
        self.thread = None
        self.max_hp = None

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

    def preprocess_image(self, img):
        img = img.resize((img.width * 2, img.height * 2))
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = ImageOps.invert(img)
        img = img.point(lambda x: 0 if x < 128 else 255, "1")
        return img

    def loop(self):
        while self.running:
            win = next((w for w in gw.getAllWindows() if w.title.startswith(self.win_prefix)), None)
            if not win:
                self.update_callback("No window")
                time.sleep(1)
                continue

            x1, y1, x2, y2 = self.region
            bbox = win.left + x1, win.top + y1, win.left + x2, win.top + y2
            img = ImageGrab.grab(bbox)
            processed_img = self.preprocess_image(img)

            try:
                text = pytesseract.image_to_string(
                    processed_img,
                    config="--psm 7 -c tessedit_char_whitelist=0123456789/"
                )
            except Exception:
                self.update_callback("OCR Error")
                time.sleep(1)
                continue

            raw_text = text.strip()

            # corrections = {
            #     '[': '1', '|': '/', 'I': '1',
            #     'l': '1', 'O': '0', 'S': '5', 'B': '8'
            # }
            # for wrong, correct in corrections.items():
            #     raw_text = raw_text.replace(wrong, correct)

            raw_text = raw_text.replace("[", "").replace("]", "")
            self.update_callback(f"OCR 原文: {raw_text}")

            text = re.sub(r"[^\d/\.]", "", raw_text)
            parts = [p for p in text.split("/") if p.strip()]

            try:
                if len(parts) == 2:
                    current_hp, max_hp = map(int, parts)
                    percent = (current_hp / max_hp) * 100
                    hp = percent if self.mode == "%_below" else current_hp
                    self.max_hp = max_hp
                else:
                    current_hp = float(''.join(c for c in text if c.isdigit() or c == '.'))
                    if self.max_hp:
                        max_hp = self.max_hp
                        percent = (current_hp / max_hp) * 100
                        hp = percent if self.mode == "%_below" else current_hp
                    else:
                        raise ValueError("未偵測到最大 HP 值")

            except Exception:
                self.update_callback(f"OCR error: {text}")
                time.sleep(0.2)
                continue

            self.update_callback(f"{current_hp:.0f}/{max_hp:.0f} | {percent:.1f}%")

            if (self.mode == "%_below" and hp < self.threshold) or (self.mode == "value_below" and current_hp < self.threshold):
                target_hp = max_hp * (self.target / 100) if self.mode == "%_below" else self.target
                delta = target_hp - current_hp
                times = math.ceil(delta / self.heal_value)

                for _ in range(times):
                    if not self.running:
                        break
                    pyautogui.press(self.key)
                    current_hp += self.heal_value
                    percent = (current_hp / max_hp) * 100 if max_hp else 0
                    self.update_callback(f"{current_hp:.0f}/{max_hp:.0f} | {percent:.1f}%")
                    time.sleep(0.1)

            time.sleep(0.4)
