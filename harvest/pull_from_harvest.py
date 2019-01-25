import requests
import json
import logging
import os

logger = logging.getLogger()


class Harvest:

    # TODO: Merge with other Call_Harvest Module in the Serverless deployment
    def call_harvest(self, url, payload):
        payload = json.dumps(payload)
        try:
            response = requests.get(
                url, timeout=10, data=payload,
                headers={'Harvest-Account-ID': '480685',
                         'Authorization': 'Bearer ' + str(os.environ.get('HARVEST_API_KEY')),
                         'User-Agent': 'New Starter Python Script',
                         'Content-Type': 'application/json'}
            )
        except Exception as error:
            logger.error("There has been an error whilst calling Harvest: " + str(error))
            return False

        parsed_response = json.loads(response.text)

        if response.status_code > 299:
            logger.error("Harvest has returned the code: " + str(response.status_code))
            return False
        logger.info("Success calling Harvest")
        return parsed_response

    def pull_all_timesheet_data_for_timeoff(self, start_date, end_date):
        url_to_call = "https://api.harvestapp.com/v2/time_entries"
        payload = {
            "project_id": 19352708, # Infinity Works 'Time Off' project code
            "from": start_date,
            "to": end_date
        }

        harvest_data = {
            "users": {}
        }
        carry_on = True

        while carry_on:
            response = self.call_harvest(url_to_call, payload)

            try:
                test_json = response['time_entries']
            except KeyError:
                logger.critical("Invalid JSON returned by Harvest when calling time sheet data for the project 'Other'")
                return False

            for timeoff in response['time_entries']:
                if timeoff['task']['id'] == 11362306 and timeoff['is_locked'] == True: # Sick leave project code and locked
                    # Add the sick leave to the harvest_data JSON for returning
                    try:
                        harvest_data['users'][str(timeoff['user']['id'])].append({
                            "spent_date": timeoff['spent_date'],
                            "hours": timeoff['hours']
                        })
                    except:
                        # If the user does not exist in harvest_data this will create them with their sick leave
                        harvest_data['users'][str(timeoff['user']['id'])] = [{
                            "spent_date": timeoff['spent_date'],
                            "hours": timeoff['hours']
                        }]

            # If there is a next page then this will find it and replace the url_to_call with the new one
            if response['links']['next'] != None:
                url_to_call = response['links']['next']
            else:
                carry_on = False

        return harvest_data

    def pull_employees_with_ids_and_emails(self):
        url_to_call = "https://api.harvestapp.com/v2/users"
        payload = {}

        user_data = {
            "users": {}
        }
        carry_on = True

        while carry_on:
            response = self.call_harvest(url_to_call, payload)

            try:
                test_json = response['users'][0]['email']
            except KeyError:
                logger.error("Invalid JSON returned by Harvest when calling time sheet data for the project 'Other'")
                return False

            # Creates an array of ID's as PK and emails within
            for employee in response['users']:
                    user_data['users'][str(employee['id'])] = {
                        "email": employee['email']
                    }

            if response['links']['next'] != None:
                url_to_call = response['links']['next']
            else:
                carry_on = False

        return user_data

    def convert_ids_to_email(self, employee_ids_with_sick_hours, user_ids_with_emails):
        # Goes through each employee ID which has Sick leave
        for employee_with_sick in employee_ids_with_sick_hours['users'].keys():
            # Gets their email by using the PK from employee_with_sick to match with the PK in user_ids_with_emails

            # Sets a new bit of JSON with the email as the PK and their sick leave inside and then deletes the old PK
            try:
                employees_email = user_ids_with_emails['users'][employee_with_sick]['email']
                employee_ids_with_sick_hours['users'][employees_email] = employee_ids_with_sick_hours['users'][employee_with_sick]
                del employee_ids_with_sick_hours['users'][employee_with_sick]
            except:
                pass
        return employee_ids_with_sick_hours

    def gather_timesheet_data(self, start_date, end_date):
        print("Gathering timesheet data")
        # Pulls all people from Harvest who have booked time off in sick leave
        employee_ids_with_sick_hours = self.pull_all_timesheet_data_for_timeoff(start_date, end_date)
        if not employee_ids_with_sick_hours:
            return False

        # Pulls back a list of employee ID's with Emails
        user_ids_with_emails = self.pull_employees_with_ids_and_emails()
        if not user_ids_with_emails:
            return False

        # Converts the employee ID's from employee_ids_with_sick_hours to their email address as a Key
        return self.convert_ids_to_email(employee_ids_with_sick_hours, user_ids_with_emails)
