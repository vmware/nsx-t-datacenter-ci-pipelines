#!/usr/bin/env bash

# proposed https://github.com/maldex/nsx-t-datacenter-ci-pipelines/blob/ee709fb6b0f0d3ffc377ec622f8b521f9201f821/docker_image/run.sh
# recent   https://github.com/vmware/nsx-t-datacenter-ci-pipelines/blob/master/docker_image/run.sh

###
# inital startup, arg parsing and dealing with values
###

set -a -e

function log { echo "-----> $@"; }

export ROOT_WORK_DIR=/home/workspace
export BIND_MOUNT_DIR=/home/concourse

log "${FUNCNAME[0]}: parsing arguments"
while [ "$1" != "" ]; do
case "$1" in
    "-CONCOURSE_URL")
        shift; export CONCOURSE_URL=$1
        shift; continue
        ;;
    "-EXTERNAL_DNS")
        shift; export EXTERNAL_DNS=$1
        shift; continue
        ;;
    "-IMAGE_WEBSERVER_PORT")
        shift; export IMAGE_WEBSERVER_PORT=$1
        shift; continue
        ;;
    "-VMWARE_USER")
        shift; export VMWARE_USER=$1
        shift; continue
        ;;
    "-VMWARE_PASS")
        shift; export VMWARE_PASS=$1
        shift; continue
        ;;        
    "-NSXT_VERSION")
        shift; export NSXT_VERSION=$1
        shift; continue
        ;;            
    "-CONFIG_FILE_NAME")
        shift; export CONFIG_FILE_NAME=$1
        shift; continue
		;;
	"bash"|"/bin/bash")
		/bin/bash -i
		exit $?
        ;;
    *)
        echo "unknown argument '$1'"
        shift
        ;;
esac
done

# defaults
if [ -z "${EXTERNAL_DNS}" ]; then             export EXTERNAL_DNS=`grep ^nameserver /etc/resolv.conf | shuf | awk 'END{print $2}'`; fi
if [ -z "${IMAGE_WEBSERVER_PORT}" ]; then     export IMAGE_WEBSERVER_PORT=40001; fi
if [ -z "${NSXT_VERSION}" ]; then             export NSXT_VERSION=2.4.1; fi
if [ -z "${CONFIG_FILE_NAME}" ]; then         export CONFIG_FILE_NAME=nsx_pipeline_config.yml; fi

# some more defaults
export CONCOURSE_TARGET=nsx-concourse
export PIPELINE_NAME=nsx-t-install
my_own_github_url=https://github.com/vmware/nsx-t-datacenter-ci-pipelines.git
concourse_version=4.2.1
unified_appliance=true
nsx_t_pipeline_branch=nsxt_2.4.0
nsxt_ansible_branch=master
#version_num=$(echo $nsxt_version | cut -d'.' -f1)
#version_sub_num=$(echo $nsxt_version | cut -d'.' -f2)
#if [[ $version_num -le 2 ]] && [[ $version_sub_num -le 3 ]]; then
#	unified_appliance=false
#	nsx_t_pipeline_branch=nsxt_2.3.0
#	nsxt_ansible_branch=v1.0.0
#fi
#if [[ $PIPELINE_BRANCH != "" ]]; then
#	nsx_t_pipeline_branch=$PIPELINE_BRANCH
#fi

export pipeline_internal_config=${CONFIG_FILE_NAME::-4}.internal.yml
export pipeline_dir=${ROOT_WORK_DIR}/nsx-t-datacenter-ci-pipelines

# verify
if [ -z "${CONCOURSE_URL}" ]; then             
    echo "CONCOURSE_URL must be specified like http://192.168.18.15:8080"
    exit 1
fi 
if [[ ! -e ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} ]]; then
    echo "Config file ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} not found, exiting"
    exit 1
fi

# some additional stuff about myself
pidfile=${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME::-4}.pid
if [ -e $pidfile ]; then
	echo "${pidfile} already exists, aborting";
	exit 3
fi


###
# fetch requirements on startup
###

function init-download-ova {
	log "${FUNCNAME[0]}: download the ovftool and OVA files"
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
	
	export ova_file_name 
	export ovftool_file_name
}
init-download-ova


function init-fetch-concourse {
	log "${FUNCNAME[0]}: fetch and prepare concourse"
	mkdir -p $ROOT_WORK_DIR
	cd $ROOT_WORK_DIR

	#git clone https://github.com/concourse/concourse-docker.git
	#concourse_docker_dir=${ROOT_WORK_DIR}/concourse-docker
	#cp ${concourse_docker_dir}/keys/generate $BIND_MOUNT_DIR
	#./generate
	git clone -b $nsx_t_pipeline_branch --single-branch $my_own_github_url
	cp ${pipeline_dir}/docker_compose/docker-compose.yml $BIND_MOUNT_DIR
	cp ${pipeline_dir}/functions/generate-keys.sh $BIND_MOUNT_DIR

	cd $BIND_MOUNT_DIR
	chmod +x generate-keys.sh
	if [ ! -d keys/ ]; then
		./generate-keys.sh
	fi
}
init-fetch-concourse


function init-adjust-config {
	log "${FUNCNAME[0]}: strictly overwriting 'nsx_image_webserver'-value in ${CONFIG_FILE_NAME} - sorry for that"
	websrv="`echo $CONCOURSE_URL | rev | cut -d':' -f 2- | rev`:${IMAGE_WEBSERVER_PORT}"
	sed -i 's%^nsx_image_webserver:.*%nsx_image_webserver: '${websrv}'%g' ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME}

	log "${FUNCNAME[0]}: writing additional pipeline configs"

	echo "ovftool_file_name: $ovftool_file_name" > $pipeline_internal_config
	echo "ova_file_name: $ova_file_name" >> $pipeline_internal_config
	echo "unified_appliance: $unified_appliance" >> $pipeline_internal_config
	echo "nsx_t_pipeline_branch: $nsx_t_pipeline_branch" >> $pipeline_internal_config
	echo "nsxt_ansible_branch: $nsxt_ansible_branch" >> $pipeline_internal_config
	
	log "${FUNCNAME[0]}: prepare the yaml for docker compose"
	sed -i "0,/^ *- CONCOURSE_EXTERNAL_URL/ s|CONCOURSE_EXTERNAL_URL.*$|CONCOURSE_EXTERNAL_URL=${CONCOURSE_URL}|" docker-compose.yml
	sed -i "0,/^ *- CONCOURSE_GARDEN_DNS_SERVER/ s|CONCOURSE_GARDEN_DNS_SERVER.*$|CONCOURSE_GARDEN_DNS_SERVER=${EXTERNAL_DNS}|" docker-compose.yml
	sed  -i "/^ *image: concourse\/concourse/ s|concourse/concourse.*$|concourse/concourse:$concourse_version|g" docker-compose.yml

	# If proxy env vars not set, remove the settings
	proxy_patterns=("http_proxy_url" "https_proxy_url" "no_proxy" "HTTP_PROXY" "HTTPS_PROXY" "NO_PROXY")
	if [[ -z "$HTTP_PROXY" ]] || [[ -z "HTTPS_PROXY" ]]; then
			for p in "${proxy_patterns[@]}"; do
					sed -i "/$p/d" docker-compose.yml
			done
	else
			sed -i "0,/^ *- HTTP_PROXY/ s|HTTP_PROXY.*$|HTTP_PROXY=${HTTP_PROXY}|" docker-compose.yml
			sed -i "0,/^ *- http_proxy_url/ s|http_proxy_url.*$|http_proxy_url=${HTTP_PROXY}|" docker-compose.yml

			sed -i "0,/^ *- HTTPS_PROXY/ s|HTTPS_PROXY.*$|HTTPS_PROXY=${HTTPS_PROXY}|" docker-compose.yml
			sed -i "0,/^ *- https_proxy_url/ s|https_proxy_url.*$|https_proxy_url=${HTTPS_PROXY}|" docker-compose.yml

			sed -i "0,/^ *- NO_PROXY/ s|NO_PROXY.*$|NO_PROXY=${NO_PROXY}|" docker-compose.yml
			sed -i "0,/^ *- no_proxy/ s|no_proxy.*$|no_proxy=${NO_PROXY}|" docker-compose.yml
	fi
	#sed -i "0,/^ *- CONCOURSE_GARDEN_NETWORK/ s|- CONCOURSE_GARDEN_NETWORK.*$|#- CONCOURSE_GARDEN_NETWORK|" docker-compose.yml
	#sed -i "/^ *- CONCOURSE_EXTERNAL_URL/ a\    - CONCOURSE_NO_REALLY_I_DONT_WANT_ANY_AUTH=true" docker-compose.yml

}
init-adjust-config

###
# actually start bits an pieces
###
echo ${HOSTNAME} > $pidfile

function shutdown-all {
	log "${FUNCNAME[0]}: terminate!"
	fly-stop
	shutdown-internal-webserver
	shutdown-concourse-compose
	rm -f $pidfile
	log "${FUNCNAME[0]}: byebye"
	exit 0
}

function shutdown-internal-webserver {
	log "${FUNCNAME[0]}: stoping the static webserver"
	while docker ps --format "{{.Names}}" | grep concourse_nginx-$HOSTNAME | xargs docker stop 2> /dev/null; do  sleep 0.1;   done;
}

function startup-internal-webserver {
	log "${FUNCNAME[0]}: start a web server to host static files such as ovftool and NSX manager OVA"
	docker run --rm --name concourse_nginx-$HOSTNAME -v ${BIND_MOUNT_DIR}:/usr/share/nginx/html:ro -p ${IMAGE_WEBSERVER_PORT}:80 -d nginx
}
startup-internal-webserver


function shutdown-concourse-compose {
	log "${FUNCNAME[0]}: bringing down Concourse server cluster"
	docker-compose down
}
function startup-concourse-compose {
	log "${FUNCNAME[0]}: bringing up Concourse server in a docker-compose cluster"
	docker-compose up -d
	echo -n "wating for cluster "
	# waiting for the concourse API server to start up
	while ! curl -s -o /dev/null $CONCOURSE_URL ; do
		if [ ! -e $pidfile ]; then shutdown-all; fi
		echo -n "."
		sleep 0.5
	done
	echo " OK"
}
startup-concourse-compose


###
# here we takeoff and start to fly
###
function fly-stop {
	log "${FUNCNAME[0]}: killing"
	fly -t $CONCOURSE_TARGET destroy-pipeline -p $PIPELINE_NAME --non-interactive
}
function fly-sync { 
	log "${FUNCNAME[0]}: logging into concourse at $CONCOURSE_URL"
	fly -t $CONCOURSE_TARGET login --insecure -u nsx -p vmware --concourse-url $CONCOURSE_URL -n main
	fly -t $CONCOURSE_TARGET sync
}
fly-sync

function fly-reset {
    log "${FUNCNAME[0]}: setting the NSX-t install pipeline $PIPELINE_NAME"
	fly -t $CONCOURSE_TARGET set-pipeline -p $PIPELINE_NAME -c ${pipeline_dir}/pipelines/nsx-t-install.yml -l ${BIND_MOUNT_DIR}/${pipeline_internal_config} -l ${BIND_MOUNT_DIR}/${CONFIG_FILE_NAME} --non-interactive
}
fly-reset

function fly-start {
	log "${FUNCNAME[0]}: unpausing the pipepline $PIPELINE_NAME"
	fly -t $CONCOURSE_TARGET unpause-pipeline -p $PIPELINE_NAME
}
fly-start
function fly-status {
	fly targets
	fly -t $CONCOURSE_TARGET status
	fly -t $CONCOURSE_TARGET workers
	fly -t $CONCOURSE_TARGET pipelines
}

set +a

log "${FUNCNAME[0]}: adding various fly-functions to bashrc"
declare -f log fly-stop fly-sync fly-reset fly-start fly-status >> ~/.bashrc

log "${FUNCNAME[0]}: should all be ready at =====>>> ${CONCOURSE_URL} <<<====="


###
# going interactive or down
###

if [ -t 0 ] ; then
    log "${FUNCNAME[0]}: (interactive shell - use 'shutdown-all' to exit)"
    bash -c "bash --login"
	log "${FUNCNAME[0]}: (interactive shell - terminated with $?)"
else
    log "${FUNCNAME[0]}: (headless mode - remove '$pidfile' to terminate)"
    while [ -e $pidfile ]; do # checking-for-pid-existence-idle-loop
        sleep 1
		# if ! docker ps | grep -q concourse-worker; then log "${FUNCNAME[0]}: lost worker, not good"; fi
    done
    log "${FUNCNAME[0]}: (headless mode - pidfile was removed)"
	shutdown-all
fi

if [ -e $pidfile ]; then shutdown-all; fi
