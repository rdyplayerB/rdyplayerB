"""One animated SVG: gold ASCII marble banner + tagline + live contribution graph, with a ripple
travelling left->right through the marble (including beneath the graph).
Stdlib only, so the hourly GitHub Action can run it.
Usage: python hero.py <username> <out.svg>   (LEVELS_FILE + TOTAL env for offline testing)"""
import datetime as dt, html, json, math, os, re, sys, urllib.request
from html.parser import HTMLParser

USER, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
def data(name):
    for p in (os.path.join(HERE, name), os.path.join(HERE, '..', 'assets', name)):
        if os.path.exists(p): return json.load(open(p))
    raise FileNotFoundError(name)
M = data('marble.json'); FONTS = data('fonts.json')

# ---------- contributions ----------
class P(HTMLParser):
    def __init__(s): super().__init__(); s.days = {}; s.in_h2 = False; s.h2 = ''
    def handle_starttag(s, tag, a):
        a = dict(a)
        if tag == 'td' and 'ContributionCalendar-day' in (a.get('class') or '') and a.get('data-date'):
            s.days[a['data-date']] = int(a.get('data-level') or 0)
        if tag == 'h2' and not s.h2: s.in_h2 = True
    def handle_endtag(s, tag):
        if tag == 'h2': s.in_h2 = False
    def handle_data(s, d):
        if s.in_h2: s.h2 += d
if os.environ.get('LEVELS_FILE'):
    first, lv = open(os.environ['LEVELS_FILE']).read().split()
    d0 = dt.date.fromisoformat(first)
    days = {(d0 + dt.timedelta(i)).isoformat(): int(c) for i, c in enumerate(lv)}
    total = os.environ.get('TOTAL', '')
else:
    req = urllib.request.Request(f'https://github.com/users/{USER}/contributions', headers={'User-Agent': 'Mozilla/5.0'})
    p = P(); p.feed(urllib.request.urlopen(req, timeout=30).read().decode())
    days = p.days; total = (re.search(r'([\d,]+)\s+contributions?', p.h2) or [None, ''])[1]
if not days: sys.exit('no contribution data found')
dates = sorted(days)
start = dt.date.fromisoformat(dates[0]); end = dt.date.fromisoformat(dates[-1])
start -= dt.timedelta((start.weekday() + 1) % 7)
weeks = ((end - start).days // 7) + 1

# ---------- layout (character grid, 10 x 19 px cells) ----------
COLS, CW, CH = 120, 10, 19
ROWS = 34
W, H = COLS * CW, ROWS * CH
TR = 16                      # tagline row
G_BOX = 20 * CH + 6          # graph box top (title sits just above)
PITCH, CELL = 19, 15
L0, L1 = 7, COLS - 7
RAMP = [(0, (44, 26, 2)), (0.30, (120, 76, 6)), (0.55, (206, 146, 18)), (0.74, (250, 196, 44)), (0.87, (255, 228, 120)), (0.95, (255, 246, 206)), (1, (255, 255, 255))]
def gold(x):
    x = max(0.0, min(1.0, x))
    for (p, a), (q, b) in zip(RAMP, RAMP[1:]):
        if x <= q:
            f = (x - p) / (q - p); return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))
    return '#ffffff'
GLYPHS = " .,:;-~=+*x%#&8@"

# dim the marble behind the tagline band and the graph block (soft edges)
def dimk(r, c):
    def band(r0, r1, k):
        dr = max(r0 - r, 0, r - r1)
        dc = max(L0 - 2 - c, 0, c - (L1 + 1))
        t = max(0.0, 1 - dr / 1.6) * max(0.0, 1 - dc / 4)
        return 1 - (1 - k) * t
    return min(band(TR, TR + 1, 0.12), band(18.8, 30.6, 0.15))

# ---------- svg ----------
NCLS = 14
o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
css = [f"@font-face{{font-family:HM;src:url(data:font/{FONTS['reg']['fmt']};base64,{FONTS['reg']['b64']}) format('{FONTS['reg']['fmt']}')}}",
       f"@font-face{{font-family:HM;font-weight:bold;src:url(data:font/{FONTS['bold']['fmt']};base64,{FONTS['bold']['b64']}) format('{FONTS['bold']['fmt']}')}}",
       "text{font-family:HM,ui-monospace,Menlo,Consolas,monospace;font-size:16.6px}",
       ".b{font-weight:bold}",
       # one travelling wave packet = a column bobs once as it passes; two packets per 20s loop
       ".w{animation:rip 10s ease-in-out infinite}",
       "@keyframes rip{0%{transform:translate(0,0)}3%{transform:translate(1.4px,-3.2px)}6%{transform:translate(-1.4px,3.2px)}"
       "9%{transform:translate(.7px,-1.4px)}12%,100%{transform:translate(0,0)}}"]
for i in range(NCLS):
    css.append(f'.c{i}{{fill:{gold(0.28 + 0.80 * ((i + 0.5) / NCLS) ** 0.8)}}}')
o.append('<style>' + ''.join(css) + '</style>')
o.append('<defs><clipPath id="clip"><rect width="%d" height="%d" rx="8"/></clipPath>'
         '<filter id="g" x="-80%%" y="-80%%" width="260%%" height="260%%"><feGaussianBlur stdDeviation="2.4" result="b"/>'
         '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
         '<linearGradient id="bev" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".22"/>'
         '<stop offset=".5" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".25"/></linearGradient></defs>' % (W, H))
o.append('<g clip-path="url(#clip)">')
o.append(f'<rect width="{W}" height="{H}" fill="#050301"/>')

# marble glyphs, grouped by column and 4-row band so each group can ride the wave
BAND = 4
for c in range(COLS):
    for b0 in range(0, ROWS, BAND):
        items = []
        for r in range(b0, min(ROWS, b0 + BAND)):
            v = M['v'][r][c] * dimk(r, c)
            gi = min(15, int(v * 16))
            if gi == 0: continue
            cls = min(NCLS - 1, int(max(v, 0.2) * NCLS))
            items.append(f'<text x="{c*CW}" y="{r*CH+15}" class="c{cls}">{html.escape(GLYPHS[gi])}</text>')
        if not items: continue
        delay = 6.0 * c / COLS + 0.35 * math.sin(b0 * 0.45 + c * 0.02)   # slightly curved wavefront
        o.append(f'<g class="w" style="animation-delay:{delay:.2f}s">' + ''.join(items) + '</g>')

# tagline
def T(x, y, s, fill, bold=False, size=None, extra=''):
    st = f' style="font-size:{size}px"' if size else ''
    return f'<text x="{x}" y="{y}" fill="{fill}"{st}{" class=\"b\"" if bold else ""}{extra}>{html.escape(s)}</text>'
_t1 = 'PRETTY FLY FOR AN AI GUY.'
o.append(f'<rect x="{L0*CW - 10}" y="{TR*CH - 3}" width="{len(_t1)*CW + 20}" height="{CH + 6}" rx="6" fill="#070402" fill-opacity=".92"/>')
o.append(f'<rect x="{L1*CW - len("zero-to-one builder")*CW - 10}" y="{TR*CH - 3}" width="{len("zero-to-one builder")*CW + 20}" height="{CH + 6}" rx="6" fill="#070402" fill-opacity=".92"/>')
o.append(T(L0*CW, TR*CH+15, _t1, '#fff6dc', True))
tag = 'zero-to-one builder'
o.append(T(L1*CW - len(tag)*CW, TR*CH+15, tag, '#ffd35c', True))
o.append(T(L0*CW, (TR+1)*CH+15, '═' * (L1 - L0), '#7a5208'))

# ---- contribution graph, laid out like GitHub's own (title, bordered box, months, days, Less/More) ----
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Noto Sans',Helvetica,Arial,sans-serif"
def S(x, y, s, fill, size, anchor='start', weight='400'):
    return (f'<text x="{x}" y="{y}" fill="{fill}" text-anchor="{anchor}" '
            f'style="font-family:{SANS};font-size:{size}px;font-weight:{weight}">{html.escape(s)}</text>')
LV = ['#21180b', '#6b4708', '#b8800e', '#f2b82a', '#ffe9a0']
BX, BY = L0*CW, G_BOX
BW, BH = (L1 - L0)*CW, 214
_tw = int(len(f'{total} contributions in the last year') * 8.6) + 24
o.append(f'<rect x="{BX - 10}" y="{BY - 34}" width="{_tw}" height="30" rx="6" fill="#070402" fill-opacity=".92"/>')
o.append(S(BX, BY - 13, f'{total} contributions in the last year', '#fff6dc', 17, weight='600'))
o.append(f'<rect x="{BX}" y="{BY}" width="{BW}" height="{BH}" rx="6" fill="#070402" fill-opacity=".88" stroke="#5a3d0a" stroke-width="1"/>')
GX = BX + 46; GT = BY + 40
last = -9
for w in range(weeks):
    d = start + dt.timedelta(w * 7)
    firsts = [d + dt.timedelta(i) for i in range(7) if (d + dt.timedelta(i)).day == 1]
    if firsts and w - last >= 3 and w < weeks - 2:
        o.append(S(GX + w*PITCH, GT - 10, firsts[0].strftime('%b'), '#e8c46a', 13)); last = w
for i, nm in ((1, 'Mon'), (3, 'Wed'), (5, 'Fri')):
    o.append(S(BX + 14, GT + i*PITCH + 12, nm, '#e8c46a', 13))
def sq(x, y, lv, size=CELL):
    extra = ' stroke="#3a2a0e" stroke-width=".8"' if lv == 0 else ''
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="3" fill="{LV[lv]}"{extra}/>'
d = start
while d <= end:
    k = d.isoformat()
    if k in days:
        w = (d - start).days // 7; r = (d.weekday() + 1) % 7
        o.append(sq(GX + w*PITCH, GT + r*PITCH, days[k]))
    d += dt.timedelta(1)
fy = GT + 7*PITCH + 22
lx = BX + BW - 18 - 34 - 5*(CELL+4) - 40
o.append(S(lx, fy + 11, 'Less', '#c89b3c', 13))
for i in range(5): o.append(sq(lx + 36 + i*(CELL+4), fy, i))
o.append(S(lx + 36 + 5*(CELL+4) + 4, fy + 11, 'More', '#c89b3c', 13))

o.append('</g></svg>')
open(OUT, 'w').write('\n'.join(o))
print(OUT, W, H, weeks, 'weeks', total, os.path.getsize(OUT), 'bytes')
