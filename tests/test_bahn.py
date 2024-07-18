import glob
import unittest
from HikeNRW.HikeNRW.bahn import get_date, get_all_data
from datetime import datetime, timedelta


class TestBahn(unittest.TestCase):
    def test_get_date(self):
        for filename in glob.glob("bahn/*.txt"):
            with open(filename, "r") as f:
                file_content = f.read()
            self.assertLess(
                get_date(file_content),
                datetime.today() + timedelta(days=365)
            )
            self.assertGreater(
                get_date(file_content),
                datetime(year=2024, month=1, day=1)
            )

    def test_get_all_data(self):
        for filename in glob.glob("bahn/*.txt"):
            with open(filename, "r") as f:
                file_content = f.read()
            results = get_all_data(file_content)
            for station in results["arr_station"]:
                self.assertFalse("platform" in station)
            for station in results["dep_station"]:
                self.assertFalse("platform" in station)
            for dp, ar in zip(results["dep_time"], results["arr_time"]):
                self.assertLess(dp, ar)


if __name__ == '__main__':
    unittest.main()
