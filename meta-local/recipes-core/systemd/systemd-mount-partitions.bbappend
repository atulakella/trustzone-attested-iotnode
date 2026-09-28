FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"
SRC_URI += "file://0001-mount-partitions-rauc-slot-aware.patch"

S = "${WORKDIR}"
