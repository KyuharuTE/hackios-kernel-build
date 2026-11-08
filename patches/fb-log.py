#!/usr/bin/env python3
"""Say what GetLayerDefaultSurface answered: the surface, and the send right handed to
backboardd. If the right is 0, CoreAnimation never got a surface to draw a layer into, which is
one of the two reasons a swap arrives with surface number 0.
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
n = 0
for f in up.rglob('MiniIOMobileFramebuffer.cpp'):
    t = f.read_text()
    if 'default surface for selector 3' in t:
        print('fb-log: already patched')
        continue
    anchor = '''\t\ts = fOwner->defaultSurface();
\t\tif (s == NULL) {
\t\t\treturn kIOReturnNoMemory;
\t\t}
\t\tout[0] = MiniIOSurfaceMakeSendRight(fTask, s);'''
    if anchor not in t:
        print('fb-log: no anchor in', f)
        continue
    add = anchor + '''
\t\tIOLog("MiniIOMobileFramebuffer: default surface for selector 3: %p (%ux%u), send right %u\\n",
\t\t    s, fOwner->fWidth, fOwner->fHeight, (unsigned) out[0]);'''
    t = t.replace(anchor, add, 1)
    f.write_text(t)
    n += 1
    print('fb-log: patched', f)
print('fb-log: %d edit(s)' % n)
