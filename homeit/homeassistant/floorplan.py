"""House floor plan: render the site's house.json (geometry in feet) to SVG.

The geometry is private site data (~/.home-it/homeassistant/floorplan/house.json); this module is
generic. Two outputs:

- `render(spec)`: a standalone, styled SVG for printing and review
  (`homeit ha floorplan` writes it next to house.json).
- `panel_config(spec)`: what the home panel's thermostat sheet needs. The SVG has no styles or
  labels, its classes carry an `fp-` prefix so the panel's own CSS can't collide with them, and
  label anchors and sensor entity ids travel as data. The panel draws names and live readings itself.

Room shapes carry id="room-<id>" and data-area="<HA area id>" so the panel can color them.

house.json, briefly: `exterior` (outer polygon), `former_exterior` (polyline drawn as an exterior
wall), `rooms` (id, name, optional short/area, kind room|closet|hall|outdoor|garage, rect [x,y,w,h]
or poly, optional label_at), `doors` / `windows` (wall h|v, at [x,y], len, type, swing, hinge, ext),
`furniture`, `hvac` (vents, returns, thermostat, sensors with HA entity ids), `annotations`.
Origin is the back-left outer corner, x to the right, y toward the front.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

INT, EXT = 0.35, 0.6          # wall thickness, ft

STYLE = """
.bg{fill:#f7f6f2}
.room{fill:#ffffff}
.room.closet,.room.hall{fill:#f1f0ec}
.room.outdoor{fill:#e9efe4}
.room.garage{fill:#ecebe7}
.gap{fill:#ffffff}
.wall{fill:none;stroke:#262a31;stroke-width:%(int)s;stroke-linejoin:miter}
.wall.outdoor{stroke:#8a9483;stroke-width:0.12}
.ext{fill:none;stroke:#262a31;stroke-width:%(ext)s;stroke-linejoin:miter}
.door{fill:none;stroke:#5b6068;stroke-width:0.07}
.door .leaf{stroke-width:0.12}
.door .open{stroke:#9a9ea5;stroke-dasharray:0.35 0.3}
.window rect{fill:#dcebf5;stroke:#262a31;stroke-width:0.06}
.window line{stroke:#262a31;stroke-width:0.05}
.window.single rect{fill:#f6dfae}
.door .porthole{stroke:#262a31;stroke-width:0.06}
.hvac .vent{fill:#2f7fd8;stroke:#1d5fae;stroke-width:0.05}
.hvac .return{fill:#d8473a;stroke:#a8322a;stroke-width:0.05}
.hvac .thermostat{fill:#c46a43;stroke:#ffffff;stroke-width:0.12}
.hvac .sensor{fill:#2f9e55;stroke:#ffffff;stroke-width:0.12}
.hvac .sensor.unconfirmed{fill:#ffffff;stroke:#2f9e55;stroke-width:0.14;stroke-dasharray:0.25 0.15}
.annot .legend text{fill:#4a4f57;font-size:0.55px;letter-spacing:0;text-anchor:start;dominant-baseline:central}
.furn *{fill:#f4f3ef;stroke:#a3a7ad;stroke-width:0.06}
.furn .counter{fill:#e7e5df}
.furn .detail{fill:none}
.furn .fireplace{fill:#c79f86;stroke:#8d6a55}
.furn .firebox{fill:#5b4a42;stroke:#3d322d}
.furn .hearth{fill:#ead8c9;stroke:#c79f86}
.furn .screen{fill:#3a3f47;stroke:#3a3f47}
.furn .keys{fill:#ffffff}
.legend .fireplace-key{fill:#c79f86;stroke:#8d6a55;stroke-width:0.06}
.furn text{fill:#7b7f86;stroke:none;font-size:0.42px}
.labels text{fill:#1f2328;text-anchor:middle;paint-order:stroke;stroke:#ffffff;stroke-width:0.18;stroke-linejoin:round}
.labels .name{font-size:0.82px;font-weight:600}
.labels .closet{font-size:0.5px;font-weight:500;fill:#4a4f57}
.labels .dims{font-size:0.5px;fill:#6b7079}
.annot text{fill:#8a8f96;font-size:0.8px;letter-spacing:0.25px;text-anchor:middle}
.annot line{stroke:#6b7079;stroke-width:0.08}
""" % {"int": INT, "ext": EXT}


def f(v: float) -> str:
    return f"{v:.3f}".rstrip("0").rstrip(".")


def rect_pts(r):
    x, y, w, h = r
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]


def room_pts(room):
    return [tuple(p) for p in room["poly"]] if "poly" in room else rect_pts(room["rect"])


def d_path(pts):
    return "M" + " L".join(f"{f(x)},{f(y)}" for x, y in pts) + " Z"


def ft_in(v: float) -> str:
    inches = round(v * 12)
    ft, inch = divmod(inches, 12)
    return f"{ft}′" if inch == 0 else f"{ft}′{inch}″"


def text(x, y, s, cls, rotate=False, size=None):
    lines = s.split("\n")
    lh = (size or 0.5) * 1.1
    y0 = y - (len(lines) - 1) * lh / 2
    tr = f' transform="rotate(-90 {f(x)} {f(y)})"' if rotate else ""
    out = []
    for i, ln in enumerate(lines):
        out.append(f'<text class="{cls}" x="{f(x)}" y="{f(y0 + i * lh)}" dominant-baseline="central"{tr}>{escape(ln)}</text>')
    return "".join(out)


# ---------------------------------------------------------------- openings
def wall_vectors(o):
    """along = unit vector along the wall, perp = unit vector to the swing side."""
    s = o.get("swing", 1)
    return ((0, 1), (s, 0)) if o["wall"] == "v" else ((1, 0), (0, s))


def gap(o, thick):
    x, y = o["at"]
    L = o["len"]
    inset = INT / 2 if o.get("type") == "opening" else 0
    pad = 0.03
    if o["wall"] == "v":
        return f'<rect class="gap" x="{f(x - thick / 2 - pad)}" y="{f(y + inset)}" width="{f(thick + 2 * pad)}" height="{f(L - 2 * inset)}"/>'
    return f'<rect class="gap" x="{f(x + inset)}" y="{f(y - thick / 2 - pad)}" width="{f(L - 2 * inset)}" height="{f(thick + 2 * pad)}"/>'


def swing_leaf(hx, hy, along, perp, L):
    px, py = hx + perp[0] * L, hy + perp[1] * L          # open leaf tip
    qx, qy = hx + along[0] * L, hy + along[1] * L        # closing jamb
    cross = (px - hx) * (qy - hy) - (py - hy) * (qx - hx)
    sweep = 1 if cross > 0 else 0
    return (f'<line class="leaf" x1="{f(hx)}" y1="{f(hy)}" x2="{f(px)}" y2="{f(py)}"/>'
            f'<path d="M{f(px)},{f(py)} A{f(L)},{f(L)} 0 0 {sweep} {f(qx)},{f(qy)}"/>')


def door(o):
    x, y = o["at"]
    L = o["len"]
    t = o.get("type", "swing")
    along, perp = wall_vectors(o)
    end = (x + along[0] * L, y + along[1] * L)
    parts = []
    if t == "swing":
        if o.get("hinge", "start") == "start":
            parts.append(swing_leaf(x, y, along, perp, L))
        else:
            parts.append(swing_leaf(end[0], end[1], (-along[0], -along[1]), perp, L))
    elif t == "double":
        h = L / 2
        parts.append(swing_leaf(x, y, along, perp, h))
        parts.append(swing_leaf(end[0], end[1], (-along[0], -along[1]), perp, h))
    elif t == "slider":
        th = (EXT if o.get("ext") else INT) / 3
        a = L * 0.55
        if o["wall"] == "h":
            parts.append(f'<rect class="leaf" x="{f(x)}" y="{f(y - th)}" width="{f(a)}" height="{f(th)}"/>')
            parts.append(f'<rect class="leaf" x="{f(x + L - a)}" y="{f(y)}" width="{f(a)}" height="{f(th)}"/>')
        else:
            parts.append(f'<rect class="leaf" x="{f(x - th)}" y="{f(y)}" width="{f(th)}" height="{f(a)}"/>')
            parts.append(f'<rect class="leaf" x="{f(x)}" y="{f(y + L - a)}" width="{f(th)}" height="{f(a)}"/>')
    elif t == "porthole":
        th = (EXT if o.get("ext") else INT) / 2
        for s in (-th, th):
            if o["wall"] == "v":
                parts.append(f'<line class="porthole" x1="{f(x + s)}" y1="{f(y)}" x2="{f(x + s)}" y2="{f(end[1])}"/>')
            else:
                parts.append(f'<line class="porthole" x1="{f(x)}" y1="{f(y + s)}" x2="{f(end[0])}" y2="{f(y + s)}"/>')
    elif t in ("opening", "garage"):
        parts.append(f'<line class="open" x1="{f(x)}" y1="{f(y)}" x2="{f(end[0])}" y2="{f(end[1])}"/>')
    return "".join(parts)


def window(o):
    x, y = o["at"]
    L = o["len"]
    t = EXT
    g = f'<g class="window {o.get("grade", "")}">'.replace(' ">', '">')
    if o["wall"] == "h":
        return (f'{g}<rect x="{f(x)}" y="{f(y - t / 2)}" width="{f(L)}" height="{f(t)}"/>'
                f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x + L)}" y2="{f(y)}"/></g>')
    return (f'{g}<rect x="{f(x - t / 2)}" y="{f(y)}" width="{f(t)}" height="{f(L)}"/>'
            f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(y + L)}"/></g>')


# ---------------------------------------------------------------- furniture
def R(x, y, w, h, cls="", rx=0.12):
    c = f' class="{cls}"' if cls else ""
    return f'<rect{c} x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(rx)}"/>'


def furniture(it):
    k = it["kind"]
    if k == "circle":
        cx, cy = it["center"]
        return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(it["r"])}"/>'
    x, y, w, h = it["rect"]
    out = []
    if k == "counter":
        out.append(R(x, y, w, h, "counter", 0.04))
    elif k == "steps":
        out.append(R(x, y, w, h, "", 0))
        n = it.get("lines", 3)
        for i in range(1, n + 1):
            yy = y + h * i / (n + 1)
            out.append(f'<line class="detail" x1="{f(x)}" y1="{f(yy)}" x2="{f(x + w)}" y2="{f(yy)}"/>')
    elif k == "bed":
        out.append(R(x, y, w, h))
        head = it.get("head", "top")
        horiz = head in ("left", "right")
        span = h if horiz else w                       # bed width across pillows
        n = 2 if span >= 4.2 else 1
        pw, pd = span / n - 0.35, 1.0
        for i in range(n):
            off = 0.175 + i * span / n
            if head == "left":
                out.append(R(x + 0.25, y + off, pd, pw, "detail", 0.2))
            elif head == "right":
                out.append(R(x + w - 0.25 - pd, y + off, pd, pw, "detail", 0.2))
            elif head == "top":
                out.append(R(x + off, y + 0.25, pw, pd, "detail", 0.2))
            else:
                out.append(R(x + off, y + h - 0.25 - pd, pw, pd, "detail", 0.2))
        fold = 0.36
        if head == "left":
            xx = x + w * fold; out.append(f'<line class="detail" x1="{f(xx)}" y1="{f(y)}" x2="{f(xx)}" y2="{f(y + h)}"/>')
        elif head == "right":
            xx = x + w * (1 - fold); out.append(f'<line class="detail" x1="{f(xx)}" y1="{f(y)}" x2="{f(xx)}" y2="{f(y + h)}"/>')
        elif head == "top":
            yy = y + h * fold; out.append(f'<line class="detail" x1="{f(x)}" y1="{f(yy)}" x2="{f(x + w)}" y2="{f(yy)}"/>')
        else:
            yy = y + h * (1 - fold); out.append(f'<line class="detail" x1="{f(x)}" y1="{f(yy)}" x2="{f(x + w)}" y2="{f(yy)}"/>')
    elif k == "sofa":
        out.append(R(x, y, w, h, "", 0.25))
        back, arm = 0.7, 0.7
        b = it.get("back", "top")
        if b == "right":
            out.append(R(x + w - back, y, back, h, "detail", 0.2))
            out.append(R(x, y, w - back, arm, "detail", 0.15)); out.append(R(x, y + h - arm, w - back, arm, "detail", 0.15))
        elif b == "left":
            out.append(R(x, y, back, h, "detail", 0.2))
            out.append(R(x + back, y, w - back, arm, "detail", 0.15)); out.append(R(x + back, y + h - arm, w - back, arm, "detail", 0.15))
        elif b == "top":
            out.append(R(x, y, w, back, "detail", 0.2))
            out.append(R(x, y + back, arm, h - back, "detail", 0.15)); out.append(R(x + w - arm, y + back, arm, h - back, "detail", 0.15))
        else:
            out.append(R(x, y + h - back, w, back, "detail", 0.2))
            out.append(R(x, y, arm, h - back, "detail", 0.15)); out.append(R(x + w - arm, y, arm, h - back, "detail", 0.15))
    elif k == "tub":
        out.append(R(x, y, w, h, "", 0.1))
        out.append(R(x + 0.3, y + 0.3, w - 0.6, h - 0.6, "detail", 0.8))
    elif k == "toilet":
        a = it.get("against", "bottom")
        tank = 0.65
        if a == "bottom":
            out.append(R(x, y + h - tank, w, tank, "", 0.1))
            cy = y + (h - tank) / 2 + 0.05
            out.append(f'<ellipse cx="{f(x + w / 2)}" cy="{f(cy)}" rx="{f(w * 0.4)}" ry="{f((h - tank) / 2)}"/>')
        elif a == "top":
            out.append(R(x, y, w, tank, "", 0.1))
            cy = y + tank + (h - tank) / 2 - 0.05
            out.append(f'<ellipse cx="{f(x + w / 2)}" cy="{f(cy)}" rx="{f(w * 0.4)}" ry="{f((h - tank) / 2)}"/>')
        elif a == "left":
            out.append(R(x, y, tank, h, "", 0.1))
            out.append(f'<ellipse cx="{f(x + tank + (w - tank) / 2)}" cy="{f(y + h / 2)}" rx="{f((w - tank) / 2)}" ry="{f(h * 0.4)}"/>')
        else:
            out.append(R(x + w - tank, y, tank, h, "", 0.1))
            out.append(f'<ellipse cx="{f(x + (w - tank) / 2)}" cy="{f(y + h / 2)}" rx="{f((w - tank) / 2)}" ry="{f(h * 0.4)}"/>')
    elif k == "vanity":
        out.append(R(x, y, w, h, "counter", 0.05))
        out.append(f'<ellipse class="detail" cx="{f(x + w / 2)}" cy="{f(y + h / 2)}" rx="{f(min(w, 2.2) * 0.3)}" ry="{f(h * 0.3)}"/>')
    elif k == "sink":
        out.append(R(x, y, w, h, "detail", 0.25))
    elif k == "cooktop":
        out.append(R(x, y, w, h, "", 0.05))
        for cx in (x + w * 0.28, x + w * 0.72):
            for cy in (y + h * 0.3, y + h * 0.7):
                out.append(f'<circle class="detail" cx="{f(cx)}" cy="{f(cy)}" r="{f(min(w, h) * 0.17)}"/>')
    elif k == "fireplace":
        out.append(R(x, y, w, h, "fireplace", 0.03))
        out.append(R(x + w * 0.15, y + h * 0.25, w * 0.7, h * 0.5, "firebox", 0.03))
    elif k == "hearth":
        out.append(R(x, y, w, h, "hearth", 0.03))
    elif k == "tv":
        out.append(R(x, y, w, h, "", 0.08))                                   # stand
        out.append(R(x + 0.15, y + 0.2, 0.22, h - 0.4, "screen", 0.03))       # TV, screen faces the room
        out.append(f'<text text-anchor="middle" x="{f(x + w * 0.62)}" y="{f(y + h / 2)}" dominant-baseline="central" '
                   f'transform="rotate(-90 {f(x + w * 0.62)} {f(y + h / 2)})">TV</text>')
    elif k == "speaker":
        out.append(R(x, y, w, h, "", 0.08))
        out.append(f'<circle class="detail" cx="{f(x + w / 2)}" cy="{f(y + h / 2)}" r="{f(min(w, h) * 0.3)}"/>')
    elif k == "piano":
        out.append(R(x, y, w, h, "", 0.08))
        out.append(R(x + 0.2, y + 0.15, w - 0.4, 0.45, "keys", 0.02))
    elif k == "table":
        out.append(R(x, y, w, h, "", 0.15))
    elif k == "chair":
        out.append(R(x, y, w, h, "", 0.25))
    else:  # box
        out.append(R(x, y, w, h, "", 0.08))
    if it.get("label"):
        rot = h > w * 1.3
        out.append(text(x + w / 2, y + h / 2, it["label"], "flabel", rotate=rot, size=0.42)
                   .replace('class="flabel"', 'text-anchor="middle"'))
    return "".join(out)


# ---------------------------------------------------------------- hvac
def wall_strip(o, depth, cls):
    """A strip on the room-side face of a wall (vent / return grille)."""
    x, y = o["at"]
    L = o["len"]
    t = (EXT if o.get("ext") else INT) / 2
    s = o.get("side", 1)
    if o["wall"] == "h":
        yy = y + t if s > 0 else y - t - depth
        return f'<rect class="{cls}" x="{f(x)}" y="{f(yy)}" width="{f(L)}" height="{f(depth)}" rx="0.05" data-area="{o.get("area", "")}"/>'
    xx = x + t if s > 0 else x - t - depth
    return f'<rect class="{cls}" x="{f(xx)}" y="{f(y)}" width="{f(depth)}" height="{f(L)}" rx="0.05" data-area="{o.get("area", "")}"/>'


def hvac(spec) -> str:
    h = spec.get("hvac")
    if not h:
        return ""
    out = ['<g class="hvac">']
    out += [wall_strip(v, 0.38, "vent") for v in h.get("vents", [])]
    out += [wall_strip(r, 0.32, "return") for r in h.get("returns", [])]
    for s in h.get("sensors", []):
        cls = "sensor unconfirmed" if s.get("unconfirmed") else "sensor"
        x, y = s["at"]
        out.append(f'<circle class="{cls}" cx="{f(x)}" cy="{f(y)}" r="0.42" data-area="{s["area"]}" '
                   f'data-temperature="{s.get("temperature", "")}" data-humidity="{s.get("humidity", "")}"/>')
    t = h.get("thermostat")
    if t:
        x, y = t["at"]
        out.append(f'<circle class="thermostat" cx="{f(x)}" cy="{f(y)}" r="0.48" data-entity="{t.get("entity", "")}" '
                   f'data-temperature="{t.get("temperature", "")}"/>')
    out.append("</g>")
    return "".join(out)


def legend(x, y) -> str:
    items = [
        ('<rect class="vent" x="{x}" y="{y1}" width="1.2" height="0.38"/>', "Supply vent, ~7.5 ft"),
        ('<rect class="return" x="{x}" y="{y1}" width="1.2" height="0.32"/>', "Return, floor level"),
        ('<circle class="thermostat" cx="{cx}" cy="{y}" r="0.42"/>', "Nest thermostat"),
        ('<circle class="sensor" cx="{cx}" cy="{y}" r="0.38"/>', "Sensor, 4 ft"),
        ('<g class="window single"><rect x="{x}" y="{y1}" width="1.2" height="0.6"/></g>', "Single-pane window"),
        ('<rect class="fireplace-key" x="{x}" y="{y1}" width="1.2" height="0.6"/>', "Fireplace (unused)"),
    ]
    out = ['<g class="legend hvac">']
    col_w = 9.0
    for i, (shape, label) in enumerate(items):
        cx0 = x + (i % 3) * col_w
        cy0 = y + (i // 3) * 1.3
        out.append(shape.format(x=f(cx0), y1=f(cy0 - 0.2), cx=f(cx0 + 0.6), y=f(cy0)))
        out.append(f'<text x="{f(cx0 + 1.7)}" y="{f(cy0)}">{escape(label)}</text>')
    out.append("</g>")
    return "".join(out)


# ---------------------------------------------------------------- main
def label_pos(r):
    if "label_at" in r:
        return r["label_at"]
    pts = room_pts(r)
    return [(min(p[0] for p in pts) + max(p[0] for p in pts)) / 2, (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2]


def render(spec, panel: bool = False) -> str:
    rooms = spec["rooms"]
    xs = [p[0] for r in rooms for p in room_pts(r)] + [p[0] for p in spec["exterior"]]
    ys = [p[1] for r in rooms for p in room_pts(r)] + [p[1] for p in spec["exterior"]]
    m = 1.5
    if panel:
        vx, vy, vw, vh = min(xs) - 0.6, min(ys) - 0.6, max(xs) - min(xs) + 1.2, max(ys) - min(ys) + 1.2
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(vx)} {f(vy)} {f(vw)} {f(vh)}" '
               f'class="floorplan" data-units="ft" preserveAspectRatio="xMidYMid meet">']
    else:
        vx, vy = min(xs) - m, min(ys) - m - 1.5
        vw, vh = max(xs) - min(xs) + 2 * m, max(ys) - min(ys) + 2 * m + 4.5
        svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(vx)} {f(vy)} {f(vw)} {f(vh)}" '
               f'width="{round(vw * 20)}" height="{round(vh * 20)}" font-family="system-ui,Segoe UI,Roboto,sans-serif" '
               f'class="floorplan" data-units="ft">',
               f"<style>{STYLE}</style>",
               f'<rect class="bg" x="{f(vx)}" y="{f(vy)}" width="{f(vw)}" height="{f(vh)}"/>']

    svg.append('<g class="rooms">')
    for r in rooms:
        area = f' data-area="{r["area"]}"' if r.get("area") else ""
        svg.append(f'<path id="room-{r["id"]}" class="room {r["kind"]}"{area} data-name="{escape(r["name"])}" d="{d_path(room_pts(r))}"/>')
    svg.append("</g>")

    ext_doors = [d for d in spec["doors"] if d.get("ext")]
    int_doors = [d for d in spec["doors"] if not d.get("ext")]

    svg.append('<g class="walls">')
    for r in rooms:
        cls = "wall outdoor" if r["kind"] == "outdoor" else "wall"
        svg.append(f'<path class="{cls}" d="{d_path(room_pts(r))}"/>')
    svg.append("</g>")

    svg.append('<g class="gaps">' + "".join(gap(d, INT) for d in int_doors) + "</g>")
    svg.append(f'<path class="ext" d="{d_path(spec["exterior"])}"/>')
    if spec.get("former_exterior"):
        fe = spec["former_exterior"]
        svg.append('<path class="ext former" d="M' + " L".join(f"{f(x)},{f(y)}" for x, y in fe) + '"/>')
    svg.append('<g class="gaps ext-gaps">' + "".join(gap(d, EXT) for d in ext_doors) + "</g>")
    svg.append('<g class="windows">' + "".join(window(w) for w in spec.get("windows", [])) + "</g>")
    svg.append('<g class="door">' + "".join(door(d) for d in spec["doors"]) + "</g>")

    svg.append('<g class="furn">' + "".join(furniture(it) for it in spec.get("furniture", [])) + "</g>")

    if not panel:
        svg.append('<g class="labels">')
        for r in rooms:
            cx, cy = label_pos(r)
            rot = r.get("rotate_label", False)
            if r["kind"] == "closet":
                svg.append(text(cx, cy, r["name"], "closet", rotate=rot, size=0.5))
                continue
            svg.append(text(cx, cy - (0 if rot else 0.35), r["name"], "name", rotate=rot, size=0.82))
            if "rect" in r and r["kind"] != "hall" and r.get("dims", True):
                _, _, w, h = r["rect"]
                svg.append(text(cx, cy + 0.55, f"{ft_in(w)} \u00d7 {ft_in(h)}", "dims", size=0.5))
        svg.append("</g>")

    svg.append(hvac(spec))

    svg.append('<g class="annot">')
    for a in spec.get("annotations", []):
        svg.append(text(a["at"][0], a["at"][1], a["text"], "", size=0.8))
    if not panel:
        if spec.get("hvac"):
            lx, ly = spec.get("legend_at", [min(xs), max(ys) + 2.0])
            svg.append(legend(lx, ly))
        sx, sy = spec.get("scale_bar_at", [min(xs), max(ys) + 2.6])
        svg.append(f'<line x1="{f(sx)}" y1="{f(sy)}" x2="{f(sx + 10)}" y2="{f(sy)}"/>')
        for i in range(0, 11, 5):
            svg.append(f'<line x1="{f(sx + i)}" y1="{f(sy - 0.3)}" x2="{f(sx + i)}" y2="{f(sy + 0.3)}"/>')
        svg.append(text(sx + 5, sy + 0.9, "10 ft", "", size=0.8))
    svg.append("</g>")
    svg.append("</svg>")
    out = "\n".join(svg)
    if panel:
        out = out.replace(' class=""', "")
        out = re.sub(r'class="([^"]*)"', lambda mm: 'class="' + " ".join("fp-" + c for c in mm.group(1).split()) + '"', out)
        out = out.replace("\n", "")
    return out


def bbox_w(r) -> float:
    xs = [p[0] for p in room_pts(r)]
    return max(xs) - min(xs)


def panel_config(spec) -> dict:
    """The `floorplan` block of the panel config: SVG plus the data the panel draws live."""
    rooms = [r for r in spec["rooms"] if r["kind"] != "closet"]
    h = spec.get("hvac") or {}
    names = {r.get("area"): r["name"] for r in rooms if r.get("area")}
    return {
        "svg": render(spec, panel=True),
        "rooms": [{"id": r["id"], "area": r.get("area"), "name": r["name"], "short": r.get("short") or r["name"], "kind": r["kind"],
                   "at": [round(v, 2) for v in label_pos(r)], "w": round(bbox_w(r), 2), "rotate": bool(r.get("rotate_label"))}
                  for r in rooms],
        "sensors": [{"area": s["area"], "name": names.get(s["area"], s["area"]), "temperature": s.get("temperature"),
                     "humidity": s.get("humidity"), "at": s["at"]} for s in h.get("sensors", [])],
        "thermostat": h.get("thermostat"),
    }


def site_dir() -> Path:
    from homeit import config
    return config.config_dir() / "homeassistant" / "floorplan"


def load_site() -> dict | None:
    p = site_dir() / "house.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main() -> None:
    spec = load_site()
    if spec is None:
        raise SystemExit(f"No floor plan: {site_dir() / 'house.json'} does not exist.")
    out = site_dir() / "floorplan.svg"
    out.write_text(render(spec), encoding="utf-8")
    print("wrote", out)
