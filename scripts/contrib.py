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

# ---- look ----
BG, RULE = '#0a0703', '#4a3005'
TITLE, LABEL = '#ffe688', '#c89016'
LV = ['#1c1407', '#5a3a06', '#a8740c', '#f6c02c', '#fff0b0']   # 0..4, banner gold ramp
CELL, GAP, R = 11, 3, 2
LEFT, TOP = 44, 64
weeks = ((end - start).days // 7) + 1
W = LEFT + weeks * (CELL + GAP) + 24
H = TOP + 7 * (CELL + GAP) + 40
F = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'

o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{F}">',
     f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>',
     '<defs><filter id="g" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="1.6" result="b"/>'
     '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>',
     f'<text x="22" y="34" font-size="14" font-weight="bold" fill="{TITLE}">{html.escape(total)} CONTRIBUTIONS IN THE LAST YEAR</text>',
     f'<line x1="22" y1="44" x2="{W-22}" y2="44" stroke="{RULE}"/>']
# month labels: on the first week that contains the 1st of a month
last=-9
for w in range(weeks):
    d = start + dt.timedelta(w * 7)
    firsts=[d+dt.timedelta(i) for i in range(7) if (d+dt.timedelta(i)).day==1]
    if firsts and w-last>=3 and w < weeks-2:
        m=firsts[0]
        o.append(f'<text x="{LEFT + w*(CELL+GAP)}" y="{TOP-8}" font-size="10" fill="{LABEL}">{m.strftime("%b").upper()}</text>')
        last=w
for i, name in ((1, 'MON'), (3, 'WED'), (5, 'FRI')):
    o.append(f'<text x="14" y="{TOP + i*(CELL+GAP) + 9}" font-size="9" fill="{LABEL}">{name}</text>')
# cells
d = start
while d <= end:
    k = d.isoformat()
    if k in days:
        w = (d - start).days // 7; r = (d.weekday() + 1) % 7
        lv = days[k]
        extra = ' filter="url(#g)"' if lv >= 3 else ''
        o.append(f'<rect x="{LEFT + w*(CELL+GAP)}" y="{TOP + r*(CELL+GAP)}" width="{CELL}" height="{CELL}" rx="{R}" fill="{LV[lv]}"{extra}/>')
    d += dt.timedelta(1)
# legend
lx = W - 22 - 5 * (CELL + GAP) - 70; ly = H - 22
o.append(f'<text x="{lx}" y="{ly+9}" font-size="10" fill="{LABEL}">LESS</text>')
for i, c in enumerate(LV):
    o.append(f'<rect x="{lx + 34 + i*(CELL+GAP)}" y="{ly}" width="{CELL}" height="{CELL}" rx="{R}" fill="{c}"/>')
o.append(f'<text x="{lx + 40 + 5*(CELL+GAP)}" y="{ly+9}" font-size="10" fill="{LABEL}">MORE</text>')
o.append('</svg>')
open(OUT, 'w').write('\n'.join(o))
print(OUT, W, H, len(days), 'days', total)
