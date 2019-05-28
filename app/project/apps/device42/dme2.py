#!/usr/bin/env python

"""
Python wrapper for the dnsmadeeasy RESTful API V2.0.
"""

import requests
import json
from time import strftime, gmtime
import hashlib
import hmac


class DME2:
    def __init__(self, apikey, secret):
        self.api = apikey
        self.secret = secret
        self.baseurl = 'http://api.dnsmadeeasy.com/V2.0/'
        
    def _headers(self):
        currTime = self._get_date()
        hashstring = self._create_hash(currTime)
        headers = {'x-dnsme-apiKey': self.api, 
                   'x-dnsme-hmac': hashstring,
                   'x-dnsme-requestDate': currTime,
                   'content-type': 'application/json'}
        return headers
    
    def _get_date(self):
        return strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())

    def _create_hash(self, rightnow):
        return hmac.new(self.secret.encode(), rightnow.encode(), hashlib.sha1).hexdigest()
    
    def _rest_connect(self, resource, method='GET', data=''):
        r = requests.request(method, self.baseurl + resource, json=data, headers=self._headers())
        if (r.status_code == 200 or  r.status_code == 201):
            if r.json:
                return r.json() 
            else:
                return r.text
        else:
            print(r.text)
            raise Exception("Error talking to dnsmadeeasy: " + str(r.status_code))               

    ##########################################################################
    #  /dns/managed - operate on multiple domains for your account
    ##########################################################################
    
    def get_domains(self):
        """
        Returns list of all domains for your account
        """
        return self._rest_connect('dns/managed', 'GET')['data']
    
    def delete_domains(self, domainIds):
        """
        Deletes all domains for your account specified as a list of their IDs.
        """
        return self._rest_connect('dns/managed', 'DELETE', json.dumps(domainIds))
    
    def update_domains(self, domainIds, data):
        """
        Updates multiple domains specified by their identifiers.
        """
        domainsData = {'ids': domainIds}
        domainsData.update(data)
        return self._rest_connect('dns/managed', 'PUT', json.dumps(domainsData))
    
    def add_domains(self, domains):
        """
        Creates multiple domains based on a list of domain names.
        Returns list of domain IDs of created domains.
        """
        data = {'names': domains}
        return self._rest_connect('dns/managed', 'POST', json.dumps(data))

    ##########################################################################
    #  /dns/managed/{domainId} - operate on a single domain
    ##########################################################################
        
    def get_domain(self, domainId):
        """
        Returns the domain specified by its ID.
        """       
        return self._rest_connect('dns/managed/' + str(domainId), 'GET')
    
    def delete_domain(self, domainId):
        """
        Deletes the specified domain by its ID.
        """
        return self._rest_connect('dns/managed/' + str(domainId), 'DELETE')

    def update_domain(self, domainId, data):
        """
        Updates a domain based on the domain identifier with new data.
        """
        return self._rest_connect('dns/managed/' + str(domainId), 'PUT', json.dumps(data))
   
    # TODO: Test EVERYTHING BELOW HERE
    
    ##########################################################################
    #    /dns/managed/{domainId}/records - operate on multiple records for 
    #       one domain
    ##########################################################################
    
    def get_records_from_domain(self, domainId):
        """
        Returns all records for the specified domain.
        """
        return self._rest_connect('dns/managed/' + str(domainId) + '/records')['data']
    
    def delete_records_from_domain(self, domainId, recordIds):
        """
        Deletes the specified records using a list of record identifiers.
        Warning: This is irreversible!
        """
        data = {'ids': recordIds}
        return self._rest_connect('dns/managed/' + str(domainId) + '/records', 'DELETE', json.dump(data))

    def add_record_to_domain(self, domainId, data):
        return self._rest_connect('dns/managed/' + str(domainId) + '/records', 'POST', data)
    
    
    def update_record_by_id(self, domainId, recordId, data):
        return self._rest_connect('dns/managed/' + str(domainId) + '/records/' + str(recordId), 'PUT', data)


    def delete_record(self, domainId, recordId):
        return self._rest_connect('dns/managed/' + str(domainId) + '/records/' + str(recordId), 'DELETE')
    

    def get_soa_records(self):
        """
        Displays all custom SOA records defined for an account.
        """
        return self._rest_connect('dns/soa', 'GET')
    
    def assign_soa_record(self, domainIds, soaId):
        """
        Assigns the domains with the custom SOA record.
        """
        data = {'ids': [str(domainId) for domainId in domainIds], 'soaId': str(soaId), }
        return self._rest_connect('dns/managed', 'PUT', json.dumps(data))
    
    def add_domains_and_assign_soa(self, domains, soaId):
        """
        Creates the domains and assign the custom SOA to them.
        """
        data = {'soaId': str(soaId), 'names': domains}
        return self._rest_connect('dns/managed', 'POST', json.dumps(data))

    def get_vanity_ns(self):
        """
        Returns a list of all vanity name server groups public and private
         defined within the account.
        """
        return self._rest_connect('dns/vanity', 'GET')['data']
    
    def get_templates(self):
        """
        Returns all public and private templates within the account.
        """
        return self._rest_connect('dns/template', 'GET')
    
    def get_template(self, templateId):
        """
        Returns the records within a template based on the template ID
        including their associated record IDs.
        """
        return self._rest_connect('dns/template/' + str(templateId) + '/records?type=A', 'GET')
    
    def delete_template_from_record(self, templateId, recordId):
        """
        Deletes the record from the template.
        """
        return self._rest_connect('dns/template/' + str(templateId) + '/records?ids=' + str(recordId), 'DELETE')
    
    def get_transfer_acls(self):
        """
        Returns the list of all AXFR transfer ACL's.
        """
        return self._rest_connect('dns/transferAcl', 'GET')['data']
        
    def get_security_folders(self):
        """
        Returns a list of folders defined in the account.
        """
        return self._rest_connect('security/folder', 'GET')  

    def get_query_usage_all(self):
        """
        Returns full report of query traffic for all months and domains.
        """
        return self._rest_connect('usageApi/queriesApi', 'GET')
        
    def get_query_usage_by_month(self, year, month):
        """
        Returns query usage for month for all domains.
        """
        return self._rest_connect('usageApi/queriesApi/%s/%s' % (str(year), str(month)))
    
    def get_query_usage_by_month_and_domain(self, year, month, domainId):
        """
        Returns query usage for month for the domain.
        """
        return self._rest_connect('usggeApi/queriesApi/' +
                                  str(year) + '/' + str(month) + 
                                  '/managed/' + str(domainId), 'GET')
    
    # TODO: rename?
    def set_dns_failover(self, recordId, data):
        """
        Configures DNS Failover for the record.
        """
        return self._rest_connect('monitor/' + str(recordId), 'PUT', json.dump(data))
    
    # TODO: /dns/secondary
    def secondary_dns_add_domains(self, domains, ipSetId):
        """
        Creates domains under secondary DNS management with the assigned
        IP Set.
        """
        data = {'names': domains, 'ipSetId': str(ipSetId)}
        return self._rest_connect('dns/secondary', 'POST', json.dump(data))
    
    # TODO: /dns/ipSet
    def secondary_dns_assign_ip_set(self, domainIds, ipSetId):
        """
        Assigns IP Set to the domains under secondary DNS management.
        """
        data = {'ids': [str(domainId) for domainId in domainIds], 'ipSetid': str(ipSetId)}
        return self._rest_connect('dns/secondary', 'PUT', json.dump(data))
    
    def secondary_dns_delete_domain(self, domainId):
        """
        Delete domain under secondary DNS management.
        """
        return self._rest_connect('dns/secondary' + str(domainId), 'DELETE')
    
    def get_ip_sets(self):
        """
        Returns a list of secondary IP Sets.
        """
        return self._rest_connect('dns/secondary/ipSet', 'GET')['data']
    
    def add_ip_set(self, name, ips):
        """
        Creates a secondary DNS IP Set.
        """
        data = {'name': name, 'ips': ips}
        return self._rest_connect('dns/secondary/ipSet', 'POST', json.dump(data))
    
    def update_ip_set_by_domain(self, domainId, ipSetId, folderId):
        """
        Assigns an IP Set to a secondary DNS domain.
        """
        data = {'ipSetId': int(ipSetId), 'folderId': int(folderId)}
        return self._rest_connect('dns/secondary/' + str(domainId), 'PUT', data)