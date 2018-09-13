

# nsx-t-datacenter-ci-pipelines
This repository provides an easy-to-use automation framework that installs and configures NSX-T on vCenter clusters where PKS and/or PAS can be deployed.

## Overview
Under the hood, there is a Concourse pipeline which is to be set up by a Docker container which the user creates. The Concourse pipeline is in turn run in three Docker containers: DB, worker, and web container. 

The Concourse pipeline performs the following jobs:
1. Deploy NSX manager, controllers and edges;
2. Convert hosts from vCenter clusters specified by user to NSX transport nodes;
3. Create NSX logical resources to make the environment PAS/PKS deployment ready.

## Try it out
```
mkdir -p /home/concourse /home/static_dependency
```
Create nsx_pipeline_config.yml based on the sample config file https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/master/pipelines/nsx-t-install.yml, and place it under /home/concourse.
```
docker pull <nsx-t-install-image>
docker run --name nsx-t-install -d -v /var/run/docker.sock:/var/run/docker.sock -v /home/concourse:/home/concourse -e CONCOURSE_URL="http://10.33.75.99:8080" -e EXTERNAL_DNS="10.33.38.1" -e IMAGE_WEBSERVER_PORT=40001 nsx-t-install
```
Set CONCOURSE_URL to http://<host_ip>:8080 (host_ip is the IP address of the primary NIC of the VM running the container (example: 10.85.99.130); it is not the loopback address. Set EXTERNAL_DNS to the DNS server (example: 8.8.8.8), and  IMAGE_WEBSERVER_PORT to the port number provided in the  nsx_pipeline_config.yml parameter nsx_image_webserver (recommendation: 40001).

Browse to the Concourse pipeline: http://<CONCOURSE_URL>/teams/main/pipelines/install-nsx-t/ (example: http://10.85.99.130:8080/teams/main/pipelines/install-nsx-t/) and click on the plus on the upper right corner to trigger a build to install NSX-T.

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


