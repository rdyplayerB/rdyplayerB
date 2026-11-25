"""Render the GitHub contribution calendar as a gold-on-black SVG matching the profile banner.
Stdlib only, so it runs in a GitHub Action with no installs.
Usage: python contrib.py <username> <out.svg>   (or set LEVELS_FILE + TOTAL for offline testing)"""
import datetime as dt, html, os, re, sys, urllib.request
from html.parser import HTMLParser

USER, OUT = sys.argv[1], sys.argv[2]

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
    first, levels = open(os.environ['LEVELS_FILE']).read().split()
    d0 = dt.date.fromisoformat(first)
    days = {(d0 + dt.timedelta(i)).isoformat(): int(c) for i, c in enumerate(levels)}
    total = os.environ.get('TOTAL', '')
else:
    req = urllib.request.Request(f'https://github.com/users/{USER}/contributions', headers={'User-Agent': 'Mozilla/5.0'})
    p = P(); p.feed(urllib.request.urlopen(req, timeout=30).read().decode())
    days = p.days
    total = (re.search(r'([\d,]+)\s+contributions?', p.h2) or [None, ''])[1]

dates = sorted(days)
start = dt.date.fromisoformat(dates[0]); end = dt.date.fromisoformat(dates[-1])
start -= dt.timedelta((start.weekday() + 1) % 7)            # back to Sunday

# ---- look: matches the gold ASCII banner ----
import base64
BG = '#060402'
TITLE, LABEL, DIM, RULE = '#ffe9a0', '#d49a1c', '#8a5c0a', '#6a4306'
LV = ['#17100a', '#4a3005', '#9a6a0c', '#f2b82a', '#fff0b0']        # empty .. hottest
GLY = ['', '+', 'x', '#', '@']                                          # same ramp language as the banner
GCOL = ['', '#7a5208', '#d9a21e', '#4a2e02', '#6a4a10']
CELL, GAP, R = 12, 3, 2
LEFT, TOP = 50, 78
weeks = ((end - start).days // 7) + 1
W = LEFT + weeks * (CELL + GAP) + 28
H = TOP + 7 * (CELL + GAP) + 48
F = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'
here = os.path.dirname(os.path.abspath(__file__))
bgp = os.path.join(here, '..', 'assets', 'marble-bg.jpg')
if not os.path.exists(bgp): bgp = os.path.join(here, 'marble-bg.jpg')
b64 = base64.b64encode(open(bgp, 'rb').read()).decode()

o = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{F}">',
     '<defs>',
     f'<clipPath id="c"><rect width="{W}" height="{H}" rx="6"/></clipPath>',
     '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
     f'<stop offset="0" stop-color="{BG}" stop-opacity="0.35"/><stop offset="0.32" stop-color="{BG}" stop-opacity="0.86"/>'
     f'<stop offset="1" stop-color="{BG}" stop-opacity="0.93"/></linearGradient>',
     '<linearGradient id="bev" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0.22"/>'
     '<stop offset="0.5" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity="0.25"/></linearGradient>',
     '<filter id="g" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="2.2" result="b"/>'
     '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
     '<filter id="tg" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="3" result="b"/>'
     '<feComponentTransfer in="b" result="b2"><feFuncA type="linear" slope="0.6"/></feComponentTransfer>'
     '<feMerge><feMergeNode in="b2"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
     '</defs>',
     '<g clip-path="url(#c)">',
     f'<rect width="{W}" height="{H}" fill="{BG}"/>',
     f'<image href="data:image/jpeg;base64,{b64}" xlink:href="data:image/jpeg;base64,{b64}" x="0" y="0" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" opacity="0.55"/>',
     f'<rect width="{W}" height="{H}" fill="url(#fade)"/>',
     '</g>',
     f'<text x="24" y="38" font-size="15" font-weight="bold" fill="{TITLE}" filter="url(#tg)" letter-spacing="0.5">{html.escape(total)} CONTRIBUTIONS IN THE LAST YEAR</text>',
     f'<line x1="24" y1="50" x2="{W-24}" y2="50" stroke="{RULE}"/><line x1="24" y1="53" x2="{W-24}" y2="53" stroke="{RULE}" stroke-opacity="0.6"/>']
last = -9
for w in range(weeks):
    d = start + dt.timedelta(w * 7)
    firsts = [d + dt.timedelta(i) for i in range(7) if (d + dt.timedelta(i)).day == 1]
    if firsts and w - last >= 3 and w < weeks - 2:
        o.append(f'<text x="{LEFT + w*(CELL+GAP)}" y="{TOP-9}" font-size="10" fill="{LABEL}" letter-spacing="1">{firsts[0].strftime("%b").upper()}</text>')
        last = w
for i, name in ((1, 'MON'), (3, 'WED'), (5, 'FRI')):
    o.append(f'<text x="18" y="{TOP + i*(CELL+GAP) + 9.5}" font-size="9" fill="{DIM}" letter-spacing="1">{name}</text>')
d = start
while d <= end:
    k = d.isoformat()
    if k in days:
        w = (d - start).days // 7; r = (d.weekday() + 1) % 7
        lv = days[k]; x = LEFT + w*(CELL+GAP); y = TOP + r*(CELL+GAP)
        f = ' filter="url(#g)"' if lv >= 3 else ''
        st = ' stroke="#2a1c08" stroke-width="0.8"' if lv == 0 else ''
        o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{R}" fill="{LV[lv]}"{st}{f}/>')
        if lv:
            o.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{R}" fill="url(#bev)"/>')
            o.append(f'<text x="{x+CELL/2}" y="{y+CELL-2.6}" font-size="9.5" font-weight="bold" text-anchor="middle" fill="{GCOL[lv]}">{html.escape(GLY[lv])}</text>')
    d += dt.timedelta(1)
lx = W - 28 - 5*(CELL+GAP) - 78; ly = H - 30
o.append(f'<text x="{lx}" y="{ly+9.5}" font-size="10" fill="{DIM}" letter-spacing="1">LESS</text>')
for i, c in enumerate(LV):
    x = lx + 38 + i*(CELL+GAP)
    o.append(f'<rect x="{x}" y="{ly}" width="{CELL}" height="{CELL}" rx="{R}" fill="{c}"' + (' stroke="#2a1c08" stroke-width="0.8"' if i == 0 else '') + (' filter="url(#g)"' if i >= 3 else '') + '/>')
    if i:
        o.append(f'<text x="{x+CELL/2}" y="{ly+CELL-2.6}" font-size="9.5" font-weight="bold" text-anchor="middle" fill="{GCOL[i]}">{html.escape(GLY[i])}</text>')
o.append(f'<text x="{lx + 44 + 5*(CELL+GAP)}" y="{ly+9.5}" font-size="10" fill="{DIM}" letter-spacing="1">MORE</text>')
o.append('</svg>')
open(OUT, 'w').write('\n'.join(o))
print(OUT, W, H, len(days), 'days', total)
