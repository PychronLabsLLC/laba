import unittest

from hardware.linear_drive import LinearDrive


class LinearDriveTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._drive = LinearDrive()

    def test_map_raw(self):
        # define map raw test
        self.assertEqual(self._drive.map_raw(50), 0.5)

    def test_map_data(self):
        # define map data test
        self.assertEqual(self._drive.map_data(0.5), 50)

    def test_map_data_zero(self):
        self.assertEqual(self._drive.map_data(0), 0)

    def test_map_raw_zero(self):
        self.assertEqual(self._drive.map_raw(0), 0)

    def test_map_data_max(self):
        self.assertEqual(self._drive.map_data(1), 100)

    def test_map_raw_max(self):
        self.assertEqual(self._drive.map_raw(100), 1)

    def test_map_data_mid(self):
        self.assertEqual(self._drive.map_data(0.5), 50)

    def test_map_raw_mid(self):
        self.assertEqual(self._drive.map_raw(50), 0.5)

    # def test_something(self):
    #     self.assertEqual(True, False)  # add assertion here


if __name__ == "__main__":
    unittest.main()
