import tkinter as tk


class BreakoutGame:
    WIDTH = 800
    HEIGHT = 600
    BALL_SIZE = 16
    PADDLE_WIDTH = 110
    PADDLE_HEIGHT = 14
    BRICK_ROWS = 5
    BRICK_COLUMNS = 10
    TICK_MS = 16

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("벽돌 깨기")
        self.root.resizable(False, False)

        self.canvas = tk.Canvas(
            root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#101827",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.canvas.focus_set()

        self.score = 0
        self.lives = 3
        self.state = "ready"
        self.ball_dx = 4.0
        self.ball_dy = -4.5
        self.keys_down: set[str] = set()
        self.bricks: dict[int, tuple[int, int, int, int]] = {}

        self._draw_scene()
        self._create_bricks()
        self._place_ball_and_paddle()
        self._show_message("스페이스바를 눌러 시작하세요")

        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        self.canvas.bind("<Motion>", self._on_mouse_move)

    def _draw_scene(self) -> None:
        self.canvas.create_text(
            24,
            27,
            text="벽돌 깨기",
            fill="#f8fafc",
            font=("맑은 고딕", 18, "bold"),
            anchor="w",
        )
        self.score_text = self.canvas.create_text(
            self.WIDTH // 2,
            29,
            text="점수: 0",
            fill="#cbd5e1",
            font=("맑은 고딕", 13),
        )
        self.lives_text = self.canvas.create_text(
            self.WIDTH - 24,
            29,
            text="목숨: 3",
            fill="#cbd5e1",
            font=("맑은 고딕", 13),
            anchor="e",
        )
        self.canvas.create_line(
            20, 54, self.WIDTH - 20, 54, fill="#334155", width=2
        )

    def _create_bricks(self) -> None:
        colors = ["#fb7185", "#fb923c", "#facc15", "#4ade80", "#38bdf8"]
        gap = 7
        side_margin = 30
        brick_width = (
            self.WIDTH - side_margin * 2 - gap * (self.BRICK_COLUMNS - 1)
        ) / self.BRICK_COLUMNS
        brick_height = 22
        top = 82

        self.bricks.clear()
        for row in range(self.BRICK_ROWS):
            for column in range(self.BRICK_COLUMNS):
                x1 = side_margin + column * (brick_width + gap)
                y1 = top + row * (brick_height + gap)
                x2 = x1 + brick_width
                y2 = y1 + brick_height
                brick_id = self.canvas.create_rectangle(
                    x1,
                    y1,
                    x2,
                    y2,
                    fill=colors[row],
                    outline="",
                    width=0,
                )
                self.bricks[brick_id] = (row, column, int(x1), int(y1))

    def _place_ball_and_paddle(self) -> None:
        paddle_y = self.HEIGHT - 48
        paddle_x = self.WIDTH / 2
        self.paddle = self.canvas.create_rectangle(
            paddle_x - self.PADDLE_WIDTH / 2,
            paddle_y,
            paddle_x + self.PADDLE_WIDTH / 2,
            paddle_y + self.PADDLE_HEIGHT,
            fill="#e2e8f0",
            outline="",
        )

        ball_x = self.WIDTH / 2
        ball_y = paddle_y - self.BALL_SIZE
        self.ball = self.canvas.create_oval(
            ball_x - self.BALL_SIZE / 2,
            ball_y - self.BALL_SIZE / 2,
            ball_x + self.BALL_SIZE / 2,
            ball_y + self.BALL_SIZE / 2,
            fill="#f8fafc",
            outline="",
        )

    def _show_message(self, message: str) -> None:
        self.canvas.delete("game_message")
        self.canvas.create_text(
            self.WIDTH / 2,
            self.HEIGHT / 2,
            text=message,
            fill="#f8fafc",
            font=("맑은 고딕", 18, "bold"),
            justify="center",
            tags="game_message",
        )

    def _on_key_press(self, event: tk.Event) -> None:
        self.keys_down.add(event.keysym.lower())
        if event.keysym == "space":
            if self.state in ("ready", "game_over", "won"):
                if self.state in ("game_over", "won"):
                    self._restart()
                self.state = "running"
                self.canvas.delete("game_message")
                self._update_game()

    def _on_key_release(self, event: tk.Event) -> None:
        self.keys_down.discard(event.keysym.lower())

    def _on_mouse_move(self, event: tk.Event) -> None:
        self._move_paddle(event.x)

    def _move_paddle(self, center_x: float) -> None:
        half_width = self.PADDLE_WIDTH / 2
        center_x = max(half_width + 10, min(self.WIDTH - half_width - 10, center_x))
        paddle_coords = self.canvas.coords(self.paddle)
        paddle_center_y = (paddle_coords[1] + paddle_coords[3]) / 2
        self.canvas.coords(
            self.paddle,
            center_x - half_width,
            paddle_center_y - self.PADDLE_HEIGHT / 2,
            center_x + half_width,
            paddle_center_y + self.PADDLE_HEIGHT / 2,
        )

    def _update_game(self) -> None:
        if self.state != "running":
            return

        paddle_coords = self.canvas.coords(self.paddle)
        if "left" in self.keys_down or "a" in self.keys_down:
            self._move_paddle(paddle_coords[0] - 8 + self.PADDLE_WIDTH / 2)
        if "right" in self.keys_down or "d" in self.keys_down:
            self._move_paddle(paddle_coords[2] + 8 - self.PADDLE_WIDTH / 2)

        self.canvas.move(self.ball, self.ball_dx, self.ball_dy)
        ball = self.canvas.coords(self.ball)
        left, top, right, bottom = ball

        if left <= 0 or right >= self.WIDTH:
            self.ball_dx = -self.ball_dx
        if top <= 56:
            self.ball_dy = abs(self.ball_dy)

        paddle = self.canvas.coords(self.paddle)
        if (
            self.ball_dy > 0
            and bottom >= paddle[1]
            and top <= paddle[3]
            and right >= paddle[0]
            and left <= paddle[2]
        ):
            hit_position = ((left + right) / 2 - (paddle[0] + paddle[2]) / 2) / (
                self.PADDLE_WIDTH / 2
            )
            self.ball_dx = hit_position * 5.5
            self.ball_dy = -max(3.5, 5.5 - abs(self.ball_dx) * 0.35)
            self.canvas.coords(
                self.ball,
                left,
                paddle[1] - self.BALL_SIZE,
                right,
                paddle[1],
            )

        if self._hit_brick():
            self.score += 10
            self.canvas.itemconfigure(self.score_text, text=f"점수: {self.score}")
            if not self.bricks:
                self.state = "won"
                self._show_message("모든 벽돌을 깼어요!\n스페이스바를 눌러 다시 시작")
                return

        if bottom >= self.HEIGHT:
            self.lives -= 1
            self.canvas.itemconfigure(self.lives_text, text=f"목숨: {self.lives}")
            if self.lives <= 0:
                self.state = "game_over"
                self._show_message(
                    f"게임 오버!  최종 점수: {self.score}\n"
                    "스페이스바를 눌러 다시 시작"
                )
                return

            self.state = "ready"
            self._reset_ball()
            self._show_message("공을 놓쳤어요!\n스페이스바를 눌러 계속")
            return

        self.root.after(self.TICK_MS, self._update_game)

    def _hit_brick(self) -> bool:
        ball = self.canvas.coords(self.ball)
        overlapping = self.canvas.find_overlapping(*ball)
        brick_id = next((item for item in overlapping if item in self.bricks), None)
        if brick_id is None:
            return False

        brick = self.canvas.coords(brick_id)
        overlap_x = min(ball[2], brick[2]) - max(ball[0], brick[0])
        overlap_y = min(ball[3], brick[3]) - max(ball[1], brick[1])
        if overlap_x < overlap_y:
            self.ball_dx = -self.ball_dx
        else:
            self.ball_dy = -self.ball_dy

        self.canvas.delete(brick_id)
        del self.bricks[brick_id]
        return True

    def _reset_ball(self) -> None:
        paddle = self.canvas.coords(self.paddle)
        center_x = (paddle[0] + paddle[2]) / 2
        ball_y = paddle[1] - self.BALL_SIZE
        self.canvas.coords(
            self.ball,
            center_x - self.BALL_SIZE / 2,
            ball_y - self.BALL_SIZE / 2,
            center_x + self.BALL_SIZE / 2,
            ball_y + self.BALL_SIZE / 2,
        )
        self.ball_dx = 4.0
        self.ball_dy = -4.5

    def _restart(self) -> None:
        self.canvas.delete(self.paddle)
        self.canvas.delete(self.ball)
        for brick_id in self.bricks:
            self.canvas.delete(brick_id)

        self.score = 0
        self.lives = 3
        self.canvas.itemconfigure(self.score_text, text="점수: 0")
        self.canvas.itemconfigure(self.lives_text, text="목숨: 3")
        self._create_bricks()
        self._place_ball_and_paddle()


def main() -> None:
    root = tk.Tk()
    BreakoutGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
