FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
RAUC_KEYRING_FILE = "keyring.pem"
SRC_URI += "file://system.conf file://keyring.pem"
