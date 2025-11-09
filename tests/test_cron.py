import unittest
import datetime

import pytz
from freezegun import freeze_time
from shcollector.utils.cron import CronScheduler, Job, timezone

tz_utc = datetime.timezone(datetime.timedelta(hours=0))
tz_utc_plus_un = datetime.timezone(datetime.timedelta(hours=1))
tz_utc_plus_deux = datetime.timezone(datetime.timedelta(hours=2))


class TestCronScheduler(unittest.TestCase):

    def setUp(self):
        self.cron = CronScheduler()

    def check_run_date(self, expected_date):
        def called_function(test, run_date):
            assert test
            assert run_date.astimezone(tz_utc) == expected_date.astimezone(tz_utc)
            self.cron.cancel()

        return called_function

    @freeze_time("2020-12-09 21:34:59", tick=True)
    def test_next_run(self):
        expected = timezone.localize(datetime.datetime(2020, 12, 9, 21, 35, 00))
        self.cron.schedule(Job('test', "* * * * *", 1, self.check_run_date(expected), {'test': True}, True))
        self.cron.start()

    @freeze_time(datetime.datetime(2025, 10, 11, 12, 00, 00, tzinfo=tz_utc_plus_deux), tick=True)
    def test_cron_at_specific_timezone(self):
        expected = datetime.datetime(2025, 10, 11, 12, 1, 00, tzinfo=tz_utc_plus_deux)
        self.cron.schedule(Job('test', "* * * * *", 1, self.check_run_date(expected), {'test': True}, True))
        self.cron.start()

    @freeze_time(datetime.datetime(2025, 10, 26, 2, 59, 59, tzinfo=tz_utc_plus_deux), tick=True)
    def test_cron_at_dst(self):
        expected = datetime.datetime(2025, 10, 26, 2, 00, 00, tzinfo=tz_utc_plus_un)
        self.cron.schedule(Job('test', "* * * * *", 1, self.check_run_date(expected), {'test': True}, True))
        self.cron.start()

    @freeze_time(datetime.datetime(2025, 1, 1, 1, 0, 59, tzinfo=tz_utc), tick=True)
    def test_cron_error(self):
        expected = datetime.datetime(2025, 1, 1, 1, 2, 00, tzinfo=tz_utc)
        self.cron.schedule(Job('test', "* * * * *", 1, self.check_run_date(expected), {'test': True}, True))
        try:
            self.cron.start()
        except AssertionError:
            assert True


if __name__ == '__main__':
    unittest.main()
