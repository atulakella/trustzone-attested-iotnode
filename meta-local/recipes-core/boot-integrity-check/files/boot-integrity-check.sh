#!/bin/sh
# Demo-only compensating integrity check for the FIP partition.
# TF-A's own TBB verification does not enforce on this open/D-tier board
# (ROTPK_NOT_DEPLOYED + stm32mp_is_auth_supported() gap) — this script
# demonstrates what correct fail-closed behavior looks like at the next
# available layer. NOT a substitute for hardware-rooted verification.

set -eu

FIP_DEV="/dev/mmcblk0p5"
FIP_LEN="1840026"
EXPECTED="bd71e41a63af6b2e61062c20776fcbadff0e6606c5c4e67027c4d20cb369728d"

LED_RED="/sys/class/leds/demo:red/brightness"
LED_GREEN="/sys/class/leds/demo:green/brightness"

led_off() {
    [ -w "$LED_RED" ] && echo 0 > "$LED_RED" || true
    [ -w "$LED_GREEN" ] && echo 0 > "$LED_GREEN" || true
}

led_off

ACTUAL=$(dd if="$FIP_DEV" bs=1 count="$FIP_LEN" status=none | sha256sum | cut -d' ' -f1)

if [ "$ACTUAL" = "$EXPECTED" ]; then
    [ -w "$LED_GREEN" ] && echo 1 > "$LED_GREEN" || true
    printf '\033[32m============================\n   INTEGRITY CHECK: OK\n============================\033[0m\n'
    exit 0
else
    [ -w "$LED_RED" ] && echo 1 > "$LED_RED" || true
    printf '\033[31m============================\n  TAMPER DETECTED - HALT\n  expected: %s\n  actual:   %s\n============================\033[0m\n' "$EXPECTED" "$ACTUAL"
    systemctl isolate emergency.target
    exit 1
fi
