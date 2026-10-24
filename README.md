# trustzone-attested-IoTNode

TrustZone secure boot, OP-TEE remote attestation, and rollback-protected A/B OTA on an STM32MP157D-DK1 (Cortex-A7 + Cortex-M4 heterogeneous SoC). Capstone thesis project, VIT-AP.

## What this is

A Yocto `meta-local` layer on top of ST's OpenSTLinux distribution implementing:

- **Secure boot chain**: ROM code → FSBL (TF-A BL2) → FIP (BL32/OP-TEE + BL33/U-Boot) → Linux, with hash-gated boot integrity verification
- **Remote attestation**: OP-TEE Trusted Application measuring boot-stage state, exposed to a normal-world CA for challenge/response attestation
- **A/B OTA**: RAUC, U-Boot env-based slot selection (not ARM FWU), with crash-safe boot counters and full rootfs/bootfs/vendorfs duplication
- **Rollback protection**: TF-A `TAMP_COUNTR` NV-counter anti-rollback (in progress)

This is a demo/thesis artifact, not a production image. Signing keys and certs in this repo are demo keys. See **Keys & signing** below before reusing anything here outside a lab bench.

## Hardware

STM32MP157D-DK1. No TF-A ROTPK fused (`ROTPK_NOT_DEPLOYED`), so the secure boot chain runs in non-fused verification mode. See `docs/` or the [[nv-counter-rollback]] notes for what that does and does not guarantee.

## Repo layout
```css
meta-local/              # the actual Yocto layer: recipes, bbappends, patches
  recipes-bsp/            u-boot, TF-A, FIP assembly
  recipes-core/           RAUC config, systemd mount fixes, boot-integrity-check
  recipes-kernel/         kernel config fragments (DM-verity, LED/UART DTS patches)
  recipes-security/       attestation TA (OP-TEE) + CA (normal world)
  recipes-st/images/      image recipes (core-image-capstone*, st-image-core.bbappend)
  tools/                   stm32mp-sign-tool (prebuilt ELF binary, vendored; see below)
  cert_create              bash wrapper script
conf-reference/           local.conf / bblayers.conf as built. Not drop-in usable, see Build setup
```

## Build setup

This layer is not a standalone buildable tree. To build:

1. Set up OpenSTLinux Yocto per ST's distribution package for `stm32mp1` (poky + ST layers)
2. Drop `meta-local/` into your layers and add it to `bblayers.conf`
3. `conf-reference/` shows the configuration this was actually built against. Paths are build-server-specific, so use it as a reference only and do not copy it directly.
4. Build target: `st-image-core` (production RAUC A/B flash target, approximately 3.29 GB rootfs). `core-image-capstone` and `core-image-capstone-dev` are separate images for the attestation-thesis demo path. Do not conflate the two.
5. Image variant: `optee` (not `opteemin`) for DK1. This was confirmed via an on-target OP-TEE presence check, not assumed.

## Keys & signing

`recipes-core/rauc/files/keyring.pem` contains the RAUC bundle verification certificate, public only, from the demo signing chain. No private keys are committed to this repo; this was verified before publishing. `tools/stm32mp-sign-tool` is a prebuilt, unstripped ELF binary from ST's signing toolchain, vendored here for build convenience rather than built from source in-layer.

**Do not reuse these keys or this signing setup for anything beyond this demo.** Rotate all keys before any real deployment.

## Status

Working end-to-end as of this writing:

- Full secure boot chain, FIP-A hash-gated LED integrity demo
- OP-TEE attestation TA, measured values + verifier matrix
- RAUC A/B OTA: failover rollback tested, including hard power-cycle; real `rauc install` bundle update verified on hardware; DM-verity bundle mounting fixed; slot-aware bootfs/vendorfs mounting fixed

Open items tracked internally, notably: TF-A NV-counter values now have a build-time configuration guard, but TF-A integration and hardware enforcement remain unverified; `/etc/fw_env.config` has a redundant-env offset bug (both copies currently identical); and there is no persistent RTC (the clock resets to approximately 2024 each boot).

## License

TBD. Add a license before making the repo public, if one is not already set.

## Host-side validation

The repository includes static host-side checks for the attestation client, FIP configuration, RAUC slot mapping, and TF-A rollback-counter configuration.

Requirements:

- Python 3.8 or newer
- GCC for the host-side attestation client harness

Run the Python checks from the repository root:

```text
python tests/run_tests.py
```

The Python checks inspect repository configuration. The attestation client tests separately compile a harness with GCC and stub the TEE client interface. They do not require a live TEE or target OP-TEE headers for the covered parsing and evidence-framing paths.

These checks inspect repository configuration and do not replace an OpenSTLinux Yocto build. A Yocto build is still required to verify BitBake parsing, generated flash layouts, FIP artifacts, and TF-A integration. Target hardware is required to verify secure-boot enforcement, OP-TEE attestation, rollback-counter enforcement, and RAUC update and failover behavior.
