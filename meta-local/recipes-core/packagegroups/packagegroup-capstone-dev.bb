SUMMARY = "Capstone development tools"
DESCRIPTION = "Development and diagnostic tools for the Capstone image."
LICENSE = "MIT"
PR = "r1"

inherit packagegroup

# The gcc toolchain can add roughly 150-300 MB to the image and widens the
# attack surface, which is undesirable for the minimal-TCB attestation story.
RDEPENDS:${PN} = "python3 gcc htop nano"
