# Docker build file for 'nsx-t-datacenter-ci-pipelines'
FROM     ubuntu:18.04

# install additional linux packages
RUN     apt-get update && \
        apt-get install -y vim curl openssh-client git wget
    
# add docker compose
RUN     cd /usr/local/bin/ && \
        wget -q -O - https://get.docker.com/ | sh && \
        wget -q -O docker-compose https://github.com/docker/compose/releases/download/1.23.2/run.sh && \
        chmod +x docker-compose && \
        file ${PWD}/docker-compose

# add fly
# wget -q -O - https://github.com/concourse/concourse/releases/download/v5.3.0/fly-5.3.0-linux-amd64.tgz | tar -zxf -
RUN     cd /usr/local/bin && \
        wget -q -O fly https://github.com/Concourse/Concourse/releases/download/v4.2.1/fly_linux_amd64 && \
        chmod +x fly && \
        file ${PWD}/fly

# add custom code
ADD     Dockerfile        /Dockerfile
ADD     run.sh            /home/run.sh
RUN     chmod +x /home/run.sh

# application launch
ENTRYPOINT         ["/home/run.sh"]
