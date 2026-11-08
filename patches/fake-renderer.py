#!/usr/bin/env python3
"""Make eagl.c report an Apple GPU as the renderer.

CoreAnimation asks glGetString(GL_RENDERER); when the answer is a software renderer it stops
drawing ("CoreAnimation: Software renderer! Simulating crash!", backboardd log). The pixels still
come from Mesa's softpipe -- only the name changes.
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
new = '''\t/* An Apple GPU's names: CoreAnimation refuses to draw with a software renderer. */
\tstatic const GLubyte apple_gpu_vendor[] = "Apple Inc.";
\tstatic const GLubyte apple_gpu_renderer[] = "Apple A11 GPU";
\tstatic const GLubyte apple_gpu_version[] = "OpenGL ES 3.0 Apple A11 GPU - 145.3";

\tif (name == 0x8a1e) {
\t\tstring = (const GLubyte *)"";
\t} else if (name == GL_VENDOR) {
\t\tstring = apple_gpu_vendor;
\t} else if (name == GL_RENDERER) {
\t\tstring = apple_gpu_renderer;
\t} else if (name == GL_VERSION) {
\t\tstring = apple_gpu_version;
\t} else {
\t\tstring = glGetString(name);
\t}'''
t = t.replace(old, new, 1)
src.write_text(t)
print('fake-renderer: patched', src)
