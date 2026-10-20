# The ST flashlayout templates derive TF-A/FIP filenames from SIGN_ENABLE.
# Keep this scoped to the image recipe so generated TSVs reference signed
# boot artifacts produced by tf-a-stm32mp and fip-stm32mp.
SIGN_ENABLE = "1"

# Capstone: RAUC A/B OTA — inject <copy>=2 into PARTITIONS_CONFIG[sdcard] entries
# for bootfs/vendorfs/rootfs, so flashlayout-stm32mp.bbclass's own
# flashlayout_partition_config() auto-population (which reads the 5th <copy>
# field from each PARTITIONS_CONFIG entry and sets
# FLASHLAYOUT_PARTITION_DUPLICATION:<config>:<label> accordingly) picks these
# up exactly the way it already does for fsbl/metadata/fip-a/fip-b.
#
# Root cause this works around: bootfs/vendorfs/rootfs come from
# PARTITIONS_IMAGES via partImage2partConfig(), which is hardcoded to emit
# only 4 fields (<binary>,<label>,<size>,<type> — no <copy>). The generic
# FLASHLAYOUT_PARTITION_DUPLICATION:<config>:<label> override (plain conf
# syntax) does NOT reliably resolve for these labels — confirmed via forced
# rebuilds and bb.warn instrumentation that the override is correctly set in
# the datastore but never applied to the generated TSV for 4-field-sourced
# labels, while the same override auto-populated from a <copy> field on a
# 5-field entry works correctly. This appends the field directly so the
# known-working code path handles it instead.

python () {
    import re

    sdcard_entries = d.getVarFlag('PARTITIONS_CONFIG', 'sdcard')
    ab_labels = ('bootfs', 'vendorfs', 'rootfs')
    rootfs_ab_size = '4194304'  # 4 GiB, matches Capstone partition plan — overrides inherited IMAGE_ROOTFS_MAXSIZE ceiling
    bootfs_ab_size = '131072'   # 128 MiB per copy, matches Capstone locked partition plan (was inheriting single-copy 64 MiB default)

    new_entries = []
    for entry in sdcard_entries.split():
        fields = entry.split(',')
        if len(fields) == 4 and fields[1] in ab_labels:
            if fields[1] == 'rootfs':
                fields[2] = rootfs_ab_size
            elif fields[1] == 'bootfs':
                fields[2] = bootfs_ab_size
            fields.append('2')
        new_entries.append(','.join(fields))

    d.setVarFlag('PARTITIONS_CONFIG', 'sdcard', ' '.join(new_entries))

}

# Install RAUC runtime and board-specific configuration into the image.
IMAGE_INSTALL:append = " rauc rauc-conf"

# Capstone: fip-b population — ST's stock FWUP=1 branch sets
# STM32MP_SSBL2_DATA to empty (fip-b left unpopulated, "Binary none" in TSV,
# intended for runtime FWU staging, which this project doesn't use).
# Override to byte-identical copy of SSBL1 (fip-a) data path, keeping
# FWUP=1 and label "fip-b" intact (SSBL2_NAME untouched) — avoids
# disturbing FWUP's other downstream effects (SIZE fields, opt-flag PED
# generation) while giving fip-b a real, flashable binary.
STM32MP_SSBL2_DATA = "${STM32MP_SSBL1_DATA}"
IMAGE_INSTALL:append = " boot-integrity-check"
