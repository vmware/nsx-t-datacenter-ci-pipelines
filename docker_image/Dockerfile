FROM ubuntu:18.04
ADD run.sh /home/run.sh

# https://docs.docker.com/compose/install/#install-compose
RUN apt-get update && \
    apt-get install -y vim curl openssh-client git wget python && \
    curl -sSL https://get.docker.com/ | sh && \
    curl -L --fail https://github.com/docker/compose/releases/download/1.23.2/run.sh -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose && \
    # download and install fly CLI
    wget -P /usr/local/bin/ https://github.com/concourse/concourse/releases/download/v5.7.0/fly-5.7.0-linux-amd64.tgz && \
    tar -C /usr/local/bin/ -xvf /usr/local/bin/fly-5.7.0-linux-amd64.tgz && \
    chmod +x /usr/local/bin/fly

ENTRYPOINT ["/home/run.sh"]
