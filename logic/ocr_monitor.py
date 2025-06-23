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

    def start(self):
        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()

    def stop(self):
        self.running = False

    def preprocess_image(self, img):
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = ImageOps.invert(img)
        img = img.point(lambda x: 0 if x < 128 else 255, "1")
        return img

    def loop(self):
        while self.running:
            win = next((w for w in gw.getAllWindows() if w.title.startswith(self.win_prefix)), None)
            if not win:
                # logging.error(f"找不到視窗: {self.win_prefix}")
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
            except Exception as e:
                # logging.error(f"OCR 執行錯誤: {e}")
                self.update_callback("OCR Error")
                time.sleep(1)
                continue

            raw_text = text.strip()
            raw_text = raw_text.replace("[", "").replace("]", "").replace("|", "/")
            self.update_callback(f"OCR 原文: {raw_text}")
            text = re.sub(r"[^\d/\.]", "", raw_text)
            # logging.info(f"OCR 清理後: '{text}'")
            parts = [p for p in text.split("/") if p.strip()]

            try:
                if len(parts) == 2:
                    current_hp, max_hp = map(int, parts)
                    percent = (current_hp / max_hp) * 100
                    hp = percent if self.mode == "%_below" else current_hp
                else:
                    current_hp = float(''.join(c for c in text if c.isdigit() or c == '.'))
                    # 嘗試用先前 max_hp，如果沒有就跳過
                    if hasattr(self, "max_hp") and self.max_hp:
                        max_hp = self.max_hp
                    else:
                        raise ValueError("未偵測到最大 HP 值")
                    percent = (current_hp / max_hp) * 100
                    hp = percent if self.mode == "%_below" else current_hp

                self.max_hp = max_hp  # 儲存供下次使用

            except Exception as e:
                # logging.error(f"OCR 數值解析失敗: '{text}' | 錯誤: {e}")
                self.update_callback(f"OCR error: {text}")
                time.sleep(0.5)
                continue

            # 顯示詳細狀態：目前 HP 與百分比
            self.update_callback(f"{current_hp:.0f}/{max_hp:.0f} | {percent:.1f}%")

            # 補血邏輯
            if (self.mode == "%_below" and hp < self.threshold) or (self.mode == "value_below" and current_hp < self.threshold):
                target_hp = max_hp * (self.target / 100) if self.mode == "%_below" else self.target
                delta = target_hp - current_hp
                times = math.ceil(delta / self.heal_value)

                # logging.info(f"補血觸發：當前HP={current_hp}, 目標={target_hp}, 每次補={self.heal_value}, 預估補 {times} 次")
                for _ in range(times):
                    if not self.running:
                        break
                    pyautogui.press(self.key)
                    current_hp += self.heal_value
                    percent = (current_hp / max_hp) * 100 if max_hp else 0
                    self.update_callback(f"{current_hp:.0f}/{max_hp:.0f} | {percent:.1f}%")
                    time.sleep(0.1)

            time.sleep(0.2)
