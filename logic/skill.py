import threading
import time
import pyautogui

class Skill:
    lock = threading.Lock()  # 所有技能共用一把鎖

    def __init__(self, name, key, hold, interval):
        self.name = name
        self.key = key
        self.hold = hold
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def loop(self):
        while self.running:
            with Skill.lock:
                #print(f"執行技能: {self.name}")
                pyautogui.keyDown(self.key)
                time.sleep(self.hold)
                pyautogui.keyUp(self.key)
            time.sleep(self.interval)
