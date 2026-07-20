#!/usr/bin/env python3
"""Render the 3 PromptBase preview covers as 1000x1000 PNGs with EXACT text.
No AI text generation -> every glyph is what we wrote. Self-contained (PIL only).
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.dirname(os.path.abspath(__file__))

# Try to load a clean sans font; fall back to PIL default if none present.
FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
MONO_CANDIDATES = [
    "C:/Windows/Fonts/consolab.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

def load(paths, size):
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default(size)

SANS = lambda s: load(FONT_CANDIDATES, s)
MONO = lambda s: load(MONO_CANDIDATES, s)

WHITE = (255, 255, 255)
DARK = (13, 17, 23)
GREY_TXT = (201, 209, 219)
MUT = (139, 148, 158)
GREEN = (63, 185, 80)
RED = (248, 81, 73)
CHATGPT = (16, 163, 127)
CLAUDE = (217, 119, 87)
GREEN_BG = (234, 250, 240)
GREEN_BD = (39, 201, 63)
SYM_BG = (255, 241, 240)
SYM_BD = (255, 204, 199)
ROOT_BG = (240, 247, 255)
ROOT_BD = (173, 198, 255)
MAG = (217, 119, 87)


def rounded_rect(draw, box, r, fill=None, outline=None, width=0):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def badge(draw, xy, text, color):
    f = SANS(34)
    w = draw.textlength(text, font=f) + 56
    x, y = xy
    rounded_rect(draw, (x, y, x + w, y + 72), 36, fill=color)
    draw.text((x + 28, y + 20), text, font=f, fill=WHITE)


def terminal_frame(draw, box):
    rounded_rect(draw, box, 28, fill=DARK, outline=(48, 54, 61), width=2)
    # title bar dots
    bx, by = box[0] + 34, box[1] + 34
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse((bx + i * 34, by, bx + i * 34 + 22, by + 22), fill=c)


def render_commit():
    img = Image.new("RGB", (1000, 1000), WHITE)
    d = ImageDraw.Draw(img)
    badge(d, (1000 - 320, 44), "ChatGPT Skill", CHATGPT)
    terminal_frame(d, (140, 300, 860, 700))
    lines = [
        (GREEN, "feat: add login retry with backoff", False),
        (MUT, "# why: auth failed under load", False),
        (RED, "- old single-try call", False),
        (GREEN, "+ retry with backoff", False),
    ]
    mf = MONO(34)
    y = 380
    for color, txt, _ in lines:
        d.text((176, y), txt, font=mf, fill=color)
        y += 64
    d.text((140, 760), "Commit Message Writer", font=SANS(52), fill=DARK)
    d.text((140, 830), "Clean, conventional commits from any diff - in 5 seconds.",
           font=SANS(28), fill=(87, 96, 106))
    img.save(os.path.join(OUT, "cover-commit-message-writer.png"))
    print("commit cover saved")


def render_ci():
    img = Image.new("RGB", (1000, 1000), WHITE)
    d = ImageDraw.Draw(img)
    badge(d, (1000 - 300, 44), "Claude Skill", CLAUDE)
    # log card
    rounded_rect(d, (130, 250, 870, 470), 24, fill=DARK, outline=(48, 54, 61), width=2)
    d.text((170, 290), "Run pytest", font=MONO(32), fill=MUT)
    d.text((170, 348), "FIRST RED - assert 500 == 200", font=MONO(26), fill=RED)
    d.text((170, 392), "(test_api.py:2, cascade below)", font=MONO(26), fill=MUT)
    d.text((170, 440), "... 200 lines of cascade ...", font=MONO(28), fill=MUT)
    # fix card
    rounded_rect(d, (130, 540, 870, 760), 20, fill=GREEN_BG, outline=GREEN_BD, width=8)
    d.text((170, 580), "FIX:", font=SANS(34), fill=(26, 127, 55))
    d.text((170, 640), "mock downstream so it returns 200, or fix the", font=SANS(30), fill=DARK)
    d.text((170, 684), "handler that throws 500. Add a contract test", font=SANS(30), fill=DARK)
    d.text((170, 728), "to fail fast.", font=SANS(30), fill=DARK)
    d.text((130, 820), "CI/CD Failure Trier", font=SANS(52), fill=DARK)
    img.save(os.path.join(OUT, "cover-ci-pipeline-trier.png"))
    print("ci cover saved")


def render_debug():
    img = Image.new("RGB", (1000, 1000), WHITE)
    d = ImageDraw.Draw(img)
    badge(d, (1000 - 300, 44), "Claude Skill", CLAUDE)
    # symptom pane
    rounded_rect(d, (130, 300, 480, 620), 20, fill=SYM_BG, outline=SYM_BD, width=2)
    d.text((160, 340), "SYMPTOM", font=SANS(34), fill=(207, 19, 34))
    d.text((160, 410), "KeyError: 'timeout'", font=MONO(28), fill=DARK)
    d.text((160, 460), "app.py:42", font=MONO(28), fill=DARK)
    d.text((160, 510), "crash on startup", font=MONO(28), fill=DARK)
    # root cause pane
    rounded_rect(d, (520, 300, 870, 620), 20, fill=ROOT_BG, outline=ROOT_BD, width=2)
    d.text((550, 340), "ROOT CAUSE", font=SANS(34), fill=(29, 57, 196))
    d.text((550, 410), "cfg['timeout'] missing", font=MONO(27), fill=DARK)
    d.text((550, 455), "from loaded config -", font=MONO(27), fill=DARK)
    d.text((550, 500), "no default provided", font=MONO(27), fill=DARK)
    d.text((550, 560), "[magnifier on the line]", font=MONO(24), fill=MAG)
    d.text((130, 700), "Root-Cause Debugger", font=SANS(52), fill=DARK)
    d.text((130, 770), "Stop guessing. Find the bug - with evidence.", font=SANS(28), fill=(87, 96, 106))
    img.save(os.path.join(OUT, "cover-root-cause-debugger.png"))
    print("debug cover saved")


if __name__ == "__main__":
    render_commit()
    render_ci()
    render_debug()
    print("ALL COVERS RENDERED")
