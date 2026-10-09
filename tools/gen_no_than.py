"""Sinh bộ asset pixel art cho tháp "Nỏ Thần" (Cổ Loa – An Dương Vương).

Chạy:  python3 tools/gen_no_than.py
Kết quả nằm trong assets/units/no_than/.

Toàn bộ hình được vẽ thủ tục từng pixel với một bảng màu cố định,
nên có thể chỉnh tham số rồi chạy lại để ra phiên bản mới.
"""

import json
import math
import os
import random

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "assets", "units", "no_than")

# ---------------------------------------------------------------------------
# Bảng màu (~36 màu): gỗ, đất nện, đá, đồng thau, vàng, đỏ son kiểu tranh Đông Hồ
# ---------------------------------------------------------------------------


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


P = {
    "outline": hexc("#1c1218"),
    "shadow": (20, 12, 16, 90),
    # gỗ
    "wood_dk": hexc("#3e2416"),
    "wood": hexc("#6e4026"),
    "wood_lt": hexc("#9a6236"),
    "wood_hi": hexc("#c98b4e"),
    "shaft": hexc("#dcb984"),
    # đất nện (thành Cổ Loa)
    "earth_dk": hexc("#4f301e"),
    "earth": hexc("#7c4f2e"),
    "earth_lt": hexc("#a36d40"),
    "earth_hi": hexc("#c48c55"),
    # đá
    "stone_dk": hexc("#3a3843"),
    "stone": hexc("#5f5d6b"),
    "stone_lt": hexc("#8a8896"),
    "stone_hi": hexc("#b4b2be"),
    # đồng thau
    "bronze_dk": hexc("#5a3510"),
    "bronze": hexc("#94621f"),
    "bronze_lt": hexc("#c99337"),
    "bronze_hi": hexc("#eec56a"),
    # vàng / thần lực
    "gold": hexc("#ffd23f"),
    "gold_lt": hexc("#ffe98a"),
    "gold_wh": hexc("#fffbe0"),
    # đỏ son
    "red_dk": hexc("#6e1616"),
    "red": hexc("#b02a26"),
    "red_lt": hexc("#e0513a"),
    # dây nỏ
    "string": hexc("#e6d6ab"),
    # cọc rào gỗ phong hoá
    "stake_dk": hexc("#5a4c3c"),
    "stake": hexc("#857257"),
    "stake_lt": hexc("#a8936f"),
    # cỏ
    "grass_dk": hexc("#2f4a22"),
    "grass": hexc("#4c6e2c"),
    "grass_lt": hexc("#73953a"),
    "grass_hi": hexc("#9dbb4c"),
    "white": hexc("#ffffff"),
}

FW, FH = 64, 64  # khung tháp
ANCHOR = (32, 57)  # tâm chân tháp (pixel) trong khung


# ---------------------------------------------------------------------------
# Canvas nhỏ với các primitive pixel
# ---------------------------------------------------------------------------


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.img.load()

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return (0, 0, 0, 0)

    def set(self, x, y, c):
        x, y = int(x), int(y)
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        if c[3] == 255:
            self.px[x, y] = c
            return
        # alpha blend
        r, g, b, a = self.px[x, y]
        sa = c[3] / 255.0
        da = a / 255.0
        oa = sa + da * (1 - sa)
        if oa <= 0:
            return
        nr = (c[0] * sa + r * da * (1 - sa)) / oa
        ng = (c[1] * sa + g * da * (1 - sa)) / oa
        nb = (c[2] * sa + b * da * (1 - sa)) / oa
        self.px[x, y] = (round(nr), round(ng), round(nb), round(oa * 255))

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, pts, c):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], c)

    def in_ellipse(self, x, y, cx, cy, rx, ry):
        return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                if self.in_ellipse(x, y, cx, cy, rx, ry):
                    self.set(x, y, c)

    def paste(self, other, dx=0, dy=0):
        layer = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        layer.paste(other.img, (dx, dy))
        self.img.alpha_composite(layer)
        self.px = self.img.load()


def outline(cv, color=P["outline"], skip=None):
    """Viền 1px quanh mọi pixel đặc (4 hướng)."""
    src = cv.img.copy()
    sp = src.load()
    out = []
    for y in range(cv.h):
        for x in range(cv.w):
            if sp[x, y][3] != 0:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < cv.w and 0 <= ny < cv.h and sp[nx, ny][3] >= 200:
                    out.append((x, y))
                    break
    for x, y in out:
        cv.px[x, y] = color


def glow_from(cv, keys, color, radius=1):
    """Tạo lớp phát sáng quanh các pixel có màu thuộc `keys`."""
    targets = {P[k][:3] for k in keys}
    g = Canvas(cv.w, cv.h)
    pts = [(x, y) for y in range(cv.h) for x in range(cv.w)
           if cv.px[x, y][3] == 255 and cv.px[x, y][:3] in targets]
    for x, y in pts:
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if abs(dx) + abs(dy) <= radius + 1:
                    g.px[min(max(x + dx, 0), cv.w - 1), min(max(y + dy, 0), cv.h - 1)] = color
    return g


# ---------------------------------------------------------------------------
# Đế tháp
# ---------------------------------------------------------------------------

BASE_CX = 32
BASE_RX, BASE_RY = 22, 8
BASE_BOT = 53
TOP_Y = {1: 44, 2: 42, 3: 39}


def front_off(x, rx=BASE_RX, ry=BASE_RY, cx=BASE_CX):
    u = (x + 0.5 - cx) / rx
    u = max(-1.0, min(1.0, u))
    return int(round(ry * math.sqrt(1 - u * u)))


def ell_pt(angle_deg, cy, scale=0.92):
    a = math.radians(angle_deg)
    return (BASE_CX - 0.5 + BASE_RX * scale * math.cos(a),
            cy + BASE_RY * scale * math.sin(a))


def draw_flag(cv, px, py, t, main, trim, tall=26, w=10, h=7):
    """Cột cờ đặt chân tại (px, py), cờ bay sang trái."""
    top = py - tall
    cv.line(px, py, px, top, P["wood_dk"])
    cv.set(px, top - 1, P["gold"])
    cv.set(px, top - 2, P["gold_lt"])
    for col in range(w):
        wave = round(math.sin(col * 0.75 - t * math.pi / 2) * 1.0 * (col / w + 0.3))
        x = px - 1 - col
        for row in range(h):
            y = top + 1 + row + wave
            edge = row == 0 or row == h - 1 or col == w - 1
            c = trim if edge else main
            # bóng nếp gấp
            if not edge and math.sin(col * 0.75 - t * math.pi / 2) < -0.5:
                c = P["red_dk"] if main == P["red"] else P["bronze_lt"]
            cv.set(x, y, c)
    # đuôi cờ xẻ
    tx = px - w
    cv.set(tx - 1, top + 2 + round(math.sin(w * 0.75 - t * math.pi / 2)), trim)
    cv.set(tx - 1, top + h - 1 + round(math.sin(w * 0.75 - t * math.pi / 2)), trim)


def draw_base(level, t=0):
    cv = Canvas(FW, FH)
    top_y = TOP_Y[level]
    cx, rx, ry = BASE_CX, BASE_RX, BASE_RY

    # thân trụ
    body = Canvas(FW, FH)
    for y in range(top_y - ry - 1, BASE_BOT + ry + 1):
        for x in range(cx - rx - 1, cx + rx + 1):
            in_top = body.in_ellipse(x, y, cx, top_y, rx, ry)
            in_bot = body.in_ellipse(x, y, cx, BASE_BOT, rx, ry)
            in_mid = top_y <= y <= BASE_BOT and abs(x + 0.5 - cx) <= rx
            if not (in_top or in_bot or in_mid):
                continue
            if in_top:
                continue  # mặt trên vẽ sau
            u = (x + 0.5 - cx) / rx
            fo = front_off(x)
            rel = y - (top_y + fo)  # số hàng dưới mép trước mặt trên
            from_bottom = (BASE_BOT + fo) - y
            if level == 1:
                shade = ["earth_hi", "earth_lt", "earth", "earth_dk"]
                k = 1 if u < -0.55 else (2 if u < 0.45 else 3)
                if u < -0.85:
                    k = 2
                if rel % 3 == 2:  # lớp đất nện
                    k = min(3, k + 1)
                if rel == 0:
                    k = max(0, k - 1)
                c = shade[k]
            else:
                shade = ["stone_hi", "stone_lt", "stone", "stone_dk"]
                k = 1 if u < -0.55 else (2 if u < 0.45 else 3)
                if u < -0.85:
                    k = 2
                row = rel // 4
                mortar = rel % 4 == 3 or (x + (row % 2) * 4) % 8 == 0
                if rel == 0:
                    k = max(0, k - 1)
                    mortar = False
                c = shade[min(3, k + 1)] if mortar else shade[k]
                if mortar and k == 3:
                    c = P["outline"]
                if level == 3 and 4 <= rel <= 7:
                    # dải đồng hoa văn trống đồng Đông Sơn
                    br = rel - 4
                    if br == 0:
                        c = P["bronze_hi"] if u < 0.45 else P["bronze_lt"]
                    elif br == 3:
                        c = P["bronze_dk"]
                    else:
                        m = (x + 1) % 5
                        if m == 2:
                            c = P["gold"] if br == 1 else P["bronze_lt"]
                        elif m in (1, 3):
                            c = P["bronze_dk"]
                        else:
                            c = P["bronze"] if u < 0.45 else P["bronze_dk"]
            if from_bottom <= 1:
                c = P[shade[3]] if isinstance(shade[3], str) else c
            body.px[x, y] = P[c] if isinstance(c, str) else c

    # mặt trên
    top = Canvas(FW, FH)
    for y in range(top_y - ry - 1, top_y + ry + 1):
        for x in range(cx - rx - 1, cx + rx + 1):
            if not top.in_ellipse(x, y, cx, top_y, rx, ry):
                continue
            inner = top.in_ellipse(x, y, cx, top_y, rx - 2, ry - 1)
            if level == 1:
                c = P["earth_lt"] if inner else P["earth_hi"]
            else:
                c = P["stone_lt"] if inner else P["stone_hi"]
                if level == 3 and not inner:
                    c = P["bronze_lt"]
            top.px[x, y] = c
    if level == 1:
        rnd = random.Random(7)
        for _ in range(16):
            gx = rnd.randint(cx - rx + 3, cx + rx - 3)
            gy = rnd.randint(top_y - ry + 2, top_y + ry - 2)
            if top.in_ellipse(gx, gy, cx, top_y, rx - 3, ry - 2):
                top.set(gx, gy, P["grass"])
                top.set(gx, gy - 1, P["grass_lt"])
        for _ in range(10):
            gx = rnd.randint(cx - rx + 3, cx + rx - 3)
            gy = rnd.randint(top_y - ry + 2, top_y + ry - 2)
            if top.in_ellipse(gx, gy, cx, top_y, rx - 3, ry - 2):
                top.set(gx, gy, P["earth"])
    else:
        # vòng lát đá
        for y in range(top_y - ry, top_y + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                a = top.in_ellipse(x, y, cx, top_y, rx - 7, ry - 3)
                b = top.in_ellipse(x, y, cx, top_y, rx - 8, ry - 4)
                if a and not b:
                    top.set(x, y, P["stone"])
        if level == 3:
            # mặt trời trống đồng ở giữa
            top.ellipse(cx, top_y, 5, 2, P["bronze"])
            top.ellipse(cx, top_y, 3, 1.2, P["gold"])
            for ang in range(0, 360, 30):
                a = math.radians(ang)
                top.line(cx - 0.5 + 5 * math.cos(a), top_y + 2 * math.sin(a),
                         cx - 0.5 + 9 * math.cos(a), top_y + 3.6 * math.sin(a), P["bronze"])

    cv.ellipse(ANCHOR[0], ANCHOR[1], 27, 6, P["shadow"])
    base = Canvas(FW, FH)
    base.paste(body)
    base.paste(top)
    outline(base)

    # hàng rào / lan can phía sau
    back = Canvas(FW, FH)
    if level == 1:
        angles = list(range(186, 356, 12))
        rails = []
        for ang in angles:
            bx, by = ell_pt(ang, top_y)
            bx, by = int(round(bx)), int(round(by))
            hgt = 6
            back.rect(bx, by - hgt, bx + 1, by, P["stake_lt"])
            back.line(bx + 1, by - hgt, bx + 1, by, P["stake"])
            back.set(bx, by - hgt - 1, P["stake_lt"])
            rails.append((bx, by - 3))
        for a, b in zip(rails, rails[1:]):
            back.line(a[0] + 1, a[1], b[0], b[1], P["stake_dk"])
    else:
        angles = list(range(186, 356, 28))
        pts = []
        for ang in angles:
            bx, by = ell_pt(ang, top_y)
            bx, by = int(round(bx)), int(round(by))
            post = P["red"] if level == 3 else P["wood"]
            post_lt = P["red_lt"] if level == 3 else P["wood_lt"]
            back.rect(bx, by - 7, bx + 1, by, post)
            back.line(bx, by - 7, bx, by, post_lt)
            back.set(bx, by - 8, P["gold"] if level == 3 else P["wood_hi"])
            back.set(bx + 1, by - 8, P["bronze_lt"] if level == 3 else P["wood_lt"])
            pts.append((bx, by))
        for a, b in zip(pts, pts[1:]):
            back.line(a[0] + 2, a[1] - 6, b[0] - 1, b[1] - 6, P["wood_lt"])
            back.line(a[0] + 2, a[1] - 3, b[0] - 1, b[1] - 3, P["wood"])
    outline(back)

    cv.paste(base)
    cv.paste(back)

    # cờ
    if level >= 2:
        fx, fy = ell_pt(214, top_y)
        flag = Canvas(FW, FH)
        if level == 2:
            draw_flag(flag, int(round(fx)), int(round(fy)), t, P["red"], P["bronze_lt"])
        else:
            draw_flag(flag, int(round(fx)), int(round(fy)), t, P["gold"], P["red"], tall=29)
            gx, gy = ell_pt(252, top_y)
            draw_flag(flag, int(round(gx)), int(round(gy)), t + 1, P["red"], P["gold"], tall=22, w=8, h=6)
        outline(flag)
        cv.paste(flag)
    return cv


# ---------------------------------------------------------------------------
# Nỏ (lớp xoay được / hoạt ảnh)
# ---------------------------------------------------------------------------


def draw_crossbow(level, nut_x=29, bend=1.0, arrow=True, shift=0, crank=0,
                  ribbon=0, tip_kick=0):
    cv = Canvas(FW, FH)
    top_y = TOP_Y[level]
    sy = top_y - 13  # hàng giữa báng nỏ
    if level == 1:
        prod_c, prod_d, prod_tip = P["wood_lt"], P["wood_dk"], P["wood_hi"]
        fit, fit_d = P["wood_dk"], P["outline"]
    elif level == 2:
        prod_c, prod_d, prod_tip = P["bronze_lt"], P["bronze"], P["bronze_hi"]
        fit, fit_d = P["bronze"], P["bronze_dk"]
    else:
        prod_c, prod_d, prod_tip = P["gold"], P["bronze_lt"], P["gold_wh"]
        fit, fit_d = P["bronze_lt"], P["bronze"]

    # chân đế xoay
    body = Canvas(FW, FH)
    body.ellipse(32, top_y, 5, 2, P["wood_dk"])
    body.ellipse(32, top_y - 0.5, 4, 1.5, P["wood"])
    body.rect(30, sy + 2, 33, top_y - 1, P["wood"])
    body.line(30, sy + 2, 30, top_y - 1, P["wood_lt"])
    body.line(33, sy + 2, 33, top_y - 1, P["wood_dk"])
    body.rect(29, sy + 2, 34, sy + 3, fit)

    # cánh nỏ (prod) – trên ngắn, dưới dài (phối cảnh 3/4)
    front = 44
    up, dn = 10, 13
    pts = []
    for yy in range(-up, dn + 1):
        n = yy / (up if yy < 0 else dn)
        x = front - (bend + 1.0) * (n * n) * 3.2
        pts.append((x, sy + yy))
    tip_t = (pts[0][0] - tip_kick, pts[0][1])
    tip_b = (pts[-1][0] - tip_kick, pts[-1][1])
    pts[0], pts[-1] = tip_t, tip_b
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        body.line(x0 + 1, y0, x1 + 1, y1, prod_d)
        body.line(x0, y0, x1, y1, prod_c)
    for tx, ty in (tip_t, tip_b):
        body.set(tx, ty, prod_tip)
        body.set(tx - 1, ty, prod_tip)

    # báng nỏ
    body.rect(18, sy - 1, 45, sy + 1, P["wood"])
    body.line(18, sy - 1, 45, sy - 1, P["wood_hi"])
    body.line(18, sy + 1, 45, sy + 1, P["wood_dk"])
    body.rect(17, sy - 2, 21, sy + 2, P["wood"])  # đuôi báng
    body.line(17, sy - 2, 21, sy - 2, P["wood_lt"])
    body.line(17, sy + 2, 21, sy + 2, P["wood_dk"])
    body.rect(42, sy - 2, 46, sy + 2, fit)  # đầu kẹp cánh
    body.line(42, sy - 2, 46, sy - 2, prod_tip if level > 1 else P["wood_lt"])
    body.line(46, sy - 2, 46, sy + 2, fit_d)
    if level >= 2:
        for bx in (25, 36):
            body.line(bx, sy - 1, bx, sy + 1, P["bronze_lt"])
            body.set(bx, sy - 1, P["bronze_hi"])

    # lẫy nỏ: gỗ (lv1) / đồng (lv2) / vuốt Rùa Vàng (lv3)
    if level == 1:
        body.line(25, sy + 2, 24, sy + 5, P["wood_dk"])
        body.set(25, sy + 2, P["wood_lt"])
    else:
        cl, cd = (P["gold"], P["bronze_lt"]) if level == 3 else (P["bronze_lt"], P["bronze"])
        body.rect(24, sy + 2, 25, sy + 2, cl)
        body.rect(23, sy + 3, 26, sy + 3, cl)
        body.set(22, sy + 4, cd)
        body.set(24, sy + 4, cd)
        body.set(26, sy + 4, cd)
        if level == 3:
            body.set(24, sy + 3, P["gold_wh"])

    # tời quay (bánh xe căng dây) ở đuôi
    wx, wy = 15, sy
    body.ellipse(wx + 0.5, wy + 0.5, 3, 3, P["wood_dk"])
    body.ellipse(wx + 0.5, wy + 0.5, 2, 2, P["wood"])
    spokes = [((0, -2), (0, 2), (-2, 0), (2, 0)), ((-1, -1), (1, 1), (-1, 1), (1, -1))][crank % 2]
    for i in range(0, 4, 2):
        body.line(wx + spokes[i][0], wy + spokes[i][1], wx + spokes[i + 1][0], wy + spokes[i + 1][1],
                  P["wood_hi"])
    body.set(wx, wy, fit)
    outline(body)
    cv.paste(body)

    # dây nỏ
    ny = sy - 1
    cv.line(tip_t[0] - 1, tip_t[1] + 1, nut_x, ny, P["string"])
    cv.line(tip_b[0] - 1, tip_b[1] - 1, nut_x, ny, P["string"])

    # mũi tên (lv3: liên châu – 3 mũi)
    if arrow:
        offsets = [(0, 0)] if level < 3 else [(0, 0), (-2, -2), (-4, -4)]
        for ox, oy in offsets:
            ay = sy - 2 + oy
            ax0 = nut_x + ox
            head = P["gold"] if level == 3 else P["bronze_lt"]
            head_d = P["bronze"] if level == 3 else P["bronze_dk"]
            cv.line(ax0, ay, 49 + ox, ay, P["shaft"])
            cv.set(ax0, ay - 1, P["red"])
            cv.set(ax0 + 1, ay - 1, P["red_lt"])
            cv.set(ax0, ay + 1, P["red_dk"])
            cv.set(ax0 + 1, ay + 1, P["red"])
            hx = 50 + ox
            cv.set(hx, ay - 1, head_d)
            cv.set(hx, ay, head)
            cv.set(hx, ay + 1, head_d)
            cv.set(hx + 1, ay, head)
            cv.set(hx + 2, ay, P["gold_wh"] if level == 3 else P["bronze_hi"])
            cv.set(hx - 1, ay, P["outline"])

    # ruy băng đỏ buộc đuôi báng (bay phấp phới)
    rib = [(-1, 0), (-2, 1), (-3, 1 + ribbon % 2), (-4, 2 - (ribbon % 2))]
    for i, (dx, dy) in enumerate(rib):
        cv.set(17 + dx - 1, sy - 2 + dy, P["red_lt"] if i < 2 else P["red"])

    if shift:
        moved = Canvas(FW, FH)
        moved.paste(cv, shift, 0)
        cv = moved
    return cv, sy


def muzzle_flash(level, sy, size):
    cv = Canvas(FW, FH)
    x, y = 53, sy - 2
    core = P["gold_wh"] if level == 3 else P["white"]
    mid = P["gold"] if level == 3 else P["gold_lt"]
    out = P["red_lt"] if level < 3 else P["gold_lt"]
    if size >= 1:
        cv.set(x, y, core)
        cv.set(x + 1, y, core)
        for d in ((0, -1), (0, 1), (2, 0), (-1, 0)):
            cv.set(x + d[0], y + d[1], mid)
    if size >= 2:
        for d in ((0, -2), (0, 2), (3, 0), (1, -1), (1, 1), (4, 0)):
            cv.set(x + d[0], y + d[1], mid)
        for d in ((-1, -2), (-1, 2), (2, -2), (2, 2), (5, 0)):
            cv.set(x + d[0], y + d[1], out)
        # vệt tốc độ
        cv.line(x + 3, y - 3, x + 7, y - 3, (255, 255, 255, 140))
        cv.line(x + 3, y + 3, x + 7, y + 3, (255, 255, 255, 140))
    if size == 3:
        for d in ((0, -3), (0, 3), (6, 0), (-2, 0)):
            cv.set(x + d[0], y + d[1], out)
    return cv


def sparkles(level, frame):
    cv = Canvas(FW, FH)
    if level < 3:
        return cv
    rnd = random.Random(100 + frame)
    for i in range(4):
        x = rnd.randint(14, 50)
        y = rnd.randint(TOP_Y[3] - 26, TOP_Y[3] - 2)
        phase = (frame + i) % 4
        if phase == 0:
            cv.set(x, y, P["gold_wh"])
        elif phase == 1:
            cv.set(x, y, P["gold_wh"])
            for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.set(x + d[0], y + d[1], (255, 220, 90, 170))
        elif phase == 2:
            cv.set(x, y, P["gold_lt"])
    return cv


def compose_tower(level, t, cb_kwargs, glow_alpha=0, flash=0, frame_seed=0):
    frame = Canvas(FW, FH)
    frame.paste(draw_base(level, t))
    cb, sy = draw_crossbow(level, **cb_kwargs)
    if level == 3 and glow_alpha:
        g = glow_from(cb, ["gold", "gold_wh", "gold_lt"], (255, 214, 80, glow_alpha), radius=1)
        frame.paste(g)
    frame.paste(cb)
    if flash:
        frame.paste(muzzle_flash(level, sy, flash))
    frame.paste(sparkles(level, frame_seed))
    return frame, sy


# Kịch bản hoạt ảnh -----------------------------------------------------------

IDLE = [
    dict(t=0, cb=dict(ribbon=0), glow=30),
    dict(t=1, cb=dict(ribbon=1), glow=50),
    dict(t=2, cb=dict(ribbon=0), glow=70),
    dict(t=3, cb=dict(ribbon=1), glow=50),
]
IDLE_MS = [180, 180, 180, 180]

ATTACK = [
    dict(t=0, cb=dict(nut_x=29, bend=1.0), glow=60),                      # sẵn sàng
    dict(t=1, cb=dict(nut_x=27, bend=1.8, ribbon=1), glow=100),           # căng dây
    dict(t=1, cb=dict(nut_x=40, bend=0.0, arrow=False, tip_kick=-1), glow=120, flash=3),  # nhả
    dict(t=2, cb=dict(nut_x=41, bend=0.3, arrow=False, shift=-1, tip_kick=1), glow=80, flash=1),  # giật
    dict(t=2, cb=dict(nut_x=35, bend=0.6, arrow=False, crank=1), glow=55),  # quay tời
    dict(t=3, cb=dict(nut_x=29, bend=1.0, crank=0, ribbon=1), glow=45),    # lắp tên mới
]
ATTACK_MS = [120, 140, 60, 80, 120, 120]
ATTACK_FIRE_FRAME = 2


def strip(frames):
    w, h = frames[0].w, frames[0].h
    sheet = Image.new("RGBA", (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f.img, (i * w, 0))
    return sheet


def tower_anim(level, script):
    frames = []
    sy = None
    for i, s in enumerate(script):
        f, sy = compose_tower(level, s["t"], s["cb"], glow_alpha=s.get("glow", 0),
                              flash=s.get("flash", 0), frame_seed=i)
        frames.append(f)
    return frames, sy


# ---------------------------------------------------------------------------
# Đạn & hiệu ứng
# ---------------------------------------------------------------------------


def projectile_arrow():
    frames = []
    for i in range(4):
        cv = Canvas(16, 8)
        y = 4
        # vệt gió
        for k in range(3):
            a = [120, 70, 35][k]
            ln = 2 + ((i + k) % 3)
            cv.line(0 + k, y - 2 + k * 2 if k < 2 else y, ln + k, y - 2 + k * 2 if k < 2 else y,
                    (255, 255, 255, a))
        cv.line(3, y, 12, y, P["shaft"])
        cv.set(3, y - 1, P["red"])
        cv.set(4, y - 1, P["red_lt"])
        cv.set(3, y + 1, P["red_dk"])
        cv.set(4, y + 1, P["red"])
        cv.set(13, y - 1, P["bronze_dk"])
        cv.set(13, y, P["bronze_lt"])
        cv.set(13, y + 1, P["bronze_dk"])
        cv.set(14, y, P["bronze_lt"])
        cv.set(15, y, P["bronze_hi"])
        cv.set(12, y + 1, P["outline"])
        frames.append(cv)
    return frames


def projectile_divine():
    frames = []
    for i in range(4):
        cv = Canvas(24, 12)
        y = 6
        # đuôi sáng
        for x in range(0, 14):
            a = int(30 + x * 9)
            cv.set(x, y, (255, 214, 80, min(a, 200)))
            if x > 5:
                cv.set(x, y - 1, (255, 214, 80, a // 3))
                cv.set(x, y + 1, (255, 214, 80, a // 3))
        rnd = random.Random(i * 13 + 5)
        for _ in range(4):
            sx = rnd.randint(0, 12)
            sy = y + rnd.choice([-3, -2, 2, 3])
            cv.set(sx, sy, P["gold_wh"] if rnd.random() < 0.5 else P["gold"])
        # hào quang quanh thân
        for x in range(9, 23):
            cv.set(x, y - 1, (255, 230, 120, 110))
            cv.set(x, y + 1, (255, 230, 120, 110))
        cv.line(9, y, 19, y, P["gold_lt"])
        cv.set(9, y - 1, P["red"])
        cv.set(10, y - 1, P["red_lt"])
        cv.set(9, y + 1, P["red_dk"])
        cv.set(10, y + 1, P["red"])
        cv.set(20, y - 1, P["gold"])
        cv.set(20, y, P["gold_wh"])
        cv.set(20, y + 1, P["gold"])
        cv.set(21, y, P["gold_wh"])
        cv.set(22, y, P["white"])
        if i % 2 == 0:
            cv.set(21, y - 2, (255, 251, 224, 200))
            cv.set(21, y + 2, (255, 251, 224, 200))
        frames.append(cv)
    return frames


def fx_hit(divine=False):
    frames = []
    core = P["gold_wh"] if divine else P["white"]
    mid = P["gold"] if divine else P["gold_lt"]
    out = P["gold_lt"] if divine else P["red_lt"]
    deb = P["bronze_lt"] if divine else P["wood_lt"]
    cx, cy = 16, 16
    rnd = random.Random(42 if divine else 24)
    debris = [(rnd.uniform(0, 2 * math.pi), rnd.uniform(0.7, 1.2)) for _ in range(9)]
    for f in range(6):
        cv = Canvas(32, 32)
        if f == 0:
            cv.rect(cx - 1, cy - 1, cx, cy, core)
            for d in ((-2, 0), (1, 0), (0, -2), (0, 1), (-1, -2), (-2, -1)):
                cv.set(cx + d[0], cy + d[1], mid)
        if 1 <= f <= 3:
            r = [0, 4, 7, 9][f]
            # tia sao
            for k in range(8):
                a = k * math.pi / 4 + (0.2 if f == 2 else 0)
                ln = r if k % 2 == 0 else r * 0.6
                x1 = cx - 0.5 + math.cos(a) * ln
                y1 = cy - 0.5 + math.sin(a) * ln
                x0 = cx - 0.5 + math.cos(a) * (r * 0.35)
                y0 = cy - 0.5 + math.sin(a) * (r * 0.35)
                cv.line(x0, y0, x1, y1, mid if f < 3 else (P["gold_lt"] if divine else P["string"]))
            if f == 1:
                cv.ellipse(cx, cy, 2.5, 2.5, core)
            if f == 2:
                cv.ellipse(cx, cy, 2, 2, mid)
                cv.set(cx - 1, cy - 1, core)
        if f >= 2:
            # vòng sóng xung kích
            r = [0, 0, 5, 8, 10, 11][f]
            a_ = [0, 0, 255, 200, 120, 60][f]
            ring = P["gold_lt"] if divine else P["string"]
            col = (ring[0], ring[1], ring[2], a_)
            for k in range(48):
                ang = k * 2 * math.pi / 48
                cv.set(round(cx - 0.5 + math.cos(ang) * r), round(cy - 0.5 + math.sin(ang) * r * 0.8), col)
        if f >= 1:
            # mảnh vụn bay ra
            for ang, sp in debris:
                d = (2 + f * 2.2) * sp
                x = round(cx - 0.5 + math.cos(ang) * d)
                y = round(cy - 0.5 + math.sin(ang) * d + f * f * 0.25)
                if f < 5:
                    cv.set(x, y, deb)
                    if f < 3:
                        cv.set(x + 1, y, deb if not divine else P["gold_lt"])
                elif (x + y) % 2 == 0:
                    cv.set(x, y, (deb[0], deb[1], deb[2], 140))
        frames.append(cv)
    return frames


# ---------------------------------------------------------------------------
# Icon UI
# ---------------------------------------------------------------------------


def icon_frame(cv, bg_a, bg_b):
    n = cv.w
    for y in range(n):
        for x in range(n):
            cv.px[x, y] = bg_a if (y < n // 2 + (x - n // 2) // 3) else bg_b
    # mặt trời trống đồng mờ phía sau
    c = n / 2
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        cv.line(c - 0.5 + 4 * math.cos(a), c - 0.5 + 4 * math.sin(a),
                c - 0.5 + 12 * math.cos(a), c - 0.5 + 12 * math.sin(a), (238, 197, 106, 45))
    cv.ellipse(c, c, 3.5, 3.5, (238, 197, 106, 60))
    # viền đồng
    for i in range(n):
        for (x, y) in ((i, 0), (i, n - 1), (0, i), (n - 1, i)):
            cv.px[x, y] = P["outline"]
        for (x, y) in ((i, 1), (1, i)):
            if 1 <= i <= n - 2:
                cv.px[x, y] = P["bronze_hi"]
        for (x, y) in ((i, n - 2), (n - 2, i)):
            if 1 <= i <= n - 2:
                cv.px[x, y] = P["bronze"]
    # răng cưa trang trí (hoa văn răng lược)
    for i in range(4, n - 4, 3):
        cv.px[i, 2] = P["bronze_lt"]
        cv.px[i, n - 3] = P["bronze_dk"]
    for (x, y) in ((2, 2), (n - 3, 2), (2, n - 3), (n - 3, n - 3)):
        cv.px[x, y] = P["gold"]


def icon_build():
    cv = Canvas(32, 32)
    icon_frame(cv, P["red"], P["red_dk"])
    art = Canvas(32, 32)
    # báng nỏ chéo 45°
    for i in range(14):
        x, y = 8 + i, 23 - i
        art.set(x, y, P["wood_lt"])
        art.set(x + 1, y, P["wood"])
        art.set(x, y + 1, P["wood_dk"])
    # cánh nỏ vuông góc, cong về sau
    fx, fy = 20, 11
    pts = []
    for k in range(-7, 8):
        bend = (k / 7) ** 2 * 2.4
        pts.append((fx + k - bend, fy + k + bend))
    for a, b in zip(pts, pts[1:]):
        art.line(a[0] + 1, a[1], b[0] + 1, b[1], P["bronze"])
        art.line(a[0], a[1], b[0], b[1], P["gold"])
    t1, t2 = pts[0], pts[-1]
    art.set(t1[0], t1[1], P["gold_wh"])
    art.set(t2[0], t2[1], P["gold_wh"])
    # vuốt rùa (lẫy)
    art.set(11, 22, P["gold"])
    art.set(12, 23, P["gold"])
    art.set(11, 24, P["bronze_lt"])
    art.set(13, 24, P["bronze_lt"])
    outline(art)
    # dây + tên
    nx, ny = 13, 18
    art.line(t1[0], t1[1] + 1, nx, ny, P["string"])
    art.line(t2[0] - 1, t2[1], nx, ny, P["string"])
    for i in range(13):
        art.set(nx + i, ny - i, P["shaft"])
    art.set(nx, ny + 1, P["red"])
    art.set(nx - 1, ny, P["red"])
    hx, hy = nx + 13, ny - 13
    art.set(hx, hy, P["gold_wh"])
    art.set(hx - 1, hy, P["gold"])
    art.set(hx, hy + 1, P["gold"])
    art.set(hx - 1, hy + 1, P["bronze_lt"])
    cv.paste(art)
    return cv


def icon_skill():
    """Kỹ năng "Thần Tiễn Liên Châu" – một phát nỏ ra muôn mũi tên."""
    cv = Canvas(32, 32)
    icon_frame(cv, hexc("#2a1c3a"), hexc("#1a1226"))
    art = Canvas(32, 32)
    starts = [(6, 22), (10, 26), (5, 14), (14, 25), (8, 18)]
    for k, (sx, sy) in enumerate(starts):
        ln = 12 if k < 3 else 9
        for i in range(ln):
            x, y = sx + i, sy - i
            a = 60 + i * 15
            art.set(x - 1, y, (255, 214, 80, min(a, 180)))
        ex, ey = sx + ln, sy - ln
        art.set(ex - 1, ey + 1, P["gold_lt"])
        art.set(ex, ey, P["gold_lt"])
        art.set(ex + 1, ey - 1, P["gold_wh"])
        art.set(ex + 1, ey, P["gold"])
        art.set(ex, ey - 1, P["gold"])
        art.set(ex + 2, ey - 2, P["white"])
    cv.paste(art)
    # tia sáng góc
    for (x, y) in ((25, 6), (24, 9), (27, 8)):
        cv.set(x, y, P["gold_wh"])
    return cv


# ---------------------------------------------------------------------------
# Preview (phóng to 4x trên nền cỏ)
# ---------------------------------------------------------------------------


def grass_bg(w, h, seed=3):
    cv = Canvas(w, h)
    rnd = random.Random(seed)
    for y in range(h):
        for x in range(w):
            cv.px[x, y] = P["grass"]
    for _ in range(w * h // 18):
        x, y = rnd.randrange(w), rnd.randrange(h)
        cv.px[x, y] = rnd.choice([P["grass_dk"], P["grass_lt"], P["grass_lt"]])
        if rnd.random() < 0.3 and y > 0:
            cv.px[x, y - 1] = P["grass_hi"]
    return cv


def upscale(img, s=4):
    return img.resize((img.width * s, img.height * s), Image.NEAREST)


def save_gif(frames, durations, path, scale=4, bg=None):
    imgs = []
    for f in frames:
        base = (bg.img.copy() if bg else Image.new("RGBA", (f.w, f.h), P["grass"]))
        base.alpha_composite(f.img)
        imgs.append(upscale(base.convert("RGB"), scale))
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=durations, loop=0,
                 disposal=2)


# ---------------------------------------------------------------------------


def main():
    sp = os.path.join(OUT, "sprites")
    ui = os.path.join(OUT, "ui")
    pv = os.path.join(OUT, "preview")
    for d in (sp, ui, pv):
        os.makedirs(d, exist_ok=True)

    meta = {
        "unit": "no_than",
        "name_vi": "Nỏ Thần",
        "frame_size": [FW, FH],
        "anchor": list(ANCHOR),
        "facing": "right (lật ngang để quay trái)",
        "levels": {},
        "projectiles": {},
        "fx": {},
        "ui": {},
    }
    names = {1: "Nỏ Cổ Loa", 2: "Nỏ Đồng", 3: "Nỏ Thần Liên Châu"}
    bg = grass_bg(FW, FH)
    all_idle, all_attack = {}, {}
    for lv in (1, 2, 3):
        idle, _ = tower_anim(lv, IDLE)
        atk, sy = tower_anim(lv, ATTACK)
        all_idle[lv], all_attack[lv] = idle, atk
        strip(idle).save(os.path.join(sp, f"tower_lv{lv}_idle.png"))
        strip(atk).save(os.path.join(sp, f"tower_lv{lv}_attack.png"))
        save_gif(idle, IDLE_MS, os.path.join(pv, f"tower_lv{lv}_idle.gif"), bg=bg)
        save_gif(atk, ATTACK_MS, os.path.join(pv, f"tower_lv{lv}_attack.gif"), bg=bg)
        meta["levels"][str(lv)] = {
            "name_vi": names[lv],
            "idle": {"file": f"sprites/tower_lv{lv}_idle.png", "frames": len(idle),
                     "durations_ms": IDLE_MS, "loop": True},
            "attack": {"file": f"sprites/tower_lv{lv}_attack.png", "frames": len(atk),
                       "durations_ms": ATTACK_MS, "loop": False,
                       "fire_frame": ATTACK_FIRE_FRAME,
                       "projectile_spawn": [52 - ANCHOR[0], (sy - 2) - ANCHOR[1]],
                       "projectile_count": 3 if lv == 3 else 1},
            "projectile": "divine" if lv == 3 else "arrow",
        }

    arrow = projectile_arrow()
    divine = projectile_divine()
    strip(arrow).save(os.path.join(sp, "projectile_arrow.png"))
    strip(divine).save(os.path.join(sp, "projectile_divine.png"))
    meta["projectiles"] = {
        "arrow": {"file": "sprites/projectile_arrow.png", "frame_size": [16, 8], "frames": 4,
                  "durations_ms": [60] * 4, "pivot": [15, 4], "rotate_to_velocity": True},
        "divine": {"file": "sprites/projectile_divine.png", "frame_size": [24, 12], "frames": 4,
                   "durations_ms": [60] * 4, "pivot": [22, 6], "rotate_to_velocity": True},
    }
    hit = fx_hit(False)
    hit_d = fx_hit(True)
    strip(hit).save(os.path.join(sp, "fx_hit.png"))
    strip(hit_d).save(os.path.join(sp, "fx_hit_divine.png"))
    hit_ms = [50, 60, 60, 70, 80, 90]
    meta["fx"] = {
        "hit": {"file": "sprites/fx_hit.png", "frame_size": [32, 32], "frames": 6,
                "durations_ms": hit_ms, "pivot": [16, 16]},
        "hit_divine": {"file": "sprites/fx_hit_divine.png", "frame_size": [32, 32], "frames": 6,
                       "durations_ms": hit_ms, "pivot": [16, 16]},
    }
    ib = icon_build()
    isk = icon_skill()
    ib.img.save(os.path.join(ui, "icon_build.png"))
    isk.img.save(os.path.join(ui, "icon_skill_than_tien.png"))
    meta["ui"] = {"build": "ui/icon_build.png", "skill": "ui/icon_skill_than_tien.png",
                  "skill_name_vi": "Thần Tiễn Liên Châu"}
    with open(os.path.join(OUT, "no_than.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)

    # GIF đạn & hiệu ứng
    save_gif(arrow, [60] * 4, os.path.join(pv, "projectile_arrow.gif"), scale=6,
             bg=grass_bg(16, 8, 5))
    save_gif(divine, [60] * 4, os.path.join(pv, "projectile_divine.gif"), scale=6,
             bg=grass_bg(24, 12, 6))
    save_gif(hit, hit_ms, os.path.join(pv, "fx_hit.gif"), scale=6, bg=grass_bg(32, 32, 7))
    save_gif(hit_d, hit_ms, os.path.join(pv, "fx_hit_divine.gif"), scale=6, bg=grass_bg(32, 32, 8))

    # Bảng tổng hợp (contact sheet)
    pad = 4
    sheet_w = pad + 6 * (FW + pad)
    sheet_h = pad + 3 * 2 * (FH + pad) + 40 + pad
    sheet = grass_bg(sheet_w, sheet_h, 11).img
    y = pad
    for lv in (1, 2, 3):
        for row in (all_idle[lv], all_attack[lv]):
            for i, f in enumerate(row):
                sheet.alpha_composite(f.img, (pad + i * (FW + pad), y))
            y += FH + pad
    x = pad
    for img in (ib.img, isk.img):
        sheet.alpha_composite(img, (x, y))
        x += 32 + pad
    for f in hit[1:4]:
        sheet.alpha_composite(f.img, (x, y))
        x += 32 + pad
    for f in hit_d[1:4]:
        sheet.alpha_composite(f.img, (x, y))
        x += 32 + pad
    sheet.alpha_composite(arrow[0].img, (x, y + 4))
    sheet.alpha_composite(divine[0].img, (x, y + 18))
    upscale(sheet, 4).save(os.path.join(pv, "contact_sheet.png"))
    print("done ->", OUT)


if __name__ == "__main__":
    main()
