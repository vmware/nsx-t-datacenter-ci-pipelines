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
