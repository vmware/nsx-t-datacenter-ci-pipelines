## Deploying Concourse using the Docker Image

The "nsx-t-ci-pipeline" Docker image automatically performs the following tasks: <br>
* If the NSX-T and OVF tool bits are not detected in /home/concourse folder the Docker image will download them automatically using the [vmw-cli](https://github.com/apnex/vmw-cli) project
* Deploys NGINX and to serve the bits to the pipeline <br>
* Deploys Concourse <br>
* Registers the pipeline and un-pauses it <br>

By performing these tasks automatically the Docker image saves you on time running these repetitive tasks. But, if you have an existing concourse server that you want to run the pipeline from, you can skip this section and go straight to [here](##Configuring the pipeline to run on an existing Concourse server)
If you are planning on using this docker image to download the bits, make sure to comment out the file names in the parameter file for the NSX manager ova and the OVFTool, this is because the Docker image will take care of serving the file for you. 

### Jumpbox requirements<br>
* Note * Concourse is not supported on Redhat. Please use Ubuntu or equivalent  
1. Install Docker-ce https://docs.docker.com/install/linux/docker-ce/ubuntu/
2. Create /home/concourse directory (sudo mkdir –p /home/concourse). In this folder create the parameter file names: nsx_pipeline_config.yml. <br> This YAML file should contains the required parameters to run the pipeline. Sample config files for PAS or PKS or both can be found at: https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/master/pipelines/sample-params.yml <br>
3. The docker image downloads NSX manager OVA and the OVF tool automatically to /home/concourse, and will always download the latest version of these files. For this purpose the docker image initiates vmw-cli which downloads binaries from my.vmware.com website automatically (a project by Andrew Obersnel https://github.com/apnex/vmw-cli) if you want to download the files manually and skip the step for the automatic download,  download and place  the following two files in to /home/concourse directory: <br>
a.	ovftool (example: VMware-ovftool-4.3.0-9158644-lin.x86_64.bundle). <br>
b.	NSX Manager OVA file. <br>

### Running the docker image <br>
1. Load the docker image <br>
`` docker load -i <file_name.tar> ``
2. Start the docker container with the following command <br> 
    ```
    docker run --name nsx-t-install -d \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v /home/concourse:/home/concourse \
      -e CONCOURSE_URL='http://<host_ip>:8080' \
      -e EXTERNAL_DNS='<dns_server>' \
      -e IMAGE_WEBSERVER_PORT=40001 \
      -e VMWARE_USER='<myvmware_user_email>' \
      -e VMWARE_PASSWORD='<myvmware_password>' \
      nsx-t-install
    ```
    For more information on supported environment variables, checkout the [Pipeline bring-up options](###Pipeline bring-up options) section below. <br>
    Docker container will start the Concourse Docker (Concourse CI running in a Docker container) (https://github.com/concourse/concourse-docker) which creates three Concourse containers (one database, one web, and one worker container) and one nginx webserver container; it consists of one Concourse pipeline<br>
    If you did not place the files manually in the /home/concourse folder, the script will download the latest versions from MyVMware using the vmw-cli tool written by Andrew Obersnel <br>
    You can watch the progress of the creation of the containers by running `` watch docker ps ``<br>
    It may take a few minutes to download the files, and for all the containers to load, once it did you should see the following containers running

    ```
    nsx-t-install
    nginx 
    Concourse web 
    Concourse Worker 
    Postgress
    ```
3. Browse to the Concourse page: http://<CONCOURSE_URL>:8080/ 
4. Login with the following default credentials
    ```
    user: nsx 
    password: vmware
    ```
<br>

## Configuring the pipeline to run on an existing Concourse server
If you are using an existing Concourse server do the following:
1. Place the NSX-T manager unified appliance OVA and the OVF tool in an accessible web server
2. Specify the web server and the file names in the param file as follows: <br>
    ```
    nsx_image_webserver: "http://192.168.110.11:40001"
    ova_file_name: "nsx-unified-appliance-2.2.0.0.0.8680778.ova" # Uncomment this if downloaded file manually and placed under /home/concourse 
    ovftool_file_name: "VMware-ovftool-4.2.0-5965791-lin.x86_64.bundle"
    ```
   Be sure to add __required pipeline branches__ mentioned in the [Pipeline bring-up options](###Pipeline bring-up options) section below.
3. Register the pipeline using: fly -t (target) sp -p (pipeline name) -c (nsx-t-datacenter-ci-pipelines/pipelines/nsx-t-install.yml) -l (parameter file) 
<br><br>

## Pipeline bring-up options

__If using the docker image provided in the [docker_image](../docker_image) folder of this repository:__<br>
The pipeline accepts the following environment variables:

| ENV_VAR | description |
|:---:|:---:|
| CONCOURSE_URL |  set to "http://<jumphost_ip>:8080". IP should be primary NIC of the VM running the Docker container, not the loopback address |
| EXTERNAL_DNS  | set to a dns server that can resolve vCenter hostname, and public names e.g. github.com |
| IMAGE_WEBSERVER_PORT | recommend '40001' if not taken    |
| VMWARE_USER (optional) | required if NSX ova need to be downloaded  |
| VMWARE_PASSWORD (optional) | required if NSX ova need to be downloaded |
| NSX-T_VERSION (optional)   | required if need to _download a earlier nsx-t version from myvmware.com_ |
| PIPELINE_BRANCH (optional __*__)    | branch to use for nsx-t-datacenter-ci-pipelines |
| ANSIBLE_BRANCH (optional __*__)     | branch to use for nsxt-ansible (https://github.com/vmware/ansible-for-nsxt) |

To set those environment variables, use -e ENV_VAR='value' in the docker run command. <br>
__Note: (*)__ Unless for debugging purposes, these two parameters should not be explicitly set! <br>
NSX-T_VERSION also should not be specified if you have placed NSX-T ova file under /home/concourse (see [README.md](../README.md)), as the pipeline will automatically determine the NSX-T version and use the compatible pipeline branches.
If you do wish to specify these ENV variables, make sure the NSX-T version and pipeline branches are compatible!! (see the matrix below)
<br><br>

__If running the pipeline on existing concourse environment and not using the nsx-t-install image, please perform following additional steps:__ in nsx_pipeline_config.yml that was created under /home/concourse, add the following two lines at the beginning, depending on which NSX-T version you are deploying:

| NSX-T 2.3.0 & earlier  |   NSX-T 2.4.0   |  NSX-T 2.5.0  |
|:----------------------:|:---------------:|:-------------:|
| nsxt_ansible_branch=v1.0.0 |  nsxt_ansible_branch=master | nsxt_ansible_branch=dev |
| nsx_t_pipeline_branch=nsxt_2.3.0 |  nsxt_ansible_branch=nsxt_2.4.0 | nsx_t_pipeline_branch=master |

Also, if ovftool and ova files were downloaded manually, add ``ova_file_name=<ova_file_name>`` and ``ovftool_file_name=<ovftool_file_name>`` in nsx_pipeline_config.yml as well, as mentioned in the section above.