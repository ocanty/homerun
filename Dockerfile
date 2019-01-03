FROM python:alpine3.7
LABEL maintainer="git@ocanty.com"

COPY . /homerun
WORKDIR /homerun

# install all python requirements
RUN pip3 install -r ./requirements.txt

# install our template tool
RUN pip install j2cli

ARG IP_SERVER=https://ifconfig.co/ip
ARG SUBDOMAIN
ARG DOMAIN 
ARG PROXY=False
ARG UPDATE_EVERY=10

# setup config via template (j2cli will use the env variables)
RUN export ip_server=${IP_SERVER}       && \
    export subdomain=${SUBDOMAIN}       && \
    export domain=${DOMAIN}             && \
    export proxy=${PROXY}               && \
    export update_every=${UPDATE_EVERY} && \
    j2 templates/config.yml.j2 > config.yml

CMD ["python3","homerun.py"]