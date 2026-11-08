#!/usr/bin/env bash
# Build a fresh HakiOS arm64 kernel (the one the iPhone-10,3 userland boots under).
set -uo pipefail
set -x

UP=${UP:-$PWD/upstream}
if [ ! -d "$UP/.git" ]; then
  git clone --filter=blob:none https://github.com/oosexgang/hakios-xnu-kernel.git "$UP"
fi
cd "$UP"
git sparse-checkout disable || true
git fetch --all --tags || true
git checkout main || true
git log -1 --format='%H %ci %s'

ls -l prebuilt/ 2>/dev/null | head

# XNU's own toolchain (theos + cctools + iPhoneOS16.5.sdk) is laid out by xnu-deps/setup.sh,
# which `make kernel` calls on its first run.
make redwood_defconfig

# Tools may want these present.
export PATH="$PWD/xnu-deps/host/bin:$PATH"

export BUILD_DSYM=0
export BUILD_LTO=0
time make kernel BUILD_DSYM=0 -j"$(nproc)" 2>&1 | tail -300
SUF=$?
sync
echo "== make kernel exit: $SUF"
OBJ=xnu-src/xnu-8796.121.2/BUILD/obj/DEVELOPMENT_ARM64_BCM2837
mkdir -p built
for f in hakios-kernel prebuilt/hakios-kernel $OBJ/mach.development.bcm2837 \
         $OBJ/mach.development.bcm2837.unstripped $OBJ/mach.development.bcm2837.a; do
  [ -e "$f" ] && { ls -l "$f"; cp -f "$f" built/ 2>/dev/null; }
done
ls -l built || true
for f in built/*; do printf '%-40s ' "$(basename $f)";   strings "$f" 2>/dev/null | grep -q IOMFBDisplayRefresh && echo HAS_REFRESH || echo no_refresh; done
echo "=== xnu-deps logs ==="
for f in xnu-deps/*.log; do [ -e "$f" ] && { echo "##### $f"; tail -60 "$f"; }; done
echo BUILD_DONE
