from random import random, uniform, randint

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.label import Label
from kivy.uix.widget import Widget

U = dp(4)                    # one "pixel" of the dino
GRAVITY = dp(2300)
JUMP_SPEED = dp(850)
START_SPEED = dp(320)
MAX_SPEED = dp(750)
DARK = (0.33, 0.33, 0.33, 1)
BG = (0.97, 0.97, 0.97, 1)


class Game(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.hi = 0
        self.clouds = [[random(), uniform(0.6, 0.9)] for _ in range(4)]
        self.hud = Label(font_size=dp(20), color=DARK, size_hint=(None, None))
        self.msg = Label(font_size=dp(26), color=DARK, size_hint=(None, None),
                         halign="center",
                         text="G A M E   O V E R\nTap to restart")
        self.add_widget(self.hud)
        self.add_widget(self.msg)
        self.reset()
        Clock.schedule_interval(self.update, 1 / 60)

    def reset(self):
        self.over = False
        self.time = 0.0
        self.dist = 0.0
        self.speed = START_SPEED
        self.dy = 0.0            # height above the ground
        self.vy = 0.0
        self.obstacles = []      # [x, width, height]
        self.next_gap = 0.0

    @property
    def ground(self):
        return Window.height * 0.35

    @property
    def dino_x(self):
        return Window.width * 0.12

    # ---------- input ----------
    def on_touch_down(self, touch):
        if self.over:
            self.reset()
        elif self.dy == 0:
            self.vy = JUMP_SPEED
        return True

    # ---------- logic ----------
    def update(self, dt):
        dt = min(dt, 0.05)
        w, h = Window.size
        for c in self.clouds:                       # drifting clouds
            c[0] -= 0.03 * dt
            if c[0] < -0.2:
                c[0], c[1] = 1.1, uniform(0.6, 0.9)
        if not self.over:
            self.step(dt, w)
        self.draw(w, h)

    def step(self, dt, w):
        self.time += dt
        self.speed = min(MAX_SPEED, START_SPEED + self.time * dp(6))
        self.dist += self.speed * dt

        # jump physics
        self.vy -= GRAVITY * dt
        self.dy += self.vy * dt
        if self.dy <= 0:
            self.dy, self.vy = 0.0, 0.0

        # move / remove cacti
        for o in self.obstacles:
            o[0] -= self.speed * dt
        self.obstacles = [o for o in self.obstacles if o[0] + o[1] > 0]

        # spawn new cactus group
        last = self.obstacles[-1] if self.obstacles else None
        if last is None or w - (last[0] + last[1]) > self.next_gap:
            n = randint(1, 3)
            self.obstacles.append([w + dp(20), dp(22) * n, uniform(dp(40), dp(62))])
            self.next_gap = self.speed * uniform(1.0, 1.9) + dp(60)

        # collision (slightly forgiving boxes)
        dx, dy = self.dino_x + U * 1.5, self.ground + self.dy + U * 0.5
        dw, dh = U * 9, U * 11
        for x, ow, oh in self.obstacles:
            ox, oy = x + dp(3), self.ground
            if dx < ox + ow - dp(6) and dx + dw > ox and dy < oy + oh - dp(4) and dy + dh > oy:
                self.over = True
                self.hi = max(self.hi, self.score)
                break

    @property
    def score(self):
        return int(self.dist / dp(12))

    # ---------- drawing ----------
    def draw_dino(self, x, y):
        Rectangle(pos=(x, y + U * 5), size=(U * 2, U * 2))             # tail
        Rectangle(pos=(x + U * 2, y + U * 3), size=(U * 5, U * 6))     # body
        Rectangle(pos=(x + U * 6, y + U * 8), size=(U * 5, U * 4))     # head
        Rectangle(pos=(x + U * 7, y + U * 5), size=(U * 2, U * 1))     # arm
        phase = int(self.dist / dp(25)) % 2 if self.dy == 0 else 0
        Rectangle(pos=(x + U * 3, y + (U if phase else 0)), size=(U * 1.5, U * 3))
        Rectangle(pos=(x + U * 5.5, y + (0 if phase else U)), size=(U * 1.5, U * 3))
        Color(*BG)
        Rectangle(pos=(x + U * 9, y + U * 10.5), size=(U, U))           # eye
        Color(*DARK)

    def draw(self, w, h):
        g = self.ground
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*BG)
            Rectangle(pos=(0, 0), size=(w, h))

            Color(0.85, 0.85, 0.85, 1)                                  # clouds
            for cx, cy in self.clouds:
                Rectangle(pos=(cx * w, cy * h), size=(dp(50), dp(12)))
                Rectangle(pos=(cx * w + dp(10), cy * h + dp(12)), size=(dp(28), dp(8)))

            Color(*DARK)
            Rectangle(pos=(0, g - dp(2)), size=(w, dp(2)))              # ground line
            span = w + dp(60)
            for i in range(14):                                         # ground bumps
                bx = (i * dp(70) - self.dist) % span
                Rectangle(pos=(bx, g - dp(10) - (i % 3) * dp(6)), size=(dp(8), dp(2)))

            for x, ow, oh in self.obstacles:                            # cacti
                for k in range(int(ow / dp(22))):
                    px = x + k * dp(22)
                    Rectangle(pos=(px + dp(7), g), size=(dp(8), oh))                    # trunk
                    Rectangle(pos=(px + dp(1), g + oh * 0.4), size=(dp(7), dp(4)))      # left arm
                    Rectangle(pos=(px + dp(1), g + oh * 0.4), size=(dp(4), oh * 0.3))
                    Rectangle(pos=(px + dp(14), g + oh * 0.5), size=(dp(7), dp(4)))     # right arm
                    Rectangle(pos=(px + dp(17), g + oh * 0.5), size=(dp(4), oh * 0.25))

            self.draw_dino(self.dino_x, g + self.dy)

        self.hud.text = f"HI {self.hi:05d}   {self.score:05d}"
        self.hud.texture_update()
        self.hud.size = self.hud.texture_size
        self.hud.pos = (w - self.hud.width - dp(15), h - self.hud.height - dp(25))

        self.msg.texture_update()
        self.msg.size = self.msg.texture_size
        self.msg.pos = (w / 2 - self.msg.width / 2, h * 0.6)
        self.msg.opacity = 1 if self.over else 0 


class DinoApp(App):
    def build(self):
        Window.clearcolor = BG
        return Game()


if __name__ == "__main__":
    DinoApp().run()
