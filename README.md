# hackios-kernel-build

Builds a fresh arm64 XNU kernel from https://github.com/oosexgang/hakios-xnu-kernel on an
x86_64 Linux host (this Codespace), because the phone is aarch64 and theos' cctools are x86_64.

Why: the kernel shipped inside the Android app (`mach.development.bcm2837`, 15 MB, built Oct 22)
still lacks `IOMFBDisplayRefresh` / `displayRefreshStepMachTime`, which the current source
publishes from `MiniIOMobileFramebuffer::publishRefresh()`. Without a display mode CoreAnimation
draws nothing, which is exactly what the serial log shows: SpringBoard spawned, window server up,
`StartWindowServer: initial main screen size:{375, 812}`, but `kFBMethodSwapBegin` is never called
and the framebuffer stays all zero.

## Run

```sh
./build.sh
```

The artifact is `upstream/hakios-kernel` (XNU names it `mach.development.bcm2837`). Copy it to the
phone as `assets/mach.development.bcm2837` and boot with `qemu/run-ios.sh`.
