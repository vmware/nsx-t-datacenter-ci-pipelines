#!/usr/bin/env bash

# globals
function log() { echo "-----> $@"; }
ROOT_WORK_DIR="/home/workspace"
BIND_MOUNT_DIR="/home/concourse"

log "parsing arguments"
while [ "$1" != "" ]; do
case "$1" in
    "-CONCOURSE_IP")
        shift; CONCOURSE_IP=$1
        shift; continue
        ;;
    "-CONCOURSE_PORT")
        shift; CONCOURSE_PORT=$1
        shift; continue
        ;;
    "-CONCOURSE_URL")
        shift; CONCOURSE_URL=$1
        shift; continue
        ;;
    "-EXTERNAL_DNS")
        shift; EXTERNAL_DNS=$1
        shift; continue
        ;;
    "-IMAGE_WEBSERVER_PORT")
        shift; IMAGE_WEBSERVER_PORT=$1
        shift; continue
        ;;
    "-VMWARE_USER")
        shift; VMWARE_USER=$1
        shift; continue
        ;;
    "-VMWARE_PASS")
        shift; VMWARE_PASS=$1
        shift; continue
        ;;        
    "-NSXT_VERSION")
        shift; NSXT_VERSION=$1
        shift; continue
        ;;            
    "-CONFIG_FILE_NAME")
        shift; CONFIG_FILE_NAME=$1
        shift; continue
		;;
    *)
        echo "unknown argument '$1'"
        shift
        ;;
esac
done

# defaults
if [ -z "${CONCOURSE_TARGET}" ]; then		  CONCOURSE_TARGET=nsx-concourse; fi
if [ -z "${PIPELINE_NAME}" ]; then 			  PIPELINE_NAME=nsx-t-install; fi
if [ -z "${CONFIG_FILE_NAME}" ]; then         CONFIG_FILE_NAME=nsx_pipeline_config.yml; fi
if [ -z "${NSXT_VERSION}" ]; then             NSXT_VERSION=2.3.0; fi
if [ -z "${IMAGE_WEBSERVER_PORT}" ]; then     IMAGE_WEBSERVER_PORT=40002; fi
if [ -z "${EXTERNAL_DNS}" ]; then             EXTERNAL_DNS=`grep ^nameserver /etc/resolv.conf | shuf | awk 'END{print $2}'`; fi
if [ -z "${CONCOURSE_PORT}" ]; then           CONCOURSE_PORT=8080; fi
if [ ! -z "${CONCOURSE_IP}" ]; then           CONCOURSE_URL="http://${CONCOURSE_IP}:${CONCOURSE_PORT}"; fi
if [ ! -z "${CONCOURSE_URL}" ]; then          CONCOURSE_IP="`echo $CONCOURSE_URL | tr -d '/' | awk -F':' '{print $2}'`"
else
    echo "either specifiy CONCOURSE_URL like http://192.168.18.15:8080 or CONCOURSE_IP like 192.168.18.15"
    exit 1
fi

if [ ! -e ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} ]; then
    echo "Config file ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} not found, exiting"
    exit 1
fi

if ! grep "nsx_image_webserver" ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} | grep -q "${CONCOUSE_IP}"; then 
    log "image_webserver not on CONCOURSE_IP, fixing"
    sed -i 's%^nsx_image_webserver:.*%nsx_image_webserver: '${CONCOURSE_IP}:${IMAGE_WEBSERVER_PORT}'%g' ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME}
fi



log "download the ovftool and OVA files"
cd $BIND_MOUNT_DIR
ova_file_name=$(ls -l *.ova | sed 's/.* nsx/nsx/;s/ova.*/ova/' | tail -n1)
ovftool_file_name=$(ls -l *.bundle | sed 's/.* VMware-ovftool/VMware-ovftool/;s/bundle.*/bundle/' | tail -n1)
nsxt_version=2.3.0
if [[ $NSXT_VERSION != "" ]]; then
    nsxt_version=$NSXT_VERSION
fi

if [[ $ova_file_name == "" ]] || [[ $ovftool_file_name == "" ]]; then
    #ovftool_file_name="VMware-ovftool-4.3.0-7948156-lin.x86_64.bundle"
    #ova_file_name="nsx-unified-appliance-2.2.0.0.0.8680778.ova"
    set -e
    docker run -itd --name vmw-cli -e VMWINDEXDIR="/state" -e VMWUSER=$VMWARE_USER -e VMWPASS=$VMWARE_PASSWORD -v ${BIND_MOUNT_DIR}:/files --entrypoint=sh apnex/vmw-cli

    docker exec -t vmw-cli vmw-cli index OVFTOOL430
    ovftool_file_name=$(docker exec -t vmw-cli vmw-cli find fileType:bundle,version:4.3 | grep VMware-ovftool | sed 's/.* VMware-ovftool/VMware-ovftool/;s/bundle.*/bundle/' | tail -n1)
    docker exec -t vmw-cli vmw-cli get $ovftool_file_name

    version_no_dots=$(echo $nsxt_version | sed 's/\.//g')
    docker exec -t vmw-cli vmw-cli index NSX-T-${version_no_dots}
    ova_file_name=$(docker exec -t vmw-cli vmw-cli find fileType:ova,version:${nsxt_version} | grep nsx-unified-appliance | sed 's/.* nsx/nsx/;s/ova.*/ova/' | tail -n1)
    docker exec -t vmw-cli vmw-cli get $ova_file_name
    docker stop vmw-cli
    docker rm vmw-cli

    if [[ $ova_file_name == "" ]]; then
        echo "OVA not found for NSX version $nsxt_version. Please specify a supported version and recreate the container."
        exit 1
    fi
    set +e
fi

log "writing additional pipeline configs"
nsx_t_pipeline_branch=master
if [[ $PIPELINE_BRANCH != "" ]]; then
    nsx_t_pipeline_branch=$PIPELINE_BRANCH
fi

pipeline_internal_config="pipeline_config_internal.yml"
echo "ovftool_file_name: $ovftool_file_name" > $pipeline_internal_config
echo "ova_file_name: $ova_file_name" >> $pipeline_internal_config
echo "nsx_t_pipeline_branch: $nsx_t_pipeline_branch" >> $pipeline_internal_config

log "start a web server to host static files such as ovftool and NSX manager OVA"
docker run --name nsx-t-install-nginx -v ${BIND_MOUNT_DIR}:/usr/share/nginx/html:ro -p ${IMAGE_WEBSERVER_PORT}:80 --rm -d nginx


log "fetch and prepare concourse"
mkdir -p $ROOT_WORK_DIR
cd $ROOT_WORK_DIR
git clone https://github.com/concourse/concourse-docker.git
git clone https://github.com/vmware/nsx-t-datacenter-ci-pipelines.git

concourse_docker_dir=${ROOT_WORK_DIR}/concourse-docker
pipeline_dir=${ROOT_WORK_DIR}/nsx-t-datacenter-ci-pipelines
cp ${concourse_docker_dir}/generate-keys.sh $BIND_MOUNT_DIR
cp ${pipeline_dir}/docker_compose/docker-compose.yml $BIND_MOUNT_DIR

cd $BIND_MOUNT_DIR
./generate-keys.sh

# prepare the yaml for docker compose
concourse_version=3.14.1
sed -i "0,/^ *- CONCOURSE_EXTERNAL_URL/ s|CONCOURSE_EXTERNAL_URL.*$|CONCOURSE_EXTERNAL_URL=${CONCOURSE_URL}|" docker-compose.yml
sed -i "0,/^ *- CONCOURSE_GARDEN_DNS_SERVER/ s|CONCOURSE_GARDEN_DNS_SERVER.*$|CONCOURSE_GARDEN_DNS_SERVER=${EXTERNAL_DNS}|" docker-compose.yml
sed -i "0,/^ *- CONCOURSE_NO_REALLY_I_DONT_WANT_ANY_AUTH/ s|CONCOURSE_NO_REALLY_I_DONT_WANT_ANY_AUTH.*$|CONCOURSE_NO_REALLY_I_DONT_WANT_ANY_AUTH=true|" docker-compose.yml
sed  -i "/^ *image: concourse\/concourse/ s|concourse/concourse.*$|concourse/concourse:$concourse_version|g" docker-compose.yml

# remove lines containing following parameters
patterns=("CONCOURSE_BASIC_AUTH_USERNAME" "CONCOURSE_BASIC_AUTH_PASSWORD" "http_proxy_url" "https_proxy_url" "no_proxy" "HTTP_PROXY" "HTTPS_PROXY" "NO_PROXY")
for p in "${patterns[@]}"; do
        sed -i "/$p/d" docker-compose.yml
done
#sed -i "0,/^ *- CONCOURSE_GARDEN_NETWORK/ s|- CONCOURSE_GARDEN_NETWORK.*$|#- CONCOURSE_GARDEN_NETWORK|" docker-compose.yml
#sed -i "/^ *- CONCOURSE_EXTERNAL_URL/ a\    - CONCOURSE_NO_REALLY_I_DONT_WANT_ANY_AUTH=true" docker-compose.yml

log "bringing up Concourse server in a docker-compose cluster"
docker-compose up -d

# waiting for the concourse API server to start up
while ! curl -s -o /dev/null $CONCOURSE_URL; do
    log "waiting for $CONCOURSE_URL to become running"
    sleep 2
done

log "fly: logging into concourse at $CONCOURSE_URL"
fly --target $CONCOURSE_TARGET login --insecure --concourse-url $CONCOURSE_URL -n main
fly --target $CONCOURSE_TARGET sync


function fly_cmd_set() {
    fly -t $CONCOURSE_TARGET set-pipeline -p $PIPELINE_NAME -c ${pipeline_dir}/pipelines/nsx-t-install.yml -l ${BIND_MOUNT_DIR}/${pipeline_internal_config} -l ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} --non-interactive
}
function fly_cmd_start() {
    fly -t $CONCOURSE_TARGET unpause-pipeline -p $PIPELINE_NAME
}
function fly_cmd_stop() {
    fly -t $CONCOURSE_TARGET destroy-pipeline -p $PIPELINE_NAME --non-interactive
}
function fly_cmd_status() {
    fly targets ; fly -t $CONCOURSE_TARGET status ; fly -t $CONCOURSE_TARGET pipelines ; fly -t $CONCOURSE_TARGET workers
}

declare -f fly_cmd_set fly_cmd_start fly_cmd_stop fly_cmd_status >> ~/.bashrc
export CONCOURSE_TARGET PIPELINE_NAME pipeline_dir BIND_MOUNT_DIR CONFIG_FILE_NAME pipeline_internal_config

log "fly: setting the NSX-t install pipeline $PIPELINE_NAME"
fly_cmd_set

log "fly: starting / unpausing pipeline"
fly_cmd_start

log "fly: veryfly"
fly_cmd_status

# adding aliases to .bashrc
#echo "alias fly-set=\"${fly_cmd_set}\"" >> ~/.bashrc
#echo "alias fly-start=\"${fly_cmd_start}\"" >> ~/.bashrc
#echo "alias fly-stop=\"${fly_cmd_stop}\"" >> ~/.bashrc
#echo "alias fly-status=\"${fly_cmd_status}\"" >> ~/.bashrc
source ~/.bashrc

cd ${BIND_MOUNT_DIR}
echo "$$" >> running.pid

if [ -t 0 ] ; then
    log "(interactive shell - exit to terminate)"
    bash     
else
    log "(not interactive shell - remove 'running.pid' to terminate)"
    while [ -e running.pid ]; do
        if ! docker ps | grep -q concourse-worker; then
            log "lost worker, restarting"
            docker-compose restart concourse-worker
        fi
        sleep 5
    done
fi

log "shutting down"
rm -f running.pid

$stop_pipeline_cmd
docker-compose down
docker stop nsx-t-install-nginx
exit 0
