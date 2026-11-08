#!/usr/bin/env python3
"""Make eagl.c report an Apple GPU as the vendor and the renderer.

CoreAnimation asks glGetString(GL_RENDERER); when the answer names a software renderer it stops
drawing ("CoreAnimation: Software renderer! Simulating crash!"). The pixels still come from
Mesa's softpipe -- only the two names change. GL_VERSION is left alone: CoreAnimation parses it
to choose between OpenGL ES 2 and 3, and a made-up one breaks the context.
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
src = up / 'userland/src/eagl.c'
t = src.read_text()

if 'apple_gpu_renderer' in t:
    print('fake-renderer: already patched')
    raise SystemExit

old = '\tstring = name == 0x8a1e ? (const GLubyte *)"" : glGetString(name);'
assert old in t, 'glGetString anchor'
new = (
    '\t/* An Apple GPU\'s names: CoreAnimation refuses to draw with a software renderer. */\n'
    '\tstatic const GLubyte apple_gpu_vendor[] = "Apple Inc.";\n'
    '\tstatic const GLubyte apple_gpu_renderer[] = "Apple A11 GPU";\n'
    '\n'
    '\tif (name == 0x8a1e) {\n'
    '\t\tstring = (const GLubyte *)"";\n'
    '\t} else if (name == GL_VENDOR) {\n'
    '\t\tstring = apple_gpu_vendor;\n'
    '\t} else if (name == GL_RENDERER) {\n'
    '\t\tstring = apple_gpu_renderer;\n'
    '\t} else {\n'
    '\t\tstring = glGetString(name);\n'
    '\t}'
)
t = t.replace(old, new, 1)
src.write_text(t)
print('fake-renderer: patched', src)
