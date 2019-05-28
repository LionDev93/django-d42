from django.core.management.base import BaseCommand
import requests

from project.apps.device42.models import CurrentCustomers


class Command(BaseCommand):
    def handle(self, *args, **options):
      with open('/home/damato/credentials/sfpass.txt') as f:  # sfpass.txt has username:password for salesforce login
        credentials = [x.strip().split(':') for x in f.readlines()]
        consumer_key = '3MVG9xOCXq4ID1uEQnNXu44BEcLArpjzPZDFaOgFmc.0uLOWRcLJ.w9I9RF5EW_0KIV3CBI9Z_Lo_b_fPLUlC'
        consumer_secret = '3803050499083620233'
        username = credentials[0][0]
        password = credentials[0][1]

        payload = {
            'grant_type': 'password',
            'client_id': consumer_key,
            'client_secret': consumer_secret,
            'username': username,
            'password': password
        }

        r = requests.post("https://login.salesforce.com/services/oauth2/token",
            headers={"Content-Type":"application/x-www-form-urlencoded"},
            data=payload)

        request_data_json = r.json()
        session_id = 'Bearer ' + request_data_json['access_token']
        headers = {"Authorization":session_id,
                 "Content-Type": "application/xml; charset=UTF-8"}
        qry = "SELECT+Email+FROM+Contact+where+AccountId+in+(SELECT+AccountId+FROM+Opportunity+where+stagename+=+'Closed Won')"
        # qry = "SELECT+Email+FROM+Contact+where+AccountId+in+(SELECT+Id+FROM+Account+where+rating+=+'active')"

        more_records = False
        next_url = ""
        base_url = "https://device42.cloudforce.com"
        while True:
            if more_records:
                req_url = "https://device42.cloudforce.com" + next_url
                r = requests.get(req_url, headers=headers)
            else:
                req_url = base_url + "/services/data/v20.0/query/?q=%s"
                r = requests.get(req_url % qry, headers=headers)
                # SELECT+count()+FROM+Opportunity+WHERE+CreatedDate+>=+this_month

            r_json = r.json()
            records = r_json['records']
            for record in records:
                try:
                    email = record['Email']
                    if email and '@' in email:
                        email_domain = email.split('@')[1]
                        if not CurrentCustomers.objects.filter(email_domain=email_domain):
                            CurrentCustomers.objects.create(email_domain=email_domain)
                except Exception as Err:
                    print 'Error parsing %s: %s' % (record, str(Err))

            more_records = 'nextRecordsUrl' in r_json.keys()
            if more_records:
                next_url = r_json['nextRecordsUrl']
            else:
                break
