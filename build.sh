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

time make kernel -j"$(nproc)" 2>&1 | tail -200
SUF=$?
sync
echo "== make kernel exit: $SUF"
for f in hakios-kernel prebuilt/hakios-kernel xnu-src/xnu-8796.121.2/BUILD/obj/DEVELOPMENT_ARM64_BCM2837/*.kernel \
         xnu-src/xnu-8796.121.2/BUILD/obj/DEVELOPMENT_ARM64_BCM2837/mach.development.bcm2837; do
  [ -e "$f" ] && ls -l "$f"
done
echo "=== xnu-deps logs ==="
for f in xnu-deps/*.log; do [ -e "$f" ] && { echo "##### $f"; tail -60 "$f"; }; done
echo BUILD_DONE
