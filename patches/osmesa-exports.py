#!/usr/bin/env python3
"""Write the list of gl* functions a Mach-O dylib exports, one a line (no leading underscore),
which is what userland/mkeagl.py calls EXPORTED. Reads the symbol table directly, so no Mesa
source tree and no nm are needed.
"""
import struct, sys

data = open(sys.argv[1], 'rb').read()
magic, = struct.unpack_from('<I', data, 0)
if magic != 0xfeedfacf:
    sys.exit('not a 64-bit Mach-O')
ncmds, = struct.unpack_from('<I', data, 16)
off = 32
symoff = nsyms = stroff = strsize = 0
for _ in range(ncmds):
    cmd, size = struct.unpack_from('<II', data, off)
    if cmd == 0x2:                                  # LC_SYMTAB
        symoff, nsyms, stroff, strsize = struct.unpack_from('<IIII', data, off + 8)
    off += size
names = set()
for i in range(nsyms):
    n_strx, n_type = struct.unpack_from('<IB', data, symoff + i * 16)
    if (n_type & 0x0e) != 0x0e:                     # only N_SECT (defined here)
        continue
    end = data.index(b'\0', stroff + n_strx)
    name = data[stroff + n_strx:end].decode('latin-1')
    if name.startswith('_gl') and len(name) > 3:
        names.add(name[1:])
for n in sorted(names):
    print(n)
