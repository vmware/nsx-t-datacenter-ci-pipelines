#!/usr/bin/env bash
# Set this via a env var
# CONCOURSE_URL="http://10.33.75.99:8080"
# EXTERNAL_DNS=<dns_ip>
# IMAGE_WEBSERVER_PORT=<port_number>
# VMWARE_USER
# VMWARE_PASSWORD
# NSXT_VERSION
# PIPELINE_BRANCH

ROOT_WORK_DIR="/home/workspace"
BIND_MOUNT_DIR="/home/concourse"
CONFIG_FILE_NAME="nsx_pipeline_config.yml"

if [[ ! -e ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} ]]; then
	echo "Config file ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} not found, exiting"
	exit 1
fi

# download the ovftool and OVA files
cd $BIND_MOUNT_DIR
ova_file_name=$(ls -l *.ova | sed 's/.* nsx/nsx/;s/ova.*/ova/' | tail -n1)
ovftool_file_name=$(ls -l *.bundle | sed 's/.* VMware-ovftool/VMware-ovftool/;s/bundle.*/bundle/' | tail -n1)
nsxt_version=2.2.0
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

nsx_t_pipeline_branch=master
if [[ $PIPELINE_BRANCH != "" ]]; then
	nsx_t_pipeline_branch=$PIPELINE_BRANCH
fi

pipeline_internal_config="pipeline_config_internal.yml"
echo "ovftool_file_name: $ovftool_file_name" > $pipeline_internal_config
echo "ova_file_name: $ova_file_name" >> $pipeline_internal_config
echo "nsx_t_pipeline_branch: $nsx_t_pipeline_branch" >> $pipeline_internal_config

# start a web server to host static files such as ovftool and NSX manager OVA
docker run --name nginx-server -v ${BIND_MOUNT_DIR}:/usr/share/nginx/html:ro -p ${IMAGE_WEBSERVER_PORT}:80 -d nginx

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

echo "bringing up Concourse server in a docker-compose cluster"
docker-compose up -d

# waiting for the concourse API server to start up
while true; do
	curl -s -o /dev/null $CONCOURSE_URL
	if [[ $? -eq 0 ]]; then
		break
	fi
	echo "waiting for Concourse web server to be running"
	sleep 2
done
echo "brought up the Concourse cluster"

# using fly to start the pipeline
CONCOURSE_TARGET=nsx-concourse
PIPELINE_NAME=nsx-t-install
echo "logging into concourse at $CONCOURSE_URL"
fly -t $CONCOURSE_TARGET sync
fly --target $CONCOURSE_TARGET login --insecure --concourse-url $CONCOURSE_URL -n main
echo "setting the NSX-t install pipeline $PIPELINE_NAME"
fly_reset_cmd="fly -t $CONCOURSE_TARGET set-pipeline -p $PIPELINE_NAME -c ${pipeline_dir}/pipelines/nsx-t-install.yml -l ${BIND_MOUNT_DIR}/${pipeline_internal_config} -l ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME}"
yes | $fly_reset_cmd
echo "unpausing the pipepline $PIPELINE_NAME"
fly -t $CONCOURSE_TARGET unpause-pipeline -p $PIPELINE_NAME

# add an alias for set-pipeline command
echo "alias fly-reset=\"$fly_reset_cmd\"" >> ~/.bashrc
destroy_cmd="cd $BIND_MOUNT_DIR; fly -t $CONCOURSE_TARGET destroy-pipeline -p $PIPELINE_NAME; docker-compose down; docker stop nginx-server; docker rm nginx-server;"
echo "alias destroy=\"$destroy_cmd\"" >> ~/.bashrc
source ~/.bashrc

while true; do
	is_worker_running=$(docker ps | grep concourse-worker)
	if [[ ! $is_worker_running ]]; then
		docker-compose restart concourse-worker
		echo "concourse worker is down; restarted it"
		break
	fi
	sleep 5
done

sleep 3d
fly -t $CONCOURSE_TARGET destroy-pipeline -p $PIPELINE_NAME
docker-compose down
docker stop nginx-server
docker rm nginx-server
exit 0
