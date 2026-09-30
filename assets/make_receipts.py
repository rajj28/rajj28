"""Generate the profile header: a terminal that types out real, verifiable project results.

    python assets/make_receipts.py assets   # rewrites the four receipts-*.svg files

Design rules: every animated element's *resting* state is the final frame, so a renderer without
animation (or a viewer with reduced motion) sees the full content; text widths are pinned with
textLength so the typing curtain lines up whatever monospace font the viewer has.
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path

FONT = 17
CHAR = 9.8             # pinned advance per character (textLength): between Consolas (.55em) and SF Mono (.6em)
LINE = 27
TOP = 44 + 34          # title bar + first baseline offset

THEMES = {
    "dark": dict(bg="#0d1117", card="#161b22", stroke="#30363d", text="#e6edf3", muted="#8b949e",
                 prompt="#7ee787", name="#79c0ff", hi="#ffa657", dots=("#ff7b72", "#d29922", "#3fb950")),
    "light": dict(bg="#ffffff", card="#f6f8fa", stroke="#d0d7de", text="#1f2328", muted="#656d76",
                  prompt="#1a7f37", name="#0969da", hi="#bc4c00", dots=("#cf222e", "#bf8700", "#1a7f37")),
}

# (kind, start_seconds, segments). kind: "type" = typed command, "fade" = output line, "blank".
# segments: list of (css_class, text)
LINES = [
    ("type", 0.35, [("prompt", "$ "), ("text", "whoami")]),
    ("fade", 1.05, [("text", "Ruturaj Sonkamble"), ("muted", " · "), ("text", "AI engineer"), ("muted", " · "), ("text", "Pune")]),
    ("fade", 1.30, [("muted", "I build agents that act on real systems, then measure if they got it right.")]),
    ("blank", 0, []),
    ("type", 1.95, [("prompt", "$ "), ("text", "tail receipts.log")]),
    ("fade", 3.00, [("name", "argus      "), ("hi", "0 LLM calls"), ("text", " over 10 runs"), ("muted", " · "), ("hi", "5/5"), ("text", " hidden bugs caught")]),
    ("fade", 3.30, [("name", "racelab    "), ("hi", "0/50"), ("text", " bad commits vs "), ("hi", "45–48/50"), ("text", " for blind retry")]),
    ("fade", 3.60, [("name", "verdict    "), ("text", "judge-bias correction: rank agreement "), ("hi", "τ 0.669 → 0.877")]),
    ("fade", 3.90, [("name", "anomaly    "), ("hi", "38×"), ("text", " faster than real time on a 6 GB laptop GPU")]),
    ("cursor", 4.45, [("prompt", "$ ")]),
]

# Phone layout: same receipts, wrapped to ~40 characters so the text stays legible at 360px wide.
COMPACT_LINES = [
    ("type", 0.35, [("prompt", "$ "), ("text", "whoami")]),
    ("fade", 1.05, [("text", "Ruturaj Sonkamble"), ("muted", " · "), ("text", "AI engineer"), ("muted", " · "), ("text", "Pune")]),
    ("fade", 1.30, [("muted", "I build agents that act on real systems,")]),
    ("fade", 1.40, [("muted", "then measure if they got it right.")]),
    ("blank", 0, []),
    ("type", 1.95, [("prompt", "$ "), ("text", "tail receipts.log")]),
    ("fade", 3.00, [("name", "argus    "), ("hi", "0 LLM calls"), ("text", " over 10 runs")]),
    ("fade", 3.10, [("text", "         "), ("hi", "5/5"), ("text", " hidden bugs caught")]),
    ("fade", 3.35, [("name", "racelab  "), ("hi", "0/50"), ("text", " bad commits vs "), ("hi", "45–48/50")]),
    ("fade", 3.45, [("text", "         for blind retry")]),
    ("fade", 3.70, [("name", "verdict  "), ("text", "rank agreement "), ("hi", "τ 0.669 → 0.877")]),
    ("fade", 3.95, [("name", "anomaly  "), ("hi", "38×"), ("text", " faster than real time")]),
    ("fade", 4.05, [("text", "         on a 6 GB laptop GPU")]),
    ("cursor", 4.55, [("prompt", "$ ")]),
]

# name prefix -> (width, pad_x, lines); height follows from the line count.
LAYOUTS = {"": (900, 34, LINES), "compact-": (470, 24, COMPACT_LINES)}


def build(theme: str, W: int, PAD_X: int, lines: list) -> str:
    c = THEMES[theme]
    H = TOP + (len(lines) - 1) * LINE + 26
    css = [
        f".card{{fill:{c['card']};stroke:{c['stroke']};stroke-width:1.5}}",
        f".mono{{font-family:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace;font-size:{FONT}px;fill:{c['text']};white-space:pre}}",
        f".title{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:13px;fill:{c['muted']}}}",
        f".text{{fill:{c['text']}}}.muted{{fill:{c['muted']}}}.prompt{{fill:{c['prompt']};font-weight:600}}",
        f".name{{fill:{c['name']}}}.hi{{fill:{c['hi']};font-weight:600}}",
        f".curtain{{fill:{c['card']}}}",
        ".fade{animation:fade .45s ease-out backwards}",
        "@keyframes fade{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}",
        ".blink{animation:blink 1.05s steps(1) infinite}",
        "@keyframes blink{50%{opacity:0}}",
        "@media (prefers-reduced-motion:reduce){.fade,.curtain,.blink{animation:none!important}}",
    ]
    body = []
    y = TOP
    for i, (kind, t0, segs) in enumerate(lines):
        text = "".join(s for _, s in segs)
        n = len(text)
        tspans = "".join(f'<tspan class="{cls}">{escape(s)}</tspan>' for cls, s in segs)
        if kind == "blank":
            y += LINE
            continue
        width = round(n * CHAR, 1)
        text_el = (f'<text class="mono" x="{PAD_X}" y="{y}" textLength="{width}" '
                   f'lengthAdjust="spacing">{tspans}</text>')
        if kind == "type":
            # Resting state: curtain parked just right of the text (invisible on the card).
            # Animation starts it covering the text and steps it right one character at a time.
            dur = max(0.45, n * 0.055)
            css.append(f"@keyframes t{i}{{from{{transform:translateX(-{width}px)}}to{{transform:translateX(0)}}}}")
            css.append(f".c{i}{{animation:t{i} {dur:.2f}s steps({n}) {t0:.2f}s backwards}}")
            body.append(text_el)
            body.append(f'<rect class="curtain c{i}" x="{PAD_X + width}" y="{y - FONT}" '
                        f'width="{width + 6}" height="{LINE}"/>')
        elif kind == "fade":
            body.append(f'<g class="fade" style="animation-delay:{t0:.2f}s">{text_el}</g>')
        elif kind == "cursor":
            cx = PAD_X + width + 2
            body.append(f'<g class="fade" style="animation-delay:{t0:.2f}s">{text_el}'
                        f'<rect class="blink" x="{cx}" y="{y - FONT + 2}" width="9" height="{FONT + 2}" '
                        f'rx="1" fill="{c["prompt"]}" style="animation-delay:{t0 + .5:.2f}s"/></g>')
        y += LINE

    dots = "".join(f'<circle cx="{26 + k * 20}" cy="22" r="6" fill="{col}"/>' for k, col in enumerate(c["dots"]))
    plain = " / ".join("".join(s for _, s in segs) for kind, _, segs in lines if kind in ("fade",))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">
<title id="t">Ruturaj Sonkamble — receipts</title>
<desc id="d">{escape(plain)}</desc>
<style>{"".join(css)}</style>
<rect class="card" x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12"/>
{dots}
<line x1="1" y1="44" x2="{W - 1}" y2="44" stroke="{c['stroke']}" stroke-width="1"/>
<text class="title" x="{W / 2}" y="27" text-anchor="middle">ruturaj@pune: ~/receipts</text>
{chr(10).join(body)}
</svg>
'''


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out.mkdir(parents=True, exist_ok=True)
    for prefix, (width, pad, lines) in LAYOUTS.items():
        for theme in THEMES:
            path = out / f"receipts-{prefix}{theme}.svg"
            path.write_text(build(theme, width, pad, lines), encoding="utf-8")
            print("wrote", path)
