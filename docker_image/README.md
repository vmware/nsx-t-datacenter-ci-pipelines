# some general notes


### install docker for ubuntu
```
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
sudo apt-get install -y docker-ce
sudo systemctl status docker
```


### install docker for fedora/rh
```
function RH_get_variant_version(){   # returns [fc|el] [version]   (blanc between)
    s=`uname -r | tr '.' '\n' | grep -e "^el" -e "^fc"`
    echo "${s:0:2} ${s:2}"
}
function install_docker(){
    read -r variant version <<< `RH_get_variant_version`
    echo "  >> Installing X11 and Xfce for ${variant} ${version}"
    case "${variant}" in
    "el")
        sudo wget -O /etc/yum.repos.d/docker-ce.repo https://download.docker.com/linux/centos/docker-ce.repo
        ;;
    "fc")
        sudo wget -O /etc/yum.repos.d/docker-ce.repo https://download.docker.com/linux/fedora/docker-ce.repo
        ;;
    *)
        echo "ERROR: UNKNOWN OS '${variant} ${version}'"
        return 99
        ;;
    esac

    sudo yum install -y docker-ce
 
    # local engine: enable and start
    sudo systemctl enable docker; sudo systemctl start docker
 
    # add all users that belong to users also to docker
    for u in `getent group users | awk -F':' '{print $NF}' | tr ',' ' '`; do
        sudo usermod -a -G docker ${u}
    done 

    sudo docker info
    echo "done. don't forget to re-bash-yourself, group membership does not yet apply to this shell"
}

install_docker
```


# some notes about this container


### build the container your own
```
cd ~
git clone https://github.com/vmware/nsx-t-datacenter-ci-pipelines.git
pushd ~/nsx-t-datacenter-ci-pipelines/docker_image
docker build -t nsx-t-install .
popd
```


### run the container
(Assuming you have a nsx_pipeline_config.yml already prepared in /home/concourse)
```
docker run -it --name nsx-t-installer --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /home/concourse:/home/concourse \
  nsx-t-install -CONCOURSE_URL http://192.168.18.146:8080 
```


### export this container
```
docker image save nsx-t-install:latest | bzip2 --best > nsx-t-install-release-`date +%Y%m%d-%H%M`.tbz2
```


### import this container
```
wget -qO- https://github.com/maldex/nsx-t-datacenter-ci-pipelines/releases/download/20181101-1048/nsx-t-install-release-20181101-1048.tbz2 | bzip2 -d -c | docker load
```
