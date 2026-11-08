#!/usr/bin/env python3
"""Log the first two swap structures, 16 words a line from 0x40.

SWAP_SURFACE(layer) is 0x54 + 4*layer here, an offset taken from one iOS version's display
object. If this image lays the swap out differently the driver reads zeros while the numbers are
somewhere else; this dump shows which offsets hold small integers.
"""
import sys, pathlib

up = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'upstream')
n = 0
BODY = '''
	{
		static int dumps;

		if (dumps < 2) {
			char line[400];
			unsigned off, base;

			dumps++;
			for (base = 0x40; base < 0x140; base += 0x40) {
				unsigned used = 0;

				for (off = base; off < base + 0x40 && off + 4 <= SWAP_SIZE; off += 4) {
					used += snprintf(line + used, sizeof(line) - used, "%02x=%08x ", off, swapWord(swap, off));
				}
				IOLog("MiniIOMobileFramebuffer: swap dump %u at %02x: %s\\n", dumps, base, line);
			}
		}
	}'''

for f in up.rglob('MiniIOMobileFramebuffer.cpp'):
    t = f.read_text()
    if 'swap dump 1 at' in t or 'base < 0x140' in t:
        print('swap-dump: already patched')
        continue
    anchor = 'IOMobileFramebuffer::present(const uint8_t * swap)\n{'
    if anchor not in t:
        print('swap-dump: no anchor in', f)
        continue
    t = t.replace(anchor, anchor + BODY, 1)
    f.write_text(t)
    n += 1
    print('swap-dump: patched', f)
print('swap-dump: %d edit(s)' % n)
