## Utilities and Troubleshooting

### Updating the parameter file
In case you need to modify the parameter, file or fix anything and rerun the pipeline, perform the following:
* Make your change to the parameter file <br>
* Hijack the container <br> 
  * run ``docker ps`` to find the "nsx-t-install" container ID 
  * run ``docker exec -it <nsx-t-install-id> bash`` <br>
  * in the container run ``fly-reset`` (this basically will run set-pipeline for the nsx-t pipeline) 
<br>

### Cleaning up

If you want to re-run from scratch do the following to cleanup: <br>
* Stop containers - `docker stop $(docker ps -a -q)` <br>
* Remove the containers -  `docker rm $(docker ps -aq)`
* Delete images -  `docker rmi -f $(docker images -a -q)` <br>
* clear cache - `docker system prune --all` <br>
* unregister the vCenter extension - https://docs.vmware.com/en/VMware-NSX-T/2.2/com.vmware.nsxt.admin.doc/GUID-E6E2F017-1106-48C5-ABCA-3D3E9130A863.html 

### Commonly seen issues:
__NSX manager OVA auto download did not work; container exited.__ <br>
Solution: it's likely the myvmware credentials were misspelled and did not work. Make sure the username is an email address, and both username and password are enclosed by single quotes (e.g. `-e VMWARE_USER='abc@efg.com' -e VMWARE_PASSWORD='pwd$pecial'`)
<br>

__There should be 3 containers related to concourse running (web, worker, postgres). But one or more are missing from `docker ps` output.__ <br>
Solution: use `docker ps -a` to find the exited container(s). Then check the logs with `docker logs <container_id>`. If the error message signals the container exited due to insufficient disk space on the jumphost, clean up unused docker volumes with:  
`docker volume rm $(docker volume ls -qf dangling=true)`  
Then clean up the existing containers:
> `docker exec -it nsx-t-install bash`  
> `cd /home/concourse`  
> `docker-compose down`  
> `exit`  
> `docker stop nginx-server nsx-t-install`  
> `docker rm nginx-server nsx-t-install`   

Finally, rerun the pipeline container.
<br>

__Ovftool fails to deploy NSX manager with OVA. Error from pipeline: "transfer failed; failed to send http data".__<br>
Solution: chances are the EXTERNAL_DNS environment variable passed to the container was unable to resolve vCenter's name. Rerun the docker container with a proper DNS nameserver.