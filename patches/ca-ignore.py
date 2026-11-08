#!/usr/bin/env python3
"""Force my_ignore_update_p() to answer 0 in userland/src/inject.c.

CoreAnimation asks its display object "should this update be ignored?". On this image the
answer is always 1, so the render loop never gets as far as a swap and the framebuffer stays
black. Answering 0 lets the loop continue.
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
src = up / 'userland/src/inject.c'
t = src.read_text()
old = '\tint ignore = orig_ignore_update_p(display, update) & 1;'
if old not in t:
    print('ca-ignore: already patched or anchor missing')
else:
    t = t.replace(old, '\tint ignore = 0; /* hakios: forced, see patches/ca-ignore.py */')
    src.write_text(t)
    print('ca-ignore: patched', src)
