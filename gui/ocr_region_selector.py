import tkinter as tk

def get_region_by_mouse(callback):
    sel = tk.Tk()
    sel.attributes("-fullscreen", True)
    sel.attributes("-alpha", 0.3)
    sel.configure(bg="black")
    sel.title("拖曳選取區域 - 按 ESC 取消")

    canvas = tk.Canvas(sel, cursor="cross")
    canvas.pack(fill=tk.BOTH, expand=True)

    start = [0, 0]
    rect = [None]

    def on_press(event):
        start[0], start[1] = event.x, event.y
        rect[0] = canvas.create_rectangle(start[0], start[1], event.x, event.y, outline="red", width=2)

    def on_drag(event):
        canvas.coords(rect[0], start[0], start[1], event.x, event.y)

    def on_release(event):
        x1, y1 = start[0], start[1]
        x2, y2 = event.x, event.y
        sel.destroy()
        callback((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))

    def on_escape(event):
        sel.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    sel.bind("<Escape>", on_escape)
    sel.mainloop()