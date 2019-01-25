import os
from bambooHRappy.bambooHRappy import bambooHrApi
import logging
import json

logger = logging.getLogger()

class SetToBamboo:

    def __init__(self):
        self.bamboo = bambooHrApi(os.environ.get('BAMBOO_TOKEN'), 'infinityworks')

    def time_off_request(self, employee_id, approval_status, start_date, end_date, time_off_type_id, amount_of_days):
        try:
            response = self.bamboo.time_off_request(employee_id, approval_status, start_date, end_date, time_off_type_id, amount_of_days)
            print("-- PUT RESPONSE --")
            time_off_response = json.loads(response.text)
        except Exception as error:
            logger.error("Could not post the time off request: " + str(error))
            return False, None
        return True, time_off_response

    def time_off_history(self, employee_id, xml_payload):
        try:
            response = self.bamboo.time_off_history(employee_id, xml_payload)
            print(response)
        except Exception as error:
            logger.error("Could not post the time off request: " + str(error))
            return False
        return True
