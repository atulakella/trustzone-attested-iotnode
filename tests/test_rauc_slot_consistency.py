import configparser
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RAUC_CONFIG = ROOT / "meta-local/recipes-core/rauc/files/system.conf"
UBOOT_PATCH = ROOT / "meta-local/recipes-bsp/u-boot/u-boot-stm32mp/0001-rauc-bootsel-override.patch"
MOUNT_PATCH = ROOT / "meta-local/recipes-core/systemd/systemd-mount-partitions/0001-mount-partitions-rauc-slot-aware.patch"


class RaucSlotConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rauc = configparser.ConfigParser()
        cls.rauc.read(RAUC_CONFIG)
        cls.uboot = UBOOT_PATCH.read_text(encoding="utf-8")
        cls.mount = MOUNT_PATCH.read_text(encoding="utf-8")

    def test_rootfs_slots_define_expected_devices_and_bootnames(self):
        self.assertEqual(self.rauc["slot.rootfs.0"]["device"], "/dev/mmcblk0p12")
        self.assertEqual(self.rauc["slot.rootfs.0"]["bootname"], "A")
        self.assertEqual(self.rauc["slot.rootfs.1"]["device"], "/dev/mmcblk0p13")
        self.assertEqual(self.rauc["slot.rootfs.1"]["bootname"], "B")

    def test_bootfs_and_vendorfs_follow_their_rootfs_slot(self):
        expected = {
            "slot.bootfs.0": ("/dev/mmcblk0p8", "rootfs.0"),
            "slot.bootfs.1": ("/dev/mmcblk0p9", "rootfs.1"),
            "slot.vendorfs.0": ("/dev/mmcblk0p10", "rootfs.0"),
            "slot.vendorfs.1": ("/dev/mmcblk0p11", "rootfs.1"),
        }
        for section, (device, parent) in expected.items():
            with self.subTest(section=section):
                self.assertEqual(self.rauc[section]["device"], device)
                self.assertEqual(self.rauc[section]["parent"], parent)

    def test_uboot_selects_matching_slot_partitions(self):
        expected = {
            "A": ("8", "/dev/mmcblk0p12"),
            "B": ("9", "/dev/mmcblk0p13"),
        }
        for slot, (boot_partition, rootfs) in expected.items():
            with self.subTest(slot=slot):
                self.assertRegex(
                    self.uboot,
                    rf'setenv raucslot {slot}; setenv distro_bootpart {boot_partition};',
                )
                self.assertRegex(
                    self.uboot,
                    rf'setenv rauc_root {re.escape(rootfs)};',
                )

    def test_mount_logic_uses_a_and_b_suffixes(self):
        self.assertIn('A) echo "1"', self.mount)
        self.assertIn('B) echo "2"', self.mount)
        self.assertIn('search_label="${part_label}${RAUC_SUFFIX}"', self.mount)


if __name__ == "__main__":
    unittest.main()
