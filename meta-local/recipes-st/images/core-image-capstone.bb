# Release image: this is the intended measured/attested rootfs.
# Keep development tooling out of this image for dm-verity/rootfs hashing.

require recipes-st/images/st-image-core.bb

SUMMARY = "Capstone release image"
