import unittest

import pandas as pd

from src.indicators import calculate_rci


class TestIndicators(unittest.TestCase):
    def test_calculate_rci_100(self):
        """
        RCI計算のテスト(RCI=100)
        テストデータ参考: https://kabu.com/investment/guide/technical/14.html
        """
        test_data = pd.DataFrame({"close": [500, 510, 515, 520, 530]})

        # 期間を変えてテスト
        period = 5
        expected = 100.0

        actual = calculate_rci(test_data, period)
        self.assertEqual(actual, expected)

    def test_calculate_rci_minus100(self):
        """
        RCI計算のテスト(RCI=-100)
        テストデータ参考: https://kabu.com/investment/guide/technical/14.html
        """
        test_data = pd.DataFrame({"close": [530, 520, 515, 510, 500]})

        # 期間を変えてテスト
        period = 5
        expected = -100.0

        actual = calculate_rci(test_data, period)
        self.assertEqual(actual, expected)
