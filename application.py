from harvest.pull_from_harvest import Harvest
from bamboo.pull_from_bamboo import PullFromBamboo
from bamboo.set_to_bamboo import SetToBamboo
import logging
import datetime
from dateutil.relativedelta import *

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

    def compare_data(self, harvest_sick_dates, start_date, end_date):
        unsuccessful_bamboo_put_requests = 0
        # Run through 1 employee at a time by their email
        for harvest_sick_email in harvest_sick_dates['users'].keys():
            # Get the days they have already booked off in Bamboo inbetween the dates we are setting for
            existing_days_in_bamboo = self.gather_bamboo_time_off_by_email(harvest_sick_email, start_date, end_date)
            if existing_days_in_bamboo != False:
                # If they have no days sick in Bamboo between these date then set the data straight away
                if existing_days_in_bamboo == True:
                    set_success = self.set_sick_days_to_bamboo(harvest_sick_email, harvest_sick_dates['users'][harvest_sick_email])
                    if not set_success:
                        return False
                else:
                    temp_sick_days = []
                    # Set the users sick days which aren't in Bamboo to the temp_sick_days array
                    for harvest_sick_day in harvest_sick_dates['users'][harvest_sick_email]:
                        for dates in existing_days_in_bamboo:
                            set_to_list = True
                            if harvest_sick_day['spent_date'] >= dates[0] and harvest_sick_day['spent_date'] <= dates[0]:
                                set_to_list = False
                                break
                        if set_to_list:
                            temp_sick_days.append(harvest_sick_day)

                    # Once the list is complete, set the sick days to Bamboo
                    set_success = self.set_sick_days_to_bamboo(harvest_sick_email, temp_sick_days)
                    if not set_success:
                        # TODO: Send message to Slack on fail - Manually sort or rerun
                        unsuccessful_bamboo_put_requests += 1
                        # If there has been too many errors then the script will stop. This is to stop spamming Slack
                        if unsuccessful_bamboo_put_requests > 10:
                            logger.critical("Stopping the script. Too many put requests to Bamboo has failed.")
                            return False
            else:
                print("Unsuccessful call")
                # TODO: Send to Slack which employee it couldn't pull Bamboo Records for

    def set_sick_days_to_bamboo(self, harvest_sick_email, set_dates):
        print("Setting data: " + str(set_dates))
        # Go through each sick day in the list
        for date in set_dates:
            employee_id = self.pull_from_bamboo.find_employee_id_by_email(harvest_sick_email)
            if not employee_id:
                logger.error("Could not find the employee ID within set_sick_days_to_bamboo")
                return False

            # Work out whether to book a full day or half day of sick to Bamboo.
            if date['hours'] <= 4:
                days_spent = 0.5
            else:
                days_spent = 1
            print("--- Setting Into Bamboo ---")
            print(employee_id)
            print(date['spent_date'])
            print(days_spent)
            set_success = self.set_to_bamboo.time_off_request(employee_id, "approved", date['spent_date'], date['spent_date'], 13, days_spent)
            if not set_success:
                print("No Success")
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



if __name__ == '__main__':
    comp = Compare()
    comp.run_all()