import unittest
from HikeNRW.HikeNRW.komoot.komoot import get_komoot_dict
from HikeNRW.HikeNRW.komoot.url_parser import extract_komoot_id


class TestTemplate(unittest.TestCase):
    def test_dict(self):
        k_id = extract_komoot_id("https://www.komoot.com/de-de/tour/1712378058")
        self.assertEqual(k_id, "1712378058")
        result = get_komoot_dict(k_id)
        self.assertEqual(result["difficulty"], "difficult")


if __name__ == '__main__':
    unittest.main()
