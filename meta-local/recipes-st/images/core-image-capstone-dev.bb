# Development image: includes packagegroup-capstone-dev and is not the
# measured/attested rootfs.

require core-image-capstone.bb

SUMMARY = "Capstone development image"
IMAGE_INSTALL:append = " packagegroup-capstone-dev"
