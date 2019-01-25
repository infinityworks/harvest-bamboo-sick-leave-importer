from bambooHRappy.bambooHRappy import bambooHrApi
import os
import logging
from datetime import date, timedelta


logger = logging.getLogger()

class PullFromBamboo:

    def __init__(self):
        self.bamboo = bambooHrApi(os.environ.get('BAMBOO_TOKEN'), 'infinityworks')

    def find_employee_id_by_email(self, email):
        print(email)
        try:
            directory = self.bamboo.get_employee_directory()
        except Exception as error:
            logger.error('Could not pull back the employee directory: ' + str(error))
            return False

        for employee in directory['employees']:
            if email == employee['workEmail']:
                return employee['id']

    def find_sick_leave_in_bamboo(self, all_employees_leave_data, employee_id):
        employee_leave = []
        for leave_data in all_employees_leave_data:
            # For some weird reason Bamboo returns Christmas and Boxing day without any context...
            try:
                test = leave_data['name']
            except KeyError as error:
                logger.error("Bamboo has returned invalid JSON: " + str(error))
                return False, []

            try:
                if int(leave_data['employeeId']) == int(employee_id):
                    employee_leave.append([leave_data['start'], leave_data['end']])
            except:
                pass

        if len(employee_leave) > 0:
            return True, employee_leave
        return True, []

    def pull_all_employees_leave_data(self, start_date, end_date):
        try:
            return self.bamboo.get_whos_out(start_date, end_date)
        except Exception as error:
            logger.error("Could not pull back all employee leave data: " + str(error))
            return False

    def flatten_dates(self, employee_sick_leave):
        bamboo_dates = []

        for dates in employee_sick_leave:
            start_date = dates[0].split("-")
            end_date = dates[1].split("-")

            bamboo_start_date = date(int(start_date[0]), int(start_date[1]), int(start_date[2]))  # start date
            bamboo_end_date = date(int(end_date[0]), int(end_date[1]), int(end_date[2]))  # end date

            delta = bamboo_end_date - bamboo_start_date  # timedelta

            for i in range(delta.days + 1):
                bamboo_dates.append(str(bamboo_start_date + timedelta(i)))

        return bamboo_dates

    # Entry Point
    def pull_sick_leave_for_employee_from_bamboo_by_email(self, email, start_date, end_date):
        print("Pulling Sick leave from Bamboo")
        all_employees_leave_data = self.pull_all_employees_leave_data(start_date, end_date)
        if not all_employees_leave_data:
            print("Could not pull all leave data")
            logger.error("Could not pull employeeleave data from Bamboo")
            return False, []

        employee_id = self.find_employee_id_by_email(email)
        if not employee_id:
            print("Could not find employee ID")
            logger.error("Could not pull the employee ID from Bamboo by their email")
            return False, []

        find_sick_success, employee_sick_leave = self.find_sick_leave_in_bamboo(all_employees_leave_data, employee_id)
        if not find_sick_success:
            return False, []


        return True, self.flatten_dates(employee_sick_leave)
