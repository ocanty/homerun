import argparse
import CloudFlare
import requests
import json
import yaml
import schedule
import sys
import time

def get_current_ip(ip_server):
    """
        Gets the public IP for the current machine
        Returns False if the IP could not be retrieved

        Parameters
        ----------
        ip_server - A HTTP(S) path that when GET requested returns the IP of the requester
    """
    r = requests.get(ip_server)

    if r.status_code == 200:
        return r.text.strip('\n')
    return False
        
def add_subdomain_a_to_domain(cf,ip,subdomain,domain,proxy):
    """
        Adds an A record pointing at an ip 
        for the subdomain specified to the zone matching the domain parameter

        Parameters
        ----------
        cf - Cloudflare Python API (v4)
        ip - IP address to point the A record at
        subdomain - Name of the A record
        domain - Zone the A record should be in
        proxy - Should this IP be proxified through Cloudflare's system?
    """
    # search for zones with our domain
    zones = cf.zones.get(params={'name':domain})

    # there should only be one zone per site
    if len(zones) == 1:
        zone = zones[0]

        # search dns records on this zone, did we previously set a record?
        records = cf.zones.dns_records.get(zone['id'],params={
            'type': 'A',
            # weirdly, cloudflare saves the name as <subdomain>.<domain> i.e 'homerun.ocanty.com'
            # rather than just 'homerun'
            # this format used for the GET request on this entity is different than the format
            # used for POST & PUT
            # so we have to search like this instead
            'name': subdomain + '.' + domain 
        })

        # we didnt find a current record, lets create a new one
        if(len(records) == 0):
            print(cf.zones.dns_records.post(zone['id'], data={
                'type':'A',
                'name':subdomain, 
                'content':ip,
                'ttl':120,
                'proxied': proxy
            }))
        else:
            cur_record = records[0]
            
            # dont bother doing the update if the current record has the same IP address
            if cur_record['content'] == ip:
                print('IP has not changed, not updating')
                return

            print(cf.zones.dns_records.put(zone['id'], records[0]['id'], data={
                'type':'A',
                'name':subdomain,
                'content':ip,
                'ttl':120,
                'proxied': proxy
            }))

def add_record_in_config(cf,config):
    """
        Adds an A record pointed to the IP retrieved at ip_server
        for the subdomain, domain and proxy status specified in config
    """
    # try to get current ip
    ip = get_current_ip(config['ip_server'])

    if not ip:
        print("Could not retrieve IP, no DNS records were modified")
        return

    add_subdomain_a_to_domain(cf, ip, config['subdomain'], config['domain'], config['proxy'])

def homerun():
    """
        Main task, verifies config and starts the job
    """
    try:
        # we need to verify that all the required options came from either a config file 
        # or were passed as command line arguments
        config = { }
        options_present = set()

        # command line parser setup
        parser = argparse.ArgumentParser()        
        parser.add_argument('-config', default='config.yml',nargs=1, type=str)
        
        args = parser.parse_args()
        
        try:
            config_file = open(args.config)
            config = yaml.safe_load(config_file)
        except FileNotFoundError:
            print('config.yml not found!', file=sys.stderr)
            exit(1)

        check_config = ['ip_server','subdomain','domain','proxy','update_every']
        
        for param in check_config:
            if not param in config:
                print(f'Missing `{param}` parameter in config.yml!',file=sys.stderr)
                exit(1)

        cf = CloudFlare.CloudFlare()
        job = lambda: add_record_in_config(cf,config)

        # run now
        job()

        # schedule it
        schedule.every(config['update_every']).minutes.do(job)

        # process scheduling
        while True: 
            schedule.run_pending()

            # process jobs in 60 sec intervals, because the minimum possible update time above is 1 min
            time.sleep(60)

    except CloudFlare.exceptions.CloudFlareAPIError as e:
        print(f'API error: {int(e)}, {str(e)}!',file=sys.stderr)
        
        # If user doesn't specify an API key, the Cloudflare exception will have X-Auth in it
        if 'X-Auth' in str(e):
            print(f'Did you configure your Cloudflare API key properly?',file=sys.stderr)

        exit(1)
