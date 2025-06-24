## Artale 楓之谷 自動技能+補(血/魔)

## 安裝教學

1.python
https://www.python.org/downloads/

2.tesseract(OCR)

```
下載網址:
https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe

安裝路徑:
C:\Program Files\Tesseract-OCR\tesseract.exe

環境變數設定 (command 命令提示自元)
set PATH=%PATH%;"C:\Program Files\Tesseract-OCR"

```

## 執行檔案

python main.python

## 設定教學

![設定畫面](pic\setting.png)

### 技能

* 按住秒數：需注意按鍵秒數，通常為0.5 ~ 0.8，如果再攻擊技能重疊後仍未施放，可考慮加長時間
* 重複時間：循環施放的等待時間，如果不想中斷，建議為技能秒數-3~5秒

### 補血與補魔

* 設定補(血/魔)截圖區域：偵測的血量與魔量，請參考圖片設定，並確認座標與偵測到的魔力與血量變化是否正確
* (血量/魔力)低於百分比時補(血/魔)：低於設定的百分比，能自動喝水
* 補(血/魔)至百分比：當需要補時，會依照設定自動判斷喝幾灌水，喝水數量會 >= 設定的百分比
* 補(血/魔)鍵：先設於楓之谷內快捷鍵，再填入快捷鍵按鍵
* 每次補(血/魔)數值：藥水的補充數值 (例:白水 HP:300 活力藥水 MP:300) 填入 300