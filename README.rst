=======
homerun
=======

homerun is a tool which updates an A record on Cloudflare whenever your public IP changes

This is useful when you want to access services hosted on your home pc/homelab whilst having a dynamic IP

Installation
------------

1. Clone the repo::

    git clone https://github.com/ocanty/homerun.git
2. Install dependencies::
     
    python3 setup.py install
3. Edit config.yml and setup configuration (example below)::
     
    ip_server: https://ifconfig.co/ip
    subdomain: homerun
    domain: ocanty.com
    proxy: false
    update_every: 10

4. Specify config options as you wish

    1. ``ip_server`` - A HTTP(S) service that when GET requested, returns the IP of the client (you probably won't need to change this)

    2. ``subdomain`` - The subdomain you want to point to your home IP

    3. ``domain`` - A Cloudflare site that is associated with your Cloudflare account

    4. ``proxy`` - Should we proxy this record through Cloudflare's system? (If this is ``true`` note that Cloudflare only supports some ports based on your plan)

    5. ``update_every`` - Check every x amount of minute for an IP change

5. Setup Cloudflare API keys

   1. `Follow Cloudflare instructions to retrieve your API key <https://support.cloudflare.com/hc/en-us/articles/200167836-Where-do-I-find-my-Cloudflare-API-key->`_.

   2. Create a file named ``.cloudflare.cfg`` in the project directory (the folder with setup.py, requirements.txt...)

   3. The file should look like as follows::

        [CloudFlare]
        email = <your cloudflare email>
        token = <global api key>

   4. `For more information about this click here <https://github.com/cloudflare/python-cloudflare#providing-cloudflare-username-and-api-key>`_.

6. Setup the systemd service

   1. Edit homerun.service, changing ``WorkingDirectory`` to the path you placed the repo::

        [Unit] 
        Description=Homerun Cloudflare Dynamic DNS daemon

        [Service]
        Type=simple
        WorkingDirectory=/home/ocanty/projects/homerun/
        ExecStart=python3 homerun.py
        ExecStop=pkill -f 'python3 homerun.py'

        [Install]
        WantedBy=multi-user.target 
   2. Tell systemd to use the service::

         sudo ln -s homerun.service /etc/systemd/system/homerun.service
         systemctl enable homerun.service
         systemctl start homerun.service
