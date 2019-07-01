##
docker-image: follow-up concerning internal run-sequence of 'nsx-t-install' image

All tough I still don't get why `fly sync` can work before `fly login`, the current image only seems to work on ubuntu hosts. Following up issue #18 and the canceled pr #19, the attached proposal is an overhaul of the current build and run methods.

Essentially:
- run.sh
-- the ENTRYPOINT directive allows for container parameters to be passed into the actual application (note: this behavior differs from CMD directive). The proposed `run.sh` allows for argument segretation of docker related and application related arguments. Please find a sample in the simplified `run.nsx-t-install-er.sh` script.
-- in short: argument passing has changed into what docker requires and what run.sh requires.
-- the original flow has been kept, but 'modularized' into shell functions. 
-- the fly-related commands have been rewritten into shell-functions.
-- the container (should) automatically detect if it's interactive and present you with a bash.
-- shutdown and destruction has been refactored.
-- the involved containers should not stay around and cause conflict (using `--rm` switch and ensuring `docker-compose down` was called upon graceful container termination)

- Dockerfile
-- splitup into multiple `run` statements leverageing the layering during the build.
-- unified downloads to wget and added some documentation.

So far i was able to bring the concourse pipeline for nsx-t-install up and running on a Fedora host.
cheers

[proposed](https://github.com/maldex/nsx-t-datacenter-ci-pipelines/blob/ee709fb6b0f0d3ffc377ec622f8b521f9201f821/docker_image/run.sh)
vs
[recent](https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/master/docker_image/run.sh)
-----------------------------------------------

## install docker
... install docker for your platform ...

## clone this repo and build
```
git clone https://github.com/vmware/nsx-t-datacenter-ci-pipelines.git
docker build -t nsx-t-install ./nsx-t-datacenter-ci-pipelines/docker_image
```

## run the container manually
(Assuming you have a _nsx_pipeline_config.yml_ already prepared in _/home/concourse_)
```
docker run -it --name nsx-t-installer --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /home/concourse:/home/concourse \
  nsx-t-install -CONCOURSE_URL http://<your_ip>:8080 
```

## run the container assisted
```
sh ./nsx-t-datacenter-ci-pipelines/docker_image/run.nsx-t-install-er.sh
```

## manually destroy all containers
```
docker ps --format "{{.Names}}" | grep -e "^concourse" -e "^nsx-t-installer" -e "^nginx-" | xargs docker stop
rm -f /home/concourse/nsx_pipeline_config.pid
```
