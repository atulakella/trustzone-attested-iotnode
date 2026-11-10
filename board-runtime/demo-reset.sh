#!/bin/sh
# Resets RAUC A/B env to a clean baseline for repeated demo reps.
# Does NOT touch FIP/flash state — tamper-test FIP reflash stays a
# separate manual step.
set -e

fw_setenv BOOT_ORDER "A B"
fw_setenv BOOT_A_LEFT 3
fw_setenv BOOT_B_LEFT 3

echo "RAUC env reset to: BOOT_ORDER='A B', BOOT_A_LEFT=3, BOOT_B_LEFT=3"
echo "Rebooting into slot A..."
reboot
