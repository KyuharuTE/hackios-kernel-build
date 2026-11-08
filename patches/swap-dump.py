#!/usr/bin/env python3
"""Log the first two swap structures whole, word by word.

The driver reads the surface numbers of a swap at SWAP_SURFACE(layer) = 0x54 + 4*layer, an offset
taken from one iOS version's CAWindowServerDisplay. If this image's layout differs, the numbers the
driver reads are zeros while the swap itself is full of them: this dump says which offsets hold
small integers, i.e. where the surface numbers really are.
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
n = 0
for f in up.rglob('MiniIOMobileFramebuffer.cpp'):
    t = f.read_text()
    if 'swap dump' in t:
        print('swap-dump: already patched')
        continue
    anchor = 'IOMobileFramebuffer::present(const uint8_t * swap)\n{'
    if anchor not in t:
        print('swap-dump: no anchor in', f)
        continue
    add = anchor + '''
\t{
\t\tstatic int dumps;

\t\tif (dumps < 2) {
\t\t\tchar line[1400];
\t\t\tunsigned used = 0, off;

\t\t\tdumps++;
\t\t\tfor (off = 0; off + 4 <= SWAP_SIZE && used + 24 < sizeof(line); off += 4) {
\t\t\t\tused += snprintf(line + used, sizeof(line) - used, "%02x=%08x ", off, swapWord(swap, off));
\t\t\t}
\t\t\tline[used] = 0;
\t\t\tIOLog("MiniIOMobileFramebuffer: swap dump %u (%u bytes): %s\\n", dumps, SWAP_SIZE, line);
\t\t}
\t}'''
    t = t.replace(anchor, add, 1)
    f.write_text(t)
    n += 1
    print('swap-dump: patched', f)
print('swap-dump: %d edit(s)' % n)
