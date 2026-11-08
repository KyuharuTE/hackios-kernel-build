#!/usr/bin/env python3
"""When a swap carries no surface, show the display's default surface instead.

backboardd asks IOMobileFramebuffer for the default surface (selector 3, GetLayerDefaultSurface,
which creates one), then sweeps every swap with surface number 0. If it is drawing into that
surface, presenting it is all that was missing.
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
n = 0
old = '''\t\tif (sid == 0) {
\t\t\t/* the bottom layer taken away: nothing is shown, the screen is black */'''
new = '''\t\tif (sid == 0 && layer == 0) {
\t\t\t/* nothing named: the surface backboardd asked for, if it drew into it */
\t\t\tMiniIOSurface * fallback = defaultSurface();

\t\t\tif (fallback != NULL) {
\t\t\t\tint32_t all[4];
\n\t\t\t\tall[0] = 0; all[1] = 0; all[2] = (int32_t) fWidth; all[3] = (int32_t) fHeight;
\t\t\t\tstatic unsigned shown;

				if (++shown <= 3) {
\t\t\t\t\tIOLog("MiniIOMobileFramebuffer: swap %u: no surface; showing the default one\\n", fSwapsShown + 1);
\t\t\t\t}
\t\t\t\tdrawLayer(fallback, all, all);
\t\t\t\tcontinue;
\t\t\t}
\t\t}
\t\tif (sid == 0) {
\t\t\t/* the bottom layer taken away: nothing is shown, the screen is black */'''

for f in up.rglob('MiniIOMobileFramebuffer.cpp'):
    t = f.read_text()
    if 'showing the default one' in t:
        print('default-surface: already patched')
        continue
    if old not in t:
        print('default-surface: no anchor in', f)
        continue
    t = t.replace(old, new, 1)
    f.write_text(t)
    n += 1
    print('default-surface: patched', f)
print('default-surface: %d edit(s)' % n)
