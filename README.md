 


# nsx-t-datacenter-ci-pipelines
This repository provides an easy-to-use automation framework that installs and configures NSX-T on vCenter clusters where PKS and/or PAS can be deployed.

## Overview
Under the hood, there is a Concourse pipeline which is to be set up by a Docker container which the user creates. The Concourse pipeline is in turn run in three Docker containers: DB, worker, and web container. 

The Concourse pipeline performs the following jobs:
1. Deploy NSX manager, controllers and edges;
2. Convert hosts from vCenter clusters specified by user to NSX transport nodes;
3. Create NSX logical resources to make the environment PAS/PKS deployment ready.

## For the full documentation see the wiki page
See the wiki: https://github.com/vmware/nsx-t-datacenter-ci-pipelines/wiki

## Try it out
On a Ubuntu VM with at least ~20GB of space,
```
wget https://github.com/vmware/nsx-t-datacenter-ci-pipelines/raw/master/docker_image/nsx-t-install-09122018.tar -O nsx-t-install.tar
docker load -i nsx-t-install.tar
mkdir -p /home/concourse
```
Create nsx_pipeline_config.yml based on a sample config file, e.g. https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/master/sample_parameters/PAS_only/nsx_pipeline_config.yml for PAS environment, and place it under /home/concourse.
```
echo "My VMware Password:" && read -s password
docker run --name nsx-t-install -d \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /home/concourse:/home/concourse \
  -e CONCOURSE_URL="http://10.33.75.99:8080" \
  -e EXTERNAL_DNS="10.33.38.1" \
  -e IMAGE_WEBSERVER_PORT=40001 \
  -e VMWARE_USER='<myvmware_user_email>' \
  -e VMWARE_PASSWORD="$password" \
  nsx-t-install
```
Set CONCOURSE_URL to http://<host_ip>:8080 (host_ip is the IP address of the primary NIC of the VM running the container (example: 10.85.99.130); it is not the loopback address. Set EXTERNAL_DNS to the DNS server (it should be able to resolve the vCenter hostname, and public names e.g. github.com), and  IMAGE_WEBSERVER_PORT to the port number provided in the  nsx_pipeline_config.yml parameter nsx_image_webserver (recommendation: 40001).

The above command will automatically download the ovftool (e.g. VMware-ovftool-4.3.0-xxxxxxx-lin.x86_64.bundle) and NSX OVA (nsx-unified-appliance-2.2.0.0.0.xxxxxxx.ova) files from myvmware.com. If you have already downloaded the two files manually, place them under /home/concourse, and run above command with VMWARE_USER and VMWARE_PASSWORD skipped.

Browse to the Concourse pipeline: http://<CONCOURSE_URL>/teams/main/pipelines/install-nsx-t/ (example: http://10.85.99.130:8080/teams/main/pipelines/install-nsx-t/) and click on the plus on the upper right corner to trigger a build to install NSX-T.

Check out the [Troubleshooting Guide](https://github.com/vmware/nsx-t-datacenter-ci-pipelines/wiki/Troubleshooting) for troubleshooting tips.

## Contributing

The nsx-t-datacenter-ci-pipelines project team welcomes contributions from the community. Before you start working with nsx-t-datacenter-ci-pipelines, please read our [Developer Certificate of Origin](https://cla.vmware.com/dco). All contributions to this repository must be signed as described on that page. Your signature certifies that you wrote the patch or have the right to pass it on as an open-source patch. For more detailed information, refer to [CONTRIBUTING.md](CONTRIBUTING.md).

## License
NSX-T-Data-Center-CI-Pipeline-with-Concourse

Copyright (c) 2018 VMware, Inc.				

The MIT license (the “License”) set forth below applies to all parts of the NSX-T-Data-Center-CI-Pipeline-with-Concourse project.  You may not use this file except in compliance with the License. 

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


