import os
from bambooHRappy.bambooHRappy import bambooHrApi
import logging

logger = logging.getLogger()

class SetToBamboo:

    def __init__(self):
        self.bamboo = bambooHrApi(os.environ.get('BAMBOO_TOKEN'), 'infinityworks')

    def time_off_request(self, employee_id, approval_status, start_date, end_date, time_off_type_id, amount_of_days):
        try:
            response = self.bamboo.time_off_request(employee_id, approval_status, start_date, end_date, time_off_type_id, amount_of_days)
        except Exception as error:
            logger.error("Could not post the time off request: " + str(error))
            return False
        return True
