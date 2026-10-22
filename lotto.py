import random
import tkinter as tk
from datetime import datetime

SETS = 5
PICK = 6


def ball_color(n):
    """번호 구간별 색상 (동행복권 규칙)"""
    if n <= 10:
        return "#FBC400"  # 노랑
    if n <= 20:
        return "#69C8F2"  # 파랑
    if n <= 30:
        return "#FF7272"  # 빨강
    if n <= 40:
        return "#AAAAAA"  # 회색
    return "#B0D840"      # 초록


def make_numbers():
    return [sorted(random.sample(range(1, 46), PICK)) for _ in range(SETS)]


def rounded_rect(canvas, x1, y1, x2, y2, r, **kw):
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r, x1, y1 + r, x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kw)


class RoundButton(tk.Canvas):
    """블랙 버튼, 모서리 12px"""

    def __init__(self, master, text, command, width=200, height=48):
        super().__init__(master, width=width, height=height,
                         bg="white", highlightthickness=0)
        rounded_rect(self, 1, 1, width - 1, height - 1, 12, fill="black")
        self.create_text(width / 2, height / 2, text=text, fill="white",
                         font=("Helvetica", 14, "bold"))
        self.bind("<Button-1>", lambda e: command())
        self.config(cursor="hand2")


class LottoApp:
    def __init__(self, root):
        self.root = root
        root.title("로또 번호 생성기")
        root.configure(bg="white")

        tk.Label(root, text="로또 번호 생성기", bg="white",
                 font=("Helvetica", 20, "bold")).pack(pady=(20, 4))
        self.date_label = tk.Label(root, text="", bg="white", fg="#666666",
                                   font=("Helvetica", 12))
        self.date_label.pack(pady=(0, 12))

        RoundButton(root, "번호 뽑기", self.draw).pack(pady=(0, 12))

        self.canvas = tk.Canvas(root, width=420, height=SETS * 56 + 10,
                                bg="white", highlightthickness=0)
        self.canvas.pack(padx=20, pady=(0, 20))

    def draw(self):
        now = datetime.now()
        self.date_label.config(text=now.strftime("%Y년 %m월 %d일 %H:%M:%S"))
        self.canvas.delete("all")
        for row, numbers in enumerate(make_numbers()):
            y = row * 56 + 30
            self.canvas.create_text(20, y, text="ABCDE"[row],
                                    font=("Helvetica", 14, "bold"))
            for i, n in enumerate(numbers):
                x = 70 + i * 60
                self.canvas.create_oval(x - 22, y - 22, x + 22, y + 22,
                                        fill=ball_color(n), outline="")
                self.canvas.create_text(x, y, text=str(n), fill="white",
                                        font=("Helvetica", 14, "bold"))


if __name__ == "__main__":
    root = tk.Tk()
    LottoApp(root)
    root.mainloop()
