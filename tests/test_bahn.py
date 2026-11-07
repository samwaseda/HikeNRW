import unittest
from pathlib import Path

from HikeNRW.HikeNRW.bahn import Bahn, get_all_data, get_date

FIXTURES = Path(__file__).parent / "bahn"


def read_fixtures():
    return [path.read_text() for path in sorted(FIXTURES.glob("*.txt"))]


class TestBahn(unittest.TestCase):
    def test_get_date(self):
        for file_content in read_fixtures():
            with self.subTest(file_content=file_content[:60]):
                self.assertIsNotNone(get_date(file_content))

    def test_get_all_data(self):
        self.assertTrue(read_fixtures(), "No Bahn timetable fixtures found")
        for file_content in read_fixtures():
            with self.subTest(file_content=file_content[:60]):
                results = get_all_data(file_content)
                for station in results["arr_station"]:
                    self.assertNotIn("platform", station.lower())
                    self.assertNotIn("gleis", station.lower())
                for station in results["dep_station"]:
                    self.assertNotIn("platform", station.lower())
                    self.assertNotIn("gleis", station.lower())
                for dp, ar in zip(results["dep_time"], results["arr_time"]):
                    self.assertLess(dp, ar)
                bahn = Bahn(results).get_results()
                self.assertLess(bahn["starting_time"], bahn["arrival_time"])
                self.assertEqual(
                    len(bahn["train_schedule"].split("\n")), 2 * len(results)
                )

    def test_handles_german_labels_missing_platforms_and_midnight(self):
        itinerary = """Düsseldorf Hbf → Example
31.12.2026
RE 1 (12345)
Nach Somewhere
Ab 23:50 Düsseldorf Hbf, Gleis 4
An 00:10 Somewhere
S 1
Nach Example
Ab 00:20 Somewhere, platform 2
An 00:30 Example, platform 1
"""
        results = get_all_data(itinerary)

        self.assertEqual(results["dep_station"].tolist(), ["Düsseldorf Hbf", "Somewhere"])
        self.assertEqual(results["arr_station"].tolist(), ["Somewhere", "Example"])
        self.assertEqual(results["dep_platform"].tolist(), ["4", "2"])
        self.assertEqual(results["arr_platform"].tolist(), ["unknown", "1"])
        self.assertEqual(
            results["arr_time"].iloc[0].date().isoformat(), "2027-01-01"
        )
        self.assertLess(results["dep_time"].iloc[1], results["arr_time"].iloc[1])

    def test_get_date_rejects_missing_or_ambiguous_dates(self):
        with self.assertRaises(ValueError):
            get_date("No date here")
        with self.assertRaises(ValueError):
            get_date("01.01.2026 and 02.01.2026")


if __name__ == "__main__":
    unittest.main()
