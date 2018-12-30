
import CloudFlare
import requests
import json
import yaml
import schedule
import time

def get_current_ip(ip_server):
    """
        Gets the public IP for the current machine
        Returns False if the IP could not be retrieved

        Parameters
        ----------
        ip_server - A HTTP(S) path that when GET requested returns the IP of the client that requested it
    """
    r = requests.get(ip_server)

    if r.status_code == 200:
        return r.text.strip('\n')
    return False
        
def add_subdomain_a_to_domain(cf,ip,subdomain,domain,proxy):
    """
        Adds an A record for the subdomain specified to the zone pointed at domain

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

        # search dns records on this zone if we placed the subdomain in it before
        records = cf.zones.dns_records.get(zone['id'],params={
            'type': 'A',
            # weirdly, cloudflare sets the name as <subdomain>.<domain> for the GET
            # the name is different for the POST of the same request
            'name': subdomain + '.' + domain 
        })

        # we didnt find a previous record, lets create a new one
        if(len(records) == 0):
            print(cf.zones.dns_records.post(zone['id'], data={
                'type':'A',
                'name':subdomain,
                'content':ip,
                'ttl':120,
                'proxied': proxy
            }))
        else:
            # update the existing one if it already existed
            print(cf.zones.dns_records.put(zone['id'], records[0]['id'], data={
                'type':'A',
                'name':subdomain,
                'content':ip,
                'ttl':120,
                'proxied': proxy
            }))

def homerun():
    """
        Adds an A record pointed to the IP retrieved at ip_server
        for the subdomain, domain, proxy status specified in config.yml
    """
    try:
        config = yaml.safe_load(open("config.yml"))
 
        # make sure each possible config option was used
        check_config = ['ip_server','subdomain','domain','proxy','update_every']

        for param in check_config:
            if not param in config:
                print(f'Missing `{param}` parameter in config.yml!')
                return

        # try to get current ip
        ip = get_current_ip(config['ip_server'])

        if not ip:
            print("Could not retrieve IP, no DNS records were modified")
            return 

        # add the A record, update every x minutes as in config
        cf = CloudFlare.CloudFlare()
        job = lambda: add_subdomain_a_to_domain(cf, ip, config['subdomain'], config['domain'], config['proxy'])

        # run now
        job()

        # schedule it
        schedule.every(config['update_every']).minutes.do(job)

        # process scheduling
        while True: 
            schedule.run_pending()

            # process jobs in 60 sec intervals, because the minimum update time above is 1 min
            time.sleep(60)

    except CloudFlare.exceptions.CloudFlareAPIError as e:
        print(f'API error: {int(e)}, {str(e)}.')

        if 'X-Auth' in str(e):
            print(f'Did you configure your Cloudflare API key properly?')
        return

    except FileNotFoundError as e:
        print(f'Could not read config.yml! ({e})')
        return

if __name__ == '__main__':
    homerun()