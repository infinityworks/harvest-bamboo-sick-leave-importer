from harvest.pull_from_harvest import Harvest
from bamboo.pull_from_bamboo import PullFromBamboo
from bamboo.set_to_bamboo import SetToBamboo
import logging
import datetime
from dateutil.relativedelta import *
from datetime import date, timedelta
import numpy as np

logger = logging.getLogger()


class Compare:

    def __init__(self):
        self.harvest = Harvest()
        self.pull_from_bamboo = PullFromBamboo()
        self.set_to_bamboo = SetToBamboo()

    def gather_harvest_sick_entries(self, start_date, end_date):
        return self.harvest.gather_timesheet_data(start_date, end_date)

    def gather_bamboo_time_off_by_email(self, email, start_date, end_date):
        return self.pull_from_bamboo.pull_sick_leave_for_employee_from_bamboo_by_email(email, start_date, end_date)

    def harvest_dates_json_to_list(self, harvest_sick_dates):
        harvest_dates = []
        for date in harvest_sick_dates:
            harvest_dates.append(date['spent_date'])

        return harvest_dates

    def compare_data(self, harvest_sick_dates, start_date, end_date):
        unsuccessful_bamboo_put_requests = 0
        # Run through 1 employee at a time by their email
        for harvest_sick_email in harvest_sick_dates['users'].keys():
            # Get the days they have already booked off in Bamboo inbetween the dates we are setting for
            find_dates_in_bamboo_success, dates_booked_off_in_bamboo = self.gather_bamboo_time_off_by_email(harvest_sick_email, start_date, end_date)
            if not find_dates_in_bamboo_success:
                # TODO: Slack the employee email for manual entry
                print("Fail")

            harvest_dates = self.harvest_dates_json_to_list(harvest_sick_dates['users'][harvest_sick_email])
            print(harvest_sick_email)
            print("-- Harvest Dates --")
            print(harvest_dates)

            if len(dates_booked_off_in_bamboo) != 0:
                # dates_to_set_in_bamboo = list(set(dates_booked_off_in_bamboo) in set(harvest_dates))
                dates_to_set_in_bamboo = np.setdiff1d(harvest_dates,dates_booked_off_in_bamboo)
            else:
                dates_to_set_in_bamboo = harvest_dates

            print("-- Dates booked off in Bamboo --")
            print(dates_booked_off_in_bamboo)

            print("-- Dates to set in Bamboo --")
            print(dates_to_set_in_bamboo)

            set_to_bamboo_success = self.set_sick_days_to_bamboo(harvest_sick_email, dates_to_set_in_bamboo)
            if not set_to_bamboo_success:
                print("Couldn't set")
                # TODO: Send to Slack which employee it couldn't pull Bamboo Records for

    def generate_xml_for_time_off_history(self, date, time_off_request_id, event_type, notes):
        generated_xml = f'''<history>
    <date>{date}</date>
    <eventType>{event_type}</eventType>
    <timeOffRequestId>{time_off_request_id}</timeOffRequestId>
    <note>{notes}</note>
    </history>
        '''
        return generated_xml

    def set_sick_days_to_bamboo(self, harvest_sick_email, set_dates):
        print("Setting data: " + str(set_dates))
        # Go through each sick day in the list
        for date in set_dates:
            employee_id = self.pull_from_bamboo.find_employee_id_by_email(harvest_sick_email)
            if not employee_id:
                logger.error("Could not find the employee ID within set_sick_days_to_bamboo")
                return False

            set_success, request_response = self.set_to_bamboo.time_off_request(employee_id, "approved", date, date, 13, 1)
            if not set_success:
                logger.error(f"Could not set {harvest_sick_email} to Bamboo for the following dates: {set_dates} in request")
                # TODO: Message Slack if unsuccessful for somone to manually sort

            time_off_id = request_response['id']
            xml_payload = self.generate_xml_for_time_off_history(date, time_off_id, "used", "Automated from Harvest")
            set_success = self.set_to_bamboo.time_off_history(employee_id, xml_payload)
            if not set_success:
                logger.error(f"Could not set {harvest_sick_email} to Bamboo for the following dates: {set_dates} in history")
                # TODO: Message Slack if unsuccessful for somone to manually sort

        return True

    def run_all(self):
        print("Application started")

        todays_date = str(datetime.datetime.today().strftime('%Y-%m-%d'))
        two_months_behind_date = datetime.datetime.today() - relativedelta(months=2)
        two_months_behind_date = two_months_behind_date.strftime('%Y-%m-%d')

        harvest_sick_days = self.gather_harvest_sick_entries(two_months_behind_date, todays_date)
        if not harvest_sick_days:
            logger.critical("Aborting Script. Could not pull Harvest Data")
            # TODO: Send message to Slack telling the user about this
            exit(1)

        compare_success = self.compare_data(harvest_sick_days, two_months_behind_date, todays_date)
        if not compare_success:
            # TODO: Send Slack message saying the script has being aborted due to too many errors occurring
            exit(1)

def testing_comparing_dates_arrays():

    bamboo_matching_dates = []
    harvest_dates = ['2018-10-31', '2018-11-03']

    bamboo_start_date = date('2018-10-31')  # start date
    bamboo_end_date = date('2018-11-31')  # end date

    delta = bamboo_end_date - bamboo_start_date  # timedelta

    for i in range(delta.days + 1):
        bamboo_matching_dates.append(str(bamboo_start_date + timedelta(i)))
        print(str(bamboo_start_date + timedelta(i)))

    matches = set(bamboo_matching_dates) - set(harvest_dates)










if __name__ == '__main__':
    comp = Compare()
    comp.run_all()
    # testing_comparing_dates_arrays()
