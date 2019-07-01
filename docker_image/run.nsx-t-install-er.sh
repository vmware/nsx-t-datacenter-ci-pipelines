#!/usr/bin/env bash

# launcher-helper for nsx-t-installer container

export MyIf=`ip route | grep "default" | awk '{ print $5; }'`
export MyIp=`ip addr show $MyIf | grep ".*inet [0-9]*.[0-9]*.[0-9]*.[0-9]*/[0-9]* " | tr '/' ' ' | awk '{ print $2; }'`
export MyDns=`grep ^nameserver /etc/resolv.conf | shuf | tail -n1 | awk '{ print $NF; }'`

echo " ---->  MyIf: ${MyIf}  |  MyIp: ${MyIp}  |  DNS: ${MyDns}  <---- "

# replace '-it' with '-d' for non-interactive
docker run --rm --name nsx-t-installer -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /home/concourse:/home/concourse \
  nsx-t-install \
  -CONCOURSE_URL "http://${MyIp}:8080" \
  -EXTERNAL_DNS "${MyDns}" \
  -VMWARE_USER "MyVmwLogin" \
  -VMWARE_PASS "MyVmwPass"
