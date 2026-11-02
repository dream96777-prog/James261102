"""제비우스 스타일 종스크롤 슈팅 게임 (그래픽/사운드 모두 코드로 생성, 외부 파일 불필요)

설치 : pip install pygame
실행 : python xevious.py

조작
  방향키 / WASD : 이동
  Z / J         : 재퍼 (공중 공격, 누르고 있으면 연사)
  X / K         : 블래스터 (지상 폭격, 조준점 위치에 착탄)
  P             : 일시정지
  Enter         : 시작
  Esc           : 종료

팁
  - 조준점이 빨갛게 깜빡이면 그 아래에 지상 목표가 있다. 아무것도 안 보여도 숨겨진 것이다.
  - 숨겨진 솔 타워는 폭탄으로 드러낸 뒤 한 번 더 맞히면 2000점.
  - 숨겨진 스페셜 플래그는 폭탄으로 드러낸 뒤 위로 지나가면 1UP.
  - 바큐라(회전하는 금속판)는 파괴할 수 없다. 피해야 한다.
  - 레이더 돔(졸바크)이 화면에 있는 동안은 적 편대가 더 자주 온다.
"""
import math
import random
from array import array
from collections import deque
from dataclasses import dataclass

import pygame

WIDTH, HEIGHT = 480, 640
FPS = 60
SCROLL = 1.0          # 지형 스크롤 속도 (픽셀/프레임)
TILE = 16
SIGHT_DIST = 160      # 기체와 조준점 사이 거리
BOMB_FLIGHT = 24      # 폭탄 비행 시간 (프레임)
BOMB_RADIUS = 18      # 폭탄 착탄 판정 반경
AREA_LENGTH = 3000    # 보스 출현까지의 프레임 수
MAX_SPARIOS = 60      # 화면에 존재할 수 있는 적탄 수

WHITE = (240, 240, 240)
YELLOW = (250, 220, 60)
RED = (230, 50, 40)
ORANGE = (250, 140, 40)
CYAN = (90, 220, 240)
SILVER = (190, 195, 205)
STEEL = (120, 125, 140)
DARK = (50, 52, 62)

# 지역별 지형 색 : 숲, 풀밭, 흙, 강, 강둑, 도로
PALETTES = [
    ((22, 82, 40), (52, 118, 56), (124, 112, 66), (36, 84, 150), (150, 138, 88), (92, 92, 88)),
    ((70, 88, 34), (116, 124, 58), (156, 128, 74), (40, 104, 128), (172, 150, 96), (104, 96, 84)),
    ((30, 66, 70), (56, 100, 92), (98, 104, 100), (26, 58, 120), (126, 130, 122), (78, 82, 92)),
    ((96, 66, 40), (146, 104, 60), (182, 146, 90), (58, 90, 120), (196, 170, 118), (112, 92, 76)),
]


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def sign(v):
    return 1 if v >= 0 else -1


@dataclass
class Ctrl:
    """한 프레임의 입력 상태"""
    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False
    zap: bool = False
    bomb: bool = False


# ---------------------------------------------------------------- 사운드
class Sounds:
    """간단한 파형을 직접 합성한다. 오디오 장치가 없으면 조용히 무시한다."""

    def __init__(self):
        self.bank = {}
        try:
            pygame.mixer.init(22050, -16, 1, 512, allowedchanges=0)
        except pygame.error:
            return
        self.bank = {
            "zap": self.tone(1400, 500, 70, 0.16),
            "bomb": self.tone(900, 200, 300, 0.16),
            "air_hit": self.tone(0, 0, 130, 0.28, noise=True),
            "ground_hit": self.tone(0, 0, 280, 0.38, noise=True),
            "die": self.tone(0, 0, 800, 0.5, noise=True),
            "reveal": self.tone(500, 1600, 220, 0.25),
            "extend": self.tone(800, 1800, 500, 0.28),
            "boss": self.tone(150, 90, 900, 0.32),
        }

    @staticmethod
    def tone(f0, f1, ms, vol, noise=False):
        count = int(22050 * ms / 1000)
        samples = array("h")
        phase = 0.0
        value = 0.0
        for i in range(count):
            t = i / count
            env = (1 - t) ** 1.5 * vol
            if noise:
                if i % (2 + int(t * 8)) == 0:   # 뒤로 갈수록 낮아지는 잡음
                    value = random.uniform(-1, 1)
                s = value
            else:
                phase += (f0 + (f1 - f0) * t) / 22050
                s = 1.0 if phase % 1 < 0.5 else -1.0
            samples.append(int(s * env * 32000))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name):
        sound = self.bank.get(name)
        if sound:
            sound.play()


# ---------------------------------------------------------------- 지형
class Terrain:
    """사인파 합성으로 숲, 강, 도로를 만들며 한 줄씩 끝없이 생성한다."""

    def __init__(self):
        self.rng = random.Random()
        self.phase = [self.rng.uniform(0, 100) for _ in range(6)]
        self.palette = PALETTES[0]
        self.row_no = 0
        self.offset = 0.0
        self.cols = WIDTH // TILE
        self.rows = deque()
        for _ in range(HEIGHT // TILE + 2):
            self.rows.appendleft(self.make_row())

    def make_row(self):
        r = self.row_no
        self.row_no += 1
        p = self.phase
        pal = self.palette
        surf = pygame.Surface((WIDTH, TILE)).convert()
        river_on = math.sin(r * 0.009 + p[5]) > -0.25
        center = self.cols / 2 + 9 * math.sin(r * 0.03 + p[3]) + 4 * math.sin(r * 0.011 + p[4])
        half = 2.2 + math.sin(r * 0.05)
        for c in range(self.cols):
            n = (math.sin(c * 0.21 + r * 0.08 + p[0])
                 + math.sin(c * 0.07 - r * 0.13 + p[1])
                 + math.sin((c + r) * 0.05 + p[2]))
            d = abs(c - center)
            x = c * TILE
            if river_on and d < half:
                self.water(surf, x, pal[3])
            elif river_on and d < half + 1:
                surf.fill(pal[4], (x, 0, TILE, TILE))
            elif (c - r // 2) % 47 < 1:
                surf.fill(pal[5], (x, 0, TILE, TILE))
            elif n > 0.45:
                self.forest(surf, x, pal[0], pal[1])
            elif n > -0.7:
                self.speckle(surf, x, pal[1], 2)
            else:
                self.speckle(surf, x, pal[2], 3)
        return surf

    def water(self, surf, x, color):
        surf.fill(color, (x, 0, TILE, TILE))
        light = tuple(min(255, v + 34) for v in color)
        if self.rng.random() < 0.3:
            surf.fill(light, (x + self.rng.randrange(TILE - 6), self.rng.randrange(TILE), 6, 1))

    def forest(self, surf, x, dark, light):
        surf.fill(dark, (x, 0, TILE, TILE))
        for _ in range(3):
            px = x + self.rng.randrange(TILE)
            py = self.rng.randrange(TILE)
            pygame.draw.circle(surf, light, (px, py), self.rng.randint(1, 3))

    def speckle(self, surf, x, color, count):
        surf.fill(color, (x, 0, TILE, TILE))
        tint = tuple(max(0, v - 18) for v in color)
        for _ in range(count):
            surf.fill(tint, (x + self.rng.randrange(TILE), self.rng.randrange(TILE), 2, 2))

    def update(self):
        self.offset += SCROLL
        while self.offset >= TILE:
            self.offset -= TILE
            self.rows.pop()
            self.rows.appendleft(self.make_row())

    def draw(self, screen):
        y = self.offset - TILE
        for row in self.rows:
            screen.blit(row, (0, int(y)))
            y += TILE


# ---------------------------------------------------------------- 스프라이트
def make_player_sprite():
    """은색 전투기 솔바루"""
    s = pygame.Surface((34, 38), pygame.SRCALPHA)
    pygame.draw.polygon(s, STEEL, [(17, 8), (33, 30), (24, 28), (17, 36), (10, 28), (1, 30)])
    pygame.draw.polygon(s, SILVER, [(17, 0), (24, 22), (21, 34), (13, 34), (10, 22)])
    pygame.draw.polygon(s, WHITE, [(17, 2), (20, 18), (14, 18)])
    pygame.draw.polygon(s, (40, 70, 170), [(17, 12), (20, 22), (14, 22)])
    pygame.draw.line(s, RED, (5, 28), (11, 24), 2)
    pygame.draw.line(s, RED, (29, 28), (23, 24), 2)
    return s


def make_shadow(radius):
    s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 80), s.get_rect())
    return s


# ---------------------------------------------------------------- 탄과 효과
class Shot:
    """재퍼 탄"""

    def __init__(self, x, y):
        self.x, self.y = x, y
        self.alive = True

    def update(self):
        self.y -= 13
        if self.y < -12:
            self.alive = False

    def draw(self, screen):
        pygame.draw.line(screen, WHITE, (self.x, self.y), (self.x, self.y + 10), 3)
        pygame.draw.line(screen, CYAN, (self.x, self.y + 10), (self.x, self.y + 16), 1)


class Bomb:
    """블래스터 폭탄 : 투하 시점의 조준점을 향해 날아가며, 목표 지점은 지형과 함께 흘러간다."""

    def __init__(self, x, y, tx, ty):
        self.sx, self.sy = x, y
        self.tx, self.ty = tx, ty
        self.t = 0
        self.alive = True

    def update(self, game):
        self.t += 1
        self.ty += SCROLL
        if self.t >= BOMB_FLIGHT:
            self.alive = False
            game.land_bomb(self.tx, self.ty)

    def draw(self, screen):
        k = self.t / BOMB_FLIGHT
        x = self.sx + (self.tx - self.sx) * k
        y = self.sy + (self.ty - self.sy) * k
        r = max(2, int(6 - 4 * k))
        pygame.draw.circle(screen, DARK, (int(x), int(y)), r + 1)
        pygame.draw.circle(screen, ORANGE, (int(x), int(y)), r)


class Spario:
    """적탄 스파리오"""

    def __init__(self, x, y, angle, speed):
        self.x, self.y = x, y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.t = random.randrange(20)
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.t += 1
        if not (-12 < self.x < WIDTH + 12 and -12 < self.y < HEIGHT + 12):
            self.alive = False

    def draw(self, screen):
        pos = (int(self.x), int(self.y))
        color = WHITE if self.t // 4 % 2 else ORANGE
        pygame.draw.circle(screen, RED, pos, 6)
        pygame.draw.circle(screen, color, pos, 4)


class Explosion:
    def __init__(self, x, y, size=26, ground=False):
        self.x, self.y = x, y
        self.size = size
        self.ground = ground
        self.t = 0
        self.life = 24
        self.alive = True
        self.sparks = [(random.uniform(0, math.tau), random.uniform(0.5, 1.0)) for _ in range(10)]

    def update(self):
        self.t += 1
        if self.ground:
            self.y += SCROLL
        if self.t >= self.life:
            self.alive = False

    def draw(self, screen):
        k = self.t / self.life
        r = int(self.size * k)
        pos = (int(self.x), int(self.y))
        if k < 0.55:
            pygame.draw.circle(screen, YELLOW if k < 0.25 else ORANGE, pos, max(1, r))
            pygame.draw.circle(screen, WHITE, pos, max(1, r // 2))
        else:
            pygame.draw.circle(screen, ORANGE, pos, max(1, r), 2)
        for angle, rate in self.sparks:
            d = self.size * 1.3 * k * rate
            x = self.x + math.cos(angle) * d
            y = self.y + math.sin(angle) * d
            screen.fill(YELLOW if k < 0.6 else RED, (int(x), int(y), 3, 3))


class Crater:
    """파괴된 지상 목표 자리에 남는 흔적"""

    def __init__(self, x, y, r):
        self.x, self.y, self.r = x, y, r
        self.alive = True

    def update(self):
        self.y += SCROLL
        if self.y > HEIGHT + 30:
            self.alive = False

    def draw(self, screen):
        rect = pygame.Rect(0, 0, self.r * 2, int(self.r * 1.5))
        rect.center = (int(self.x), int(self.y))
        pygame.draw.ellipse(screen, (28, 26, 22), rect)
        pygame.draw.ellipse(screen, (70, 62, 48), rect, 2)


# ---------------------------------------------------------------- 공중 적
AIR_STATS = {
    "toroid": (14, 30),
    "torkan": (15, 50),
    "kapi": (15, 150),
    "zoshi": (13, 100),
    "bacura": (20, 0),
}


class AirEnemy:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = x, y
        self.r, self.score = AIR_STATS[kind]
        self.invulnerable = kind == "bacura"
        self.vx = self.vy = 0.0
        self.phase = 0
        self.timer = 0
        self.spin = random.uniform(0, math.tau)
        self.stop_y = random.randint(70, 250)
        self.alive = True

    def update(self, game):
        getattr(self, "move_" + self.kind)(game)
        self.x += self.vx
        self.y += self.vy
        self.timer += 1
        self.spin += 0.16
        if (self.x < -70 or self.x > WIDTH + 70 or self.y > HEIGHT + 60 or self.y < -600
                or (self.phase > 0 and self.y < -40)):
            self.alive = False

    def move_toroid(self, game):
        p = game.player
        if self.phase == 0:
            self.vy = 2.6
            self.vx = max(-1.6, min(1.6, (p.x - self.x) * 0.02))
            if self.y > p.y - 190:
                self.phase = 1
                self.vx = 3.6 * sign(self.x - p.x)
                if random.random() < 0.25 + game.area * 0.08:
                    game.fire_at_player(self.x, self.y)
        else:
            self.vy -= 0.09

    def move_torkan(self, game):
        if self.phase == 0:
            self.vy = 3.0
            if self.y >= self.stop_y:
                self.phase, self.timer, self.vy = 1, 0, 0.0
        elif self.phase == 1:
            if self.timer == 40:
                game.fire_at_player(self.x, self.y)
            if self.timer >= 75:
                self.phase = 2
                self.vy = -3.0
                self.vx = random.choice((-1.5, 1.5))

    def move_kapi(self, game):
        p = game.player
        if self.phase == 0:
            if self.timer == 0:
                angle = math.atan2(p.y - self.y, p.x - self.x)
                self.vx = math.cos(angle) * 5
                self.vy = math.sin(angle) * 5
            if self.y > p.y - 140:
                self.phase = 1
                self.turn = sign(self.x - p.x)
        else:
            self.vy -= 0.28
            self.vx += 0.2 * self.turn

    def move_zoshi(self, game):
        p = game.player
        if self.timer < 360:
            angle = math.atan2(p.y - self.y, p.x - self.x)
            self.vx += (math.cos(angle) * 2.7 - self.vx) * 0.04
            self.vy += (math.sin(angle) * 2.7 - self.vy) * 0.04
            if self.timer % 90 == 70:
                game.fire_at_player(self.x, self.y)
        else:
            self.vy += 0.05

    def move_bacura(self, game):
        self.vy = 1.7

    def draw(self, screen):
        pos = (int(self.x), int(self.y))
        if self.kind == "toroid":
            w = max(3, int(abs(math.cos(self.spin)) * 28))
            rect = pygame.Rect(0, 0, w, 28)
            rect.center = pos
            pygame.draw.ellipse(screen, SILVER, rect)
            if w > 12:
                inner = rect.inflate(-10, -12)
                pygame.draw.ellipse(screen, DARK, inner)
            pygame.draw.ellipse(screen, STEEL, rect, 2)
        elif self.kind == "torkan":
            x, y = pos
            pygame.draw.polygon(screen, (50, 90, 200), [(x - 16, y - 8), (x + 16, y - 8), (x, y + 16)])
            pygame.draw.polygon(screen, SILVER, [(x - 8, y - 12), (x + 8, y - 12), (x, y + 6)])
            pygame.draw.circle(screen, RED if self.phase == 1 else CYAN, (x, y - 4), 4)
        elif self.kind == "kapi":
            angle = math.atan2(self.vy, self.vx) if (self.vx or self.vy) else math.pi / 2
            pts = [(18, 0), (-13, 13), (-6, 0), (-13, -13)]
            ca, sa = math.cos(angle), math.sin(angle)
            poly = [(self.x + a * ca - b * sa, self.y + a * sa + b * ca) for a, b in pts]
            pygame.draw.polygon(screen, (210, 170, 60), poly)
            pygame.draw.polygon(screen, (110, 70, 20), poly, 2)
        elif self.kind == "zoshi":
            poly = []
            for i in range(8):
                r = 16 if i % 2 == 0 else 6
                a = self.spin + i * math.pi / 4
                poly.append((self.x + math.cos(a) * r, self.y + math.sin(a) * r))
            pygame.draw.polygon(screen, (200, 50, 70), poly)
            pygame.draw.circle(screen, YELLOW, pos, 4)
        elif self.kind == "bacura":
            h = max(3, int(abs(math.sin(self.spin * 0.5)) * 34))
            rect = pygame.Rect(0, 0, 40, h)
            rect.center = pos
            pygame.draw.rect(screen, SILVER, rect)
            pygame.draw.rect(screen, WHITE, (rect.x, rect.y, rect.w, max(1, h // 4)))
            pygame.draw.rect(screen, DARK, rect, 2)


# ---------------------------------------------------------------- 지상 적
GROUND_STATS = {        # 반경, 점수, 내구도
    "barra": (16, 100, 1),
    "zolbak": (15, 200, 1),
    "logram": (14, 300, 1),
    "domogram": (15, 800, 1),
    "derota": (20, 1000, 2),
    "sol": (15, 2000, 1),
    "flag": (12, 1000, 1),
}


class GroundEnemy:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = x, y
        self.r, self.score, self.hp = GROUND_STATS[kind]
        self.hidden = kind in ("sol", "flag")
        self.timer = random.randrange(60)
        self.vx = random.choice((-0.8, 0.8)) if kind == "domogram" else 0.0
        self.flash = 0
        self.alive = True

    def update(self, game):
        self.y += SCROLL
        self.x += self.vx
        if self.x < 24 or self.x > WIDTH - 24:
            self.vx = -self.vx
        self.timer += 1
        if self.flash:
            self.flash -= 1
        if self.y > HEIGHT + 30:
            self.alive = False
            return
        if self.y > 0 and not self.hidden:
            self.try_fire(game)

    def try_fire(self, game):
        period = {"logram": 130, "domogram": 110, "derota": 45, "sol": 150}.get(self.kind)
        if not period:
            return
        period = max(period // 2, period - game.area * 8)
        if self.timer % period == 0:
            game.fire_at_player(self.x, self.y)

    def bomb_hit(self, game):
        if self.hidden:
            self.hidden = False
            game.sounds.play("reveal")
            return
        if self.kind == "flag":
            return
        self.hp -= 1
        self.flash = 8
        if self.hp <= 0:
            self.alive = False
            game.add_score(self.score, self.x, self.y)
            game.explode(self.x, self.y, self.r + 14, ground=True)
            game.craters.append(Crater(self.x, self.y, self.r))
            game.sounds.play("ground_hit")

    def draw(self, screen):
        if self.hidden:
            return
        x, y = int(self.x), int(self.y)
        getattr(self, "draw_" + self.kind)(screen, x, y)
        if self.flash:
            pygame.draw.circle(screen, WHITE, (x, y), self.r, 2)

    def draw_barra(self, s, x, y):
        pygame.draw.polygon(s, (170, 170, 176), [(x, y), (x - 16, y - 16), (x + 16, y - 16)])
        pygame.draw.polygon(s, (130, 130, 138), [(x, y), (x + 16, y - 16), (x + 16, y + 16)])
        pygame.draw.polygon(s, (90, 90, 100), [(x, y), (x - 16, y + 16), (x + 16, y + 16)])
        pygame.draw.polygon(s, (150, 150, 158), [(x, y), (x - 16, y - 16), (x - 16, y + 16)])

    def draw_zolbak(self, s, x, y):
        pygame.draw.circle(s, DARK, (x, y), 15)
        pygame.draw.circle(s, (190, 180, 150), (x, y), 12)
        a = self.timer * 0.12
        pygame.draw.line(s, RED, (x, y), (x + math.cos(a) * 12, y + math.sin(a) * 12), 3)
        pygame.draw.circle(s, DARK, (x, y), 3)

    def draw_logram(self, s, x, y):
        pygame.draw.circle(s, DARK, (x, y), 14)
        pygame.draw.circle(s, (104, 110, 90), (x, y), 11)
        opening = self.timer % 130 < 30
        pygame.draw.circle(s, RED if opening else DARK, (x, y), 5)

    def draw_domogram(self, s, x, y):
        pygame.draw.rect(s, DARK, (x - 15, y - 11, 30, 22), border_radius=4)
        pygame.draw.rect(s, (100, 120, 80), (x - 12, y - 8, 24, 16), border_radius=3)
        pygame.draw.circle(s, (160, 170, 120), (x, y), 6)
        for i in range(-12, 13, 6):
            s.fill(STEEL, (x + i - 1, y - 13, 3, 3))
            s.fill(STEEL, (x + i - 1, y + 10, 3, 3))

    def draw_derota(self, s, x, y):
        poly = [(x + math.cos(i * math.pi / 4 + 0.39) * 20, y + math.sin(i * math.pi / 4 + 0.39) * 20)
                for i in range(8)]
        pygame.draw.polygon(s, (120, 80, 70), poly)
        pygame.draw.polygon(s, DARK, poly, 2)
        pygame.draw.circle(s, DARK, (x, y), 10)
        pygame.draw.circle(s, RED if self.timer % 45 < 12 else ORANGE, (x, y), 5)

    def draw_sol(self, s, x, y):
        pygame.draw.circle(s, DARK, (x, y), 15)
        pygame.draw.circle(s, (210, 190, 90), (x, y), 12)
        pygame.draw.circle(s, DARK, (x, y), 8, 2)
        pygame.draw.circle(s, RED, (x, y), 3)

    def draw_flag(self, s, x, y):
        pygame.draw.line(s, WHITE, (x - 8, y - 14), (x - 8, y + 14), 3)
        color = YELLOW if self.timer // 10 % 2 else ORANGE
        pygame.draw.polygon(s, color, [(x - 6, y - 14), (x + 14, y - 7), (x - 6, y)])


# ---------------------------------------------------------------- 보스
class Boss:
    """거대 모선 안도어 제네시스 : 폭탄으로만 공격할 수 있다."""

    def __init__(self, area):
        self.x, self.y = WIDTH / 2, -130.0
        self.t = 0
        self.core_hp = 6 + area * 2
        self.turrets = [[-58, -58, True], [58, -58, True], [-58, 58, True], [58, 58, True]]
        self.flash = 0
        self.dying = 0

    def targets(self):
        """조준점 판정용 좌표 목록"""
        pts = [(self.x + t[0], self.y + t[1]) for t in self.turrets if t[2]]
        pts.append((self.x, self.y))
        return pts

    def update(self, game):
        self.t += 1
        if self.flash:
            self.flash -= 1
        if self.dying:
            self.dying -= 1
            self.y += 0.6
            if self.dying % 7 == 0:
                game.explode(self.x + random.randint(-90, 90), self.y + random.randint(-90, 90), 34)
                game.sounds.play("air_hit")
            return
        self.y = min(150.0, self.y + 1.0)
        self.x = WIDTH / 2 + math.sin(self.t * 0.012) * 90
        if self.y < 40:
            return
        rate = max(50, 100 - game.area * 8)
        for i, t in enumerate(self.turrets):
            if t[2] and (self.t + i * 23) % rate == 0:
                game.fire_at_player(self.x + t[0], self.y + t[1])
        if self.t % 170 == 0:
            for off in (-0.3, 0, 0.3):
                game.fire_at_player(self.x, self.y, off)

    def bomb_hit(self, x, y, game):
        if self.dying:
            return
        for t in self.turrets:
            if t[2] and dist(x, y, self.x + t[0], self.y + t[1]) < 16 + BOMB_RADIUS:
                t[2] = False
                game.add_score(1000, self.x + t[0], self.y + t[1])
                game.explode(self.x + t[0], self.y + t[1], 28)
                game.sounds.play("ground_hit")
        if dist(x, y, self.x, self.y) < 20 + BOMB_RADIUS:
            self.core_hp -= 1
            self.flash = 8
            game.sounds.play("ground_hit")
            if self.core_hp <= 0:
                self.dying = 110
                game.sparios.clear()
                game.add_score(5000, self.x, self.y)

    def finished(self):
        return self.core_hp <= 0 and self.dying == 0

    def draw(self, s):
        x, y = int(self.x), int(self.y)
        hull = [(x + math.cos(i * math.pi / 4 + 0.39) * 100, y + math.sin(i * math.pi / 4 + 0.39) * 100)
                for i in range(8)]
        shade = [(a + 8, b + 12) for a, b in hull]
        pygame.draw.polygon(s, (20, 22, 26), shade)
        pygame.draw.polygon(s, (108, 112, 122), hull)
        pygame.draw.polygon(s, (60, 62, 72), hull, 4)
        pygame.draw.circle(s, (84, 88, 100), (x, y), 66)
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(s, (60, 62, 72), (x + math.cos(a) * 40, y + math.sin(a) * 40),
                             (x + math.cos(a) * 92, y + math.sin(a) * 92), 3)
        for tx, ty, on in self.turrets:
            pos = (x + tx, y + ty)
            if on:
                pygame.draw.circle(s, DARK, pos, 16)
                pygame.draw.circle(s, (170, 130, 70), pos, 12)
                pygame.draw.circle(s, RED, pos, 5)
            else:
                pygame.draw.circle(s, (34, 30, 28), pos, 13)
        pygame.draw.circle(s, DARK, (x, y), 24)
        core = WHITE if self.flash else (220, 60 + (self.t * 4) % 120, 50)
        pygame.draw.circle(s, core, (x, y), 17)


# ---------------------------------------------------------------- 플레이어
class Player:
    def __init__(self):
        self.sprite = make_player_sprite()
        self.shadow = pygame.mask.from_surface(self.sprite).to_surface(
            setcolor=(0, 0, 0, 90), unsetcolor=(0, 0, 0, 0))
        self.reset()

    def reset(self):
        self.x, self.y = WIDTH / 2, HEIGHT - 80.0
        self.invincible = 150
        self.zap_cool = 0
        self.bomb_cool = 0

    @property
    def sight(self):
        return self.x, self.y - SIGHT_DIST

    def update(self, ctrl, game):
        dx = ctrl.right - ctrl.left
        dy = ctrl.down - ctrl.up
        speed = 2.6 if dx and dy else 3.6
        self.x = max(18, min(WIDTH - 18, self.x + dx * speed))
        self.y = max(SIGHT_DIST + 20, min(HEIGHT - 26, self.y + dy * speed))
        self.zap_cool = max(0, self.zap_cool - 1)
        self.bomb_cool = max(0, self.bomb_cool - 1)
        if self.invincible:
            self.invincible -= 1
        if ctrl.zap and not self.zap_cool:
            self.zap_cool = 9
            game.shots.append(Shot(self.x - 7, self.y - 12))
            game.shots.append(Shot(self.x + 7, self.y - 12))
            game.sounds.play("zap")
        if ctrl.bomb and not self.bomb_cool:
            self.bomb_cool = BOMB_FLIGHT + 4
            game.bombs.append(Bomb(self.x, self.y - 10, *self.sight))
            game.sounds.play("bomb")

    def draw(self, screen):
        if self.invincible and self.invincible // 4 % 2:
            return
        rect = self.sprite.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(self.shadow, rect.move(16, 24))
        screen.blit(self.sprite, rect)


# ---------------------------------------------------------------- 게임 본체
class Game:
    def __init__(self, sounds=None):
        self.sounds = sounds or Sounds()
        self.font = pygame.font.Font(None, 26)
        self.big = pygame.font.Font(None, 58)
        self.logo = pygame.font.Font(None, 92)
        self.terrain = Terrain()
        self.shadows = {r: make_shadow(r) for r in set(v[0] for v in AIR_STATS.values())}
        self.hi_score = 20000
        self.state = "title"
        self.tick = 0
        self.player = Player()
        self.new_game()
        self.state = "title"

    def new_game(self):
        self.state = "play"
        self.score = 0
        self.lives = 2
        self.next_extend = 20000
        self.area = 1
        self.terrain.palette = PALETTES[0]
        self.player.reset()
        self.clear_field()
        self.start_area()

    def clear_field(self):
        self.shots, self.bombs, self.sparios = [], [], []
        self.air, self.ground, self.explosions, self.craters = [], [], [], []
        self.popups = []
        self.boss = None
        self.dead_timer = 0

    def start_area(self):
        self.area_frame = 0
        self.air_timer = 120
        self.ground_timer = 90
        self.banner = 150
        self.flag_at = random.randint(600, AREA_LENGTH - 400)
        self.sol_timer = random.randint(350, 800)
        self.terrain.palette = PALETTES[(self.area - 1) % len(PALETTES)]

    # ---- 공용 동작
    def fire_at_player(self, x, y, offset=0.0):
        p = self.player
        if len(self.sparios) >= MAX_SPARIOS or self.dead_timer or dist(x, y, p.x, p.y) < 70:
            return
        angle = math.atan2(p.y - y, p.x - x) + offset
        self.sparios.append(Spario(x, y, angle, min(5.0, 2.4 + 0.25 * self.area)))

    def explode(self, x, y, size=26, ground=False):
        self.explosions.append(Explosion(x, y, size, ground))

    def add_score(self, value, x=None, y=None):
        self.score += value
        self.hi_score = max(self.hi_score, self.score)
        if x is not None and value >= 500:
            self.popups.append([x, y, str(value), 50])
        if self.score >= self.next_extend:
            self.next_extend += 60000
            self.lives += 1
            self.sounds.play("extend")

    def land_bomb(self, x, y):
        self.explode(x, y, 14, ground=True)
        for g in self.ground:
            if g.alive and dist(x, y, g.x, g.y) < g.r + BOMB_RADIUS:
                g.bomb_hit(self)
        if self.boss:
            self.boss.bomb_hit(x, y, self)

    def sight_locked(self):
        sx, sy = self.player.sight
        for g in self.ground:
            if dist(sx, sy, g.x, g.y) < g.r + 10 and not (g.kind == "flag" and not g.hidden):
                return True
        if self.boss and not self.boss.dying:
            return any(dist(sx, sy, x, y) < 26 for x, y in self.boss.targets())
        return False

    # ---- 적 생성
    def spawn_air(self):
        a = self.area
        table = [("toroid", 6), ("torkan", 4), ("kapi", 2 + min(a, 3)),
                 ("zoshi", min(a, 4)), ("bacura", 1 + min(a, 3))]
        kind = random.choices([k for k, _ in table], [w for _, w in table])[0]
        if kind == "toroid":
            x = random.randint(50, WIDTH - 50)
            for i in range(random.randint(3, 5)):
                self.air.append(AirEnemy("toroid", x, -30 - i * 44))
        elif kind == "torkan":
            for _ in range(random.randint(1, 1 + min(a, 3))):
                self.air.append(AirEnemy("torkan", random.randint(40, WIDTH - 40),
                                         -30 - random.randint(0, 80)))
        elif kind == "kapi":
            x = random.randint(40, WIDTH - 120)
            for i in range(3):
                self.air.append(AirEnemy("kapi", x + i * 40, -30 - i * 30))
        elif kind == "zoshi":
            for _ in range(random.randint(2, 2 + min(a, 2))):
                if random.random() < 0.5:
                    self.air.append(AirEnemy("zoshi", random.randint(30, WIDTH - 30), -30))
                else:
                    self.air.append(AirEnemy("zoshi", random.choice((-30, WIDTH + 30)),
                                             random.randint(30, 220)))
        else:
            x = random.randint(40, WIDTH - 180)
            for i in range(random.randint(2, 3)):
                self.air.append(AirEnemy("bacura", x + i * 62, -30))

    def spawn_ground(self):
        table = [("barra", 5), ("logram", 4), ("zolbak", 2), ("domogram", 2),
                 ("derota", 1 if self.area == 1 else 2)]
        kind = random.choices([k for k, _ in table], [w for _, w in table])[0]
        x = random.randint(30, WIDTH - 30)
        if kind == "barra":
            for i in range(random.randint(1, 4)):
                self.ground.append(GroundEnemy("barra", min(x + i * 38, WIDTH - 20), -30))
        else:
            self.ground.append(GroundEnemy(kind, x, -30))

    def run_spawners(self):
        self.air_timer -= 1
        if self.air_timer <= 0:
            self.spawn_air()
            interval = max(60, 130 - self.area * 12)
            if any(g.kind == "zolbak" for g in self.ground):
                interval = int(interval * 0.6)
            if self.boss:
                interval *= 3
            self.air_timer = interval
        if self.boss:
            return
        self.ground_timer -= 1
        if self.ground_timer <= 0:
            self.spawn_ground()
            self.ground_timer = random.randint(70, 130)
        self.sol_timer -= 1
        if self.sol_timer <= 0:
            self.ground.append(GroundEnemy("sol", random.randint(40, WIDTH - 40), -30))
            self.sol_timer = random.randint(700, 1200)
        if self.area_frame == self.flag_at:
            self.ground.append(GroundEnemy("flag", random.randint(40, WIDTH - 40), -30))

    # ---- 프레임 갱신
    def update(self, ctrl):
        self.tick += 1
        self.terrain.update()
        if self.state != "play":
            return
        if self.banner:
            self.banner -= 1
        self.area_frame += 1
        if self.area_frame == AREA_LENGTH and not self.boss:
            self.boss = Boss(self.area)
            self.sounds.play("boss")
        self.run_spawners()

        if self.dead_timer:
            self.dead_timer -= 1
            if self.dead_timer == 0:
                if self.lives < 0:
                    self.state = "gameover"
                else:
                    self.player.reset()
        else:
            self.player.update(ctrl, self)

        for group in (self.shots, self.sparios, self.explosions, self.craters):
            for obj in group:
                obj.update()
        for bomb in self.bombs:
            bomb.update(self)
        for group in (self.air, self.ground):
            for obj in group:
                obj.update(self)
        if self.boss:
            self.boss.update(self)
            if self.boss.finished():
                self.boss = None
                self.area += 1
                self.start_area()

        self.collide()
        for popup in self.popups:
            popup[1] -= 0.5
            popup[3] -= 1
        self.popups = [p for p in self.popups if p[3] > 0]
        for name in ("shots", "bombs", "sparios", "air", "ground", "explosions", "craters"):
            setattr(self, name, [o for o in getattr(self, name) if o.alive])

    def collide(self):
        for shot in self.shots:
            for e in self.air:
                if e.alive and shot.alive and dist(shot.x, shot.y, e.x, e.y) < e.r + 6:
                    shot.alive = False
                    if e.invulnerable:
                        break
                    e.alive = False
                    self.add_score(e.score, e.x, e.y)
                    self.explode(e.x, e.y, e.r + 12)
                    self.sounds.play("air_hit")
                    break

        p = self.player
        if self.dead_timer:
            return
        for g in self.ground:
            if g.kind == "flag" and not g.hidden and g.alive and dist(p.x, p.y, g.x, g.y) < 26:
                g.alive = False
                self.lives += 1
                self.add_score(g.score, g.x, g.y)
                self.sounds.play("extend")
        if p.invincible:
            return
        for b in self.sparios:
            if dist(p.x, p.y, b.x, b.y) < 10:
                b.alive = False
                self.kill_player()
                return
        for e in self.air:
            if e.alive and dist(p.x, p.y, e.x, e.y) < e.r + 7:
                self.kill_player()
                return

    def kill_player(self):
        p = self.player
        self.explode(p.x, p.y, 50)
        self.explode(p.x - 14, p.y + 8, 30)
        self.explode(p.x + 14, p.y - 8, 30)
        self.sounds.play("die")
        self.lives -= 1
        self.dead_timer = 130
        self.sparios.clear()
        self.bombs.clear()

    # ---- 그리기
    def text(self, screen, font, msg, color, center=None, topleft=None):
        img = font.render(msg, True, color)
        shade = font.render(msg, True, (0, 0, 0))
        rect = img.get_rect()
        if center:
            rect.center = center
        else:
            rect.topleft = topleft
        screen.blit(shade, rect.move(2, 2))
        screen.blit(img, rect)

    def draw_sight(self, screen):
        x, y = self.player.sight
        x, y = int(x), int(y)
        locked = self.sight_locked()
        color = RED if locked and self.tick // 4 % 2 else (WHITE if not locked else YELLOW)
        pygame.draw.rect(screen, color, (x - 14, y - 14, 28, 28), 2)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            pygame.draw.line(screen, color, (x + dx * 6, y + dy * 6), (x + dx * 20, y + dy * 20), 2)

    def draw_field(self, screen):
        self.terrain.draw(screen)
        for c in self.craters:
            c.draw(screen)
        for g in self.ground:
            g.draw(screen)
        if self.boss:
            self.boss.draw(screen)
        for e in self.air:
            screen.blit(self.shadows[e.r], (int(e.x - e.r + 16), int(e.y - e.r + 24)))
        for b in self.bombs:
            b.draw(screen)
        for e in self.air:
            e.draw(screen)
        for s in self.shots:
            s.draw(screen)
        if not self.dead_timer:
            self.draw_sight(screen)
            self.player.draw(screen)
        for b in self.sparios:
            b.draw(screen)
        for ex in self.explosions:
            ex.draw(screen)

    def draw_hud(self, screen):
        self.text(screen, self.font, f"SCORE {self.score:07d}", WHITE, topleft=(10, 8))
        self.text(screen, self.font, f"HI {self.hi_score:07d}", YELLOW, center=(WIDTH / 2 + 60, 17))
        self.text(screen, self.font, f"AREA {self.area}", CYAN, topleft=(WIDTH - 76, 8))
        icon = pygame.transform.smoothscale(self.player.sprite, (17, 19))
        for i in range(max(0, self.lives)):
            screen.blit(icon, (10 + i * 22, HEIGHT - 28))
        for x, y, msg, _ in self.popups:
            self.text(screen, self.font, msg, YELLOW, center=(int(x), int(y)))
        if self.banner:
            self.text(screen, self.big, f"AREA {self.area}", WHITE, center=(WIDTH / 2, HEIGHT / 2 - 40))
        if self.boss and self.boss.y < 40:
            if self.tick // 12 % 2:
                self.text(screen, self.big, "WARNING", RED, center=(WIDTH / 2, HEIGHT / 2))

    def draw(self, screen):
        if self.state == "title":
            self.terrain.draw(screen)
            self.text(screen, self.logo, "XEVIOUS", SILVER, center=(WIDTH / 2, 170))
            self.text(screen, self.font, "STYLE VERTICAL SHOOTER", CYAN, center=(WIDTH / 2, 225))
            lines = ["ARROWS / WASD   MOVE", "Z / J   ZAPPER (AIR)", "X / K   BLASTER (GROUND)", "P   PAUSE"]
            for i, line in enumerate(lines):
                self.text(screen, self.font, line, WHITE, center=(WIDTH / 2, 320 + i * 30))
            if self.tick // 30 % 2:
                self.text(screen, self.font, "PRESS ENTER", YELLOW, center=(WIDTH / 2, 490))
            self.text(screen, self.font, f"HI {self.hi_score:07d}", YELLOW, center=(WIDTH / 2, 30))
            return
        self.draw_field(screen)
        self.draw_hud(screen)
        if self.state == "pause":
            self.text(screen, self.big, "PAUSE", WHITE, center=(WIDTH / 2, HEIGHT / 2))
        elif self.state == "gameover":
            self.text(screen, self.big, "GAME OVER", RED, center=(WIDTH / 2, HEIGHT / 2 - 20))
            self.text(screen, self.font, "PRESS ENTER", WHITE, center=(WIDTH / 2, HEIGHT / 2 + 30))


def read_ctrl():
    k = pygame.key.get_pressed()
    return Ctrl(
        left=k[pygame.K_LEFT] or k[pygame.K_a],
        right=k[pygame.K_RIGHT] or k[pygame.K_d],
        up=k[pygame.K_UP] or k[pygame.K_w],
        down=k[pygame.K_DOWN] or k[pygame.K_s],
        zap=k[pygame.K_z] or k[pygame.K_j],
        bomb=k[pygame.K_x] or k[pygame.K_k],
    )


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("XEVIOUS style")
    clock = pygame.time.Clock()
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN:
                    if game.state == "title":
                        game.new_game()
                    elif game.state == "gameover":
                        game.state = "title"
                elif event.key == pygame.K_p:
                    if game.state == "play":
                        game.state = "pause"
                    elif game.state == "pause":
                        game.state = "play"
        if game.state != "pause":
            game.update(read_ctrl())
        game.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
