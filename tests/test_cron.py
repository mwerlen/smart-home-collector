import unittest
import datetime
from freezegun import freeze_time
from shcollector.utils.cron import CronScheduler, Job, timezone


class TestCronScheduler(unittest.TestCase):

    def setUp(self):
        self.cron = CronScheduler()

    def check_run_date(self, test, run_date):
        assert test
        expected = timezone.localize(datetime.datetime(2020, 12, 9, 21, 35, 00))
        assert run_date == expected
        self.cron.cancel()

    @freeze_time("2020-12-09 21:34:59", tick=True)
    def test_next_run(self):
        self.cron.schedule(Job('test', "* * * * *", 1, self.check_run_date, {'test': True}, True))
        self.cron.start()


if __name__ == '__main__':
    unittest.main()
