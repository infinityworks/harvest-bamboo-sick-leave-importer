import unittest
from unittest import mock
from unittest.mock import MagicMock
from application import logging, Compare
from bamboo.pull_from_bamboo import PullFromBamboo




class TestApplication(unittest.TestCase):

    def setUp(self):
        logging.error = MagicMock()
        logging.info = MagicMock()
        self.comp = Compare()


    @mock.patch('bamboo.pull_from_bamboo.PullFromBamboo.pull_sick_leave_for_employee_from_bamboo_by_email')
    def test_match_logic(self, bamboo_mock):
        bamboo_mock.return_value = [['2019-01-18', '2019-02-01'], ['2018-10-01', '2018-10-21']]

        harvest_sick_dates = {
            "users": {
                "random.user@infinityworks.com": [{'spent_date': '2019-01-18', 'hours': 8.0}, {'spent_date': '2018-11-19', 'hours': 8.0}],
                "second.user@infinityworks.com": [{'spent_date': '2018-10-01', 'hours': 8.0}, {'spent_date': '2019-01-02', 'hours': 8.0}],
            }
        }

        start_date = "2018-10-29"
        end_date = "2019-02-01"


        return_value = self.comp.compare_data(harvest_sick_dates, start_date, end_date)