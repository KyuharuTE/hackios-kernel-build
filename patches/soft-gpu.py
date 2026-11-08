#!/usr/bin/env python3
"""Make the kernel publish a GPU service with no Adreno behind it.

Three edits:
 1. hakios.gpu.cpp: a RedwoodGPU alias class, same implementation, old name.
 2. hakios.gpu.cpp: the user client starts even when the GPU is not ready.
 3. hakios.adreno.c: HakiosGPUStart() is called even when the steps failed.
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
gpu = up / 'drivers/gpu/hakios.gpu.cpp'
adr = up / 'drivers/gpu/hakios.adreno.c'
g = gpu.read_text()
a = adr.read_text()
n = 0

ALIAS = '''/* A second registration of this service under the name an older userland looks for:
 * IOServiceMatching("RedwoodGPU") in /redwood/bin/gl_test and libredwood.dylib.
 */
class RedwoodGPU : public HakiosGPU
{
\tOSDeclareDefaultStructors(RedwoodGPU);

public:
\tvirtual bool start(IOService * provider) APPLE_KEXT_OVERRIDE;
};

OSDefineMetaClassAndStructors(RedwoodGPU, HakiosGPU);

bool
RedwoodGPU::start(IOService * provider)
{
\tif (!IOService::start(provider)) {
\t\treturn false;
\t}
\tsetProperty(kIOUserClientClassKey, "HakiosGPUUserClient");
\tsetName("RedwoodGPU");
\tregisterService();
\treturn true;
}

void
HakiosGPUStart(void)
{'''

if 'RedwoodGPU::start' not in g:
    old = 'void\nHakiosGPUStart(void)\n{'
    assert g.count(old) == 1, 'HakiosGPUStart anchor'
    g = g.replace(old, ALIAS, 1)
    n += 1

ALIAS_CALL = '''\tgpu->release();

\t/* the same service again, under the old name, in case the userland is older than this kernel */
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
\t}'''

if 'also registered as RedwoodGPU' not in g:
    old = '\tgpu->release();\n}'
    assert g.count(old) == 1, 'gpu->release anchor'
    g = g.replace(old, ALIAS_CALL + '\n}', 1)
    n += 1

if 'if (!hakios_gpu_ready() || !IOUserClient::start(provider)) {' in g:
    g = g.replace('if (!hakios_gpu_ready() || !IOUserClient::start(provider)) {',
                  'if (!IOUserClient::start(provider)) {', 1)
    n += 1

SOFT = '''\tif (!gpu_kept) {
\t\t/* No hardware behind it (QEMU, an SoC without the Adreno driver): the service is
\t\t * registered anyway, so that a userland with a software renderer has somewhere to
\t\t * hand its frames. */
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
print('soft-gpu patch: %d edit(s)' % n)
