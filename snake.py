"""뱀 게임 (표준 라이브러리 tkinter 사용, 별도 설치 불필요)

조작법
  방향키 또는 WASD : 이동
  P               : 일시정지 / 계속
  R 또는 Enter     : 게임 오버 후 다시 시작
  Esc             : 종료
"""

import random
import tkinter as tk
from collections import deque

CELL_SIZE = 24
COLUMNS = 25
ROWS = 25
HUD_HEIGHT = 40

START_DELAY_MS = 150  # 시작 속도 (이동 간격)
MIN_DELAY_MS = 60  # 최고 속도
SPEEDUP_PER_FOOD_MS = 3  # 먹이 하나당 빨라지는 정도

COLOR_BACKGROUND = "#1e1e2e"
COLOR_HUD = "#11111b"
COLOR_TEXT = "#cdd6f4"
COLOR_SNAKE_HEAD = "#a6e3a1"
COLOR_SNAKE_BODY = "#40a02b"
COLOR_FOOD = "#f38ba8"

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

KEY_DIRECTIONS = {
    "up": UP,
    "down": DOWN,
    "left": LEFT,
    "right": RIGHT,
    "w": UP,
    "s": DOWN,
    "a": LEFT,
    "d": RIGHT,
}


class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("뱀 게임")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=COLUMNS * CELL_SIZE,
            height=ROWS * CELL_SIZE + HUD_HEIGHT,
            bg=COLOR_BACKGROUND,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.best_score = 0
        self.after_id = None

        self.root.bind("<KeyPress>", self.on_key)
        self.reset()

    def reset(self):
        """게임 상태를 초기화하고 게임 루프를 시작한다."""
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)

        center_x, center_y = COLUMNS // 2, ROWS // 2
        self.snake = deque((center_x - i, center_y) for i in range(3))
        self.direction = RIGHT
        self.pending_turns = deque()
        self.score = 0
        self.delay = START_DELAY_MS
        self.paused = False
        self.game_over = False
        self.won = False
        self.food = self.place_food()

        self.draw()
        self.after_id = self.root.after(self.delay, self.tick)

    def place_food(self):
        """뱀이 없는 칸 중 하나를 골라 먹이를 놓는다. 빈 칸이 없으면 None."""
        occupied = set(self.snake)
        empty = [
            (x, y)
            for x in range(COLUMNS)
            for y in range(ROWS)
            if (x, y) not in occupied
        ]
        return random.choice(empty) if empty else None

    def on_key(self, event):
        key = event.keysym.lower()

        if key == "escape":
            self.root.destroy()
        elif self.game_over:
            if key in ("r", "return"):
                self.reset()
        elif key == "p":
            self.toggle_pause()
        elif key in KEY_DIRECTIONS and not self.paused:
            self.queue_turn(KEY_DIRECTIONS[key])

    def queue_turn(self, new_direction):
        """입력을 큐에 넣어 한 틱에 한 번씩 방향을 바꾼다.

        한 틱 안에 키를 빠르게 두 번 눌러도 자기 몸으로 되돌아가지 않게 하고,
        연속 입력도 잃어버리지 않는다.
        """
        last = self.pending_turns[-1] if self.pending_turns else self.direction
        is_reverse = (new_direction[0] == -last[0] and new_direction[1] == -last[1])
        if new_direction != last and not is_reverse and len(self.pending_turns) < 2:
            self.pending_turns.append(new_direction)

    def toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        else:
            self.after_id = self.root.after(self.delay, self.tick)
        self.draw()

    def tick(self):
        self.step()
        self.draw()
        if self.game_over:
            self.after_id = None
        else:
            self.after_id = self.root.after(self.delay, self.tick)

    def step(self):
        """뱀을 한 칸 이동시키고 충돌과 먹이를 처리한다."""
        if self.pending_turns:
            self.direction = self.pending_turns.popleft()

        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        eating = new_head == self.food

        hit_wall = not (0 <= new_head[0] < COLUMNS and 0 <= new_head[1] < ROWS)
        # 먹지 않는 경우 꼬리는 이번 틱에 비켜나므로 꼬리 칸으로는 이동할 수 있다.
        body = list(self.snake) if eating else list(self.snake)[:-1]
        if hit_wall or new_head in body:
            self.end_game()
            return

        self.snake.appendleft(new_head)
        if eating:
            self.score += 1
            self.delay = max(MIN_DELAY_MS, self.delay - SPEEDUP_PER_FOOD_MS)
            self.food = self.place_food()
            if self.food is None:
                self.won = True
                self.end_game()
        else:
            self.snake.pop()

    def end_game(self):
        self.game_over = True
        self.best_score = max(self.best_score, self.score)

    def draw(self):
        self.canvas.delete("all")
        self.draw_hud()
        if self.food is not None:
            self.draw_food()
        self.draw_snake()

        if self.game_over:
            title = "승리!" if self.won else "게임 오버"
            self.draw_message(title, f"점수: {self.score}  |  R 또는 Enter: 다시 시작")
        elif self.paused:
            self.draw_message("일시정지", "P: 계속하기")

    def draw_hud(self):
        width = COLUMNS * CELL_SIZE
        self.canvas.create_rectangle(0, 0, width, HUD_HEIGHT, fill=COLOR_HUD, width=0)
        self.canvas.create_text(
            12, HUD_HEIGHT / 2, anchor="w", fill=COLOR_TEXT,
            font=("Malgun Gothic", 13, "bold"), text=f"점수: {self.score}",
        )
        self.canvas.create_text(
            width - 12, HUD_HEIGHT / 2, anchor="e", fill=COLOR_TEXT,
            font=("Malgun Gothic", 13), text=f"최고 점수: {self.best_score}",
        )

    def cell_box(self, cell, padding=1):
        x, y = cell
        left = x * CELL_SIZE + padding
        top = y * CELL_SIZE + HUD_HEIGHT + padding
        right = (x + 1) * CELL_SIZE - padding
        bottom = (y + 1) * CELL_SIZE + HUD_HEIGHT - padding
        return left, top, right, bottom

    def draw_food(self):
        self.canvas.create_oval(*self.cell_box(self.food, padding=3), fill=COLOR_FOOD, width=0)

    def draw_snake(self):
        for index, cell in enumerate(self.snake):
            color = COLOR_SNAKE_HEAD if index == 0 else COLOR_SNAKE_BODY
            self.canvas.create_rectangle(*self.cell_box(cell), fill=color, width=0)

    def draw_message(self, title, subtitle):
        center_x = COLUMNS * CELL_SIZE / 2
        center_y = ROWS * CELL_SIZE / 2 + HUD_HEIGHT
        self.canvas.create_rectangle(
            center_x - 200, center_y - 55, center_x + 200, center_y + 55,
            fill=COLOR_HUD, outline=COLOR_TEXT,
        )
        self.canvas.create_text(
            center_x, center_y - 15, fill=COLOR_TEXT,
            font=("Malgun Gothic", 22, "bold"), text=title,
        )
        self.canvas.create_text(
            center_x, center_y + 22, fill=COLOR_TEXT,
            font=("Malgun Gothic", 11), text=subtitle,
        )


def main():
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
