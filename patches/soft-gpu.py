#!/usr/bin/env python3
"""Publish a GPU service with no Adreno behind it.

 1. hakios.gpu.cpp      : RedwoodGPU alias class (old name), and HakiosGPUStart in C linkage
 2. hakios.gpu.cpp      : the user client starts even when the GPU is not ready
 3. hakios.adreno.c     : HakiosGPUStart is called even when the steps failed
 4. MiniIOMobileFramebuffer.cpp : start() calls HakiosGPUStart (a path that always runs)
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
gpu = up / 'drivers/gpu/hakios.gpu.cpp'
adr = up / 'drivers/gpu/hakios.adreno.c'
n = 0

g = gpu.read_text()
a = adr.read_text()

ALIAS = '''/* The same service again under the name an older userland asks for:
 * IOServiceMatching("RedwoodGPU") in /redwood/bin/gl_test and libredwood.dylib.
 */
class RedwoodGPU : public HakiosGPU
{
	OSDeclareDefaultStructors(RedwoodGPU);

public:
	virtual bool start(IOService * provider) APPLE_KEXT_OVERRIDE;
};

OSDefineMetaClassAndStructors(RedwoodGPU, HakiosGPU);

bool
RedwoodGPU::start(IOService * provider)
{
	if (!IOService::start(provider)) {
		return false;
	}
	setProperty(kIOUserClientClassKey, "HakiosGPUUserClient");
	setName("RedwoodGPU");
	registerService();
	return true;
}

extern "C" void
HakiosGPUStart(void)
{'''

if 'RedwoodGPU::start' not in g:
    old = 'void\nHakiosGPUStart(void)\n{'
    assert g.count(old) == 1, 'HakiosGPUStart anchor'
    g = g.replace(old, ALIAS, 1)
    n += 1

ALIAS_CALL = '''\tgpu->release();

\t/* also under the old name, in case the userland is older than this kernel */
\t{
\t\tRedwoodGPU * alias = OSTypeAlloc(RedwoodGPU);

\t\tif (alias != NULL) {
\t\t\tif (alias->init() && alias->attach(provider) && alias->start(provider)) {
\t\t\t\tIOLog("HakiosGPU: also registered as RedwoodGPU\\n");
\t\t\t} else {
\t\t\t\talias->detach(provider);
\t\t\t\tIOLog("HakiosGPU: the RedwoodGPU alias did not start\\n");
\t\t\t}
\t\t\talias->release();
\t\t}
\t}
}'''

if 'also registered as RedwoodGPU' not in g:
    old = '\tgpu->release();\n}'
    assert g.count(old) == 1, 'gpu release anchor'
    g = g.replace(old, ALIAS_CALL, 1)
    n += 1

if 'if (!hakios_gpu_ready() || !IOUserClient::start(provider)) {' in g:
    g = g.replace('if (!hakios_gpu_ready() || !IOUserClient::start(provider)) {',
                  'if (!IOUserClient::start(provider)) {', 1)
    n += 1

SOFT = '''\tif (!gpu_kept) {
\t\t/* No 3D core here (QEMU, an SoC without the Adreno driver): the service is
\t\t * registered anyway, so a software renderer has somewhere to hand its frames. */
\t\tprintf("adreno: no 3D core here: the service HakiosGPU is registered for software clients\\n");
\t\tHakiosGPUStart();
\t}
'''

if 'for software clients' not in a:
    old = '\tif (by_itself) {\n\t\t/* (one line for whoever wonders why the picture is drawn slowly'
    assert a.count(old) == 1, 'adreno anchor'
    a = a.replace(old, SOFT + old, 1)
    n += 1

gpu.write_text(g)
adr.write_text(a)

# 4. the display driver's start() always runs on every board
DECL = 'extern "C" void HakiosGPUStart(void);\n\n'
for mfb in list(up.rglob('MiniIOMobileFramebuffer.cpp')):
    t = mfb.read_text()
    if 'HakiosGPUStart' in t:
        continue
    anchor = 'bool\nIOMobileFramebuffer::start(IOService * provider)\n{'
    if anchor not in t:
        print('missing anchor in', mfb)
        continue
    t = t.replace(anchor, DECL + anchor, 1)
    body = '\tsetProperty("HakiosWaitsForGPU", kOSBooleanTrue);'
    if body in t:
        t = t.replace(body, body + '''\n\t/* with no Adreno behind the display, the service is still registered:\n\t * a userland with a software renderer hands its frames over through it */\n\t{\n\t\tstatic bool started;\n\n\t\tif (!started) {\n\t\t\tstarted = true;\n\t\t\tHakiosGPUStart();\n\t\t}\n\t}''', 1)
        n += 1
    mfb.write_text(t)
    print('patched', mfb)

print('soft-gpu patch: %d edit(s) total' % n)
