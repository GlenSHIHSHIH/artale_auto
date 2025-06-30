import threading, time, pytesseract, pyautogui, logging, math, re
from PIL import ImageGrab, ImageEnhance, ImageOps, Image, ImageFilter
import pygetwindow as gw

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

logging.basicConfig(level=logging.INFO, filename="ocr_heal.log", format="%(asctime)s %(message)s")

class HealthMonitor:
    def __init__(self, win_prefix, region, threshold, target, key, update_callback, heal_value):
        self.win_prefix = win_prefix
        self.region = region
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
        """简化的图像预处理"""
        # 放大图像
        img = img.resize((img.width * 4, img.height * 4), Image.LANCZOS)
        
        # 转灰度
        img = img.convert("L")
        
        # 增强对比度
        img = ImageEnhance.Contrast(img).enhance(3.0)
        
        # 锐化
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        
        # 简单二值化
        img = img.point(lambda x: 0 if x < 120 else 255, "L")
        
        return img

    def extract_hp_from_text(self, raw_text):
        # 移除明显的干扰字符
        cleaned = raw_text
        
        # 处理常见误识别
        replacements = {
            'i': '1','I': '1', 
            'E': '2',
            'c': '3','E': '2',
            'z': '2','Z': '2',
            'O': '0','o': '0',
            'S': '5','s': '5',
            'b': '6', 'G': '6',
            'e': '8','B': '8',
            'g': '9',            
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        """从完整文本中提取HP数值 - 移除前3位和后1位"""
     
        # 移除换行和多余空格
        cleaned = cleaned.replace('\n', '').replace('\r', '').replace(' ', '').strip()
        
        #print(f"清理后文本: '{cleaned}'")
        
        # 检查文本长度，确保至少有4个字符才能移除前3后1
        if len(cleaned) < 7:
            # #print("文本太短，无法移除前綴與後1位")
            return None, None
        
        index = cleaned.rfind('[')
        
        if index == -1:
            index = next((i for i, c in enumerate(cleaned) if c.isdigit()), -1)  
            index+1         

        trimmed = cleaned[index:-1]
        
        # 只保留数字和斜杠
        numbers_only = re.sub(r'[^\d/]', '', trimmed)
        # #print(f"只保留数字: '{numbers_only}'")
        
        # 寻找 数字/数字 的模式
        hp_pattern = r'(\d+)/(\d+)'
        match = re.search(hp_pattern, numbers_only)
        
        if match:
            try:
                current_hp = int(match.group(1))
                max_hp = int(match.group(2))
                
                # 验证数值合理性
                if current_hp > max_hp:
                    # 尝试修正：如果当前HP位数比最大HP多，截取后面部分
                    current_str = str(current_hp)
                    max_str = str(max_hp)
                
                # 最终验证
                if 0 <= current_hp <= max_hp:
                    #print(f"結果: {current_hp}/{max_hp}")
                    return current_hp, max_hp
                else:
                    #print(f"數值不合理: {current_hp}/{max_hp}")
                    return None, None
                    
            except ValueError as e:
                #print(f"數值轉換錯誤: {e}")
                return None, None
        else:
            #print("未找到數值格式")
            return None, None

    def loop(self):
        while self.running:
            win = next((w for w in gw.getAllWindows() if w.title.startswith(self.win_prefix)), None)
            if not win:
                self.update_callback("No window")
                time.sleep(1)
                continue

            x1, y1, x2, y2 = self.region
            bbox = x1, y1, x2, y2
            img = ImageGrab.grab(bbox)
            
            processed_img = self.preprocess_image(img)
            
            # 使用宽松的OCR配置来读取全部文字
            try:
                
                # 如果第一种方法失败，尝试第二种配置
                full_text = pytesseract.image_to_string(
                    processed_img,
                    config="--oem 1 --psm 6 -c tessedit_char_whitelist=0123456789/[]HPMPabcdefghijklmnopqrstuvwxyz",
                ).strip()
                # #print(f"ocr识别: '{full_text}'")
                
            except Exception as e:
                #print(f"OCR错误: {e}")
                self.update_callback("OCR Error")
                time.sleep(1)
                continue

            

            # 从完整文本中提取HP数值（移除前3后1）
            current_hp, max_hp = self.extract_hp_from_text(full_text)
            
            if current_hp is None or max_hp is None or current_hp <= 0:
                self.update_callback(f"解析失败: {full_text}")
                time.sleep(0.5)
                continue
            
            percent = (current_hp / max_hp) * 100            
            
            self.update_callback(f"{current_hp}/{max_hp} | {percent:.1f}%")
            
            # 治疗逻辑
            if ( percent < self.threshold) :
                target_hp = max_hp * (self.target / 100) 
                delta = target_hp - current_hp
                times = math.ceil(delta / self.heal_value)

                for _ in range(times):
                    if not self.running:
                        break
                    pyautogui.press(self.key)
                    current_hp += self.heal_value
                    time.sleep(0.1)

            time.sleep(0.5)