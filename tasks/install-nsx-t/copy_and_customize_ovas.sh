#!/bin/bash

set -e

export ROOT_DIR=`pwd`

export TASKS_DIR=$(dirname $BASH_SOURCE)
export PIPELINE_DIR=$(cd $TASKS_DIR/../../ && pwd)
export FUNCTIONS_DIR=$(cd $PIPELINE_DIR/functions && pwd)

source $FUNCTIONS_DIR/copy_ovas.sh

DEBUG=""
if [ "$ENABLE_ANSIBLE_DEBUG" == "true" ]; then
  DEBUG="-vvv"
fi

NSX_T_MANAGER_OVA=$(ls $ROOT_DIR/nsx-mgr-ova)
NSX_T_CONTROLLER_OVA=$(ls $ROOT_DIR/nsx-ctrl-ova)
NSX_T_EDGE_OVA=$(ls $ROOT_DIR/nsx-edge-ova)

cat > customize_ova_vars.yml <<-EOF
ovftool_path: '/usr/bin'
ova_file_path: "$OVA_ISO_PATH"
nsx_manager_filename: "$NSX_T_MANAGER_OVA"
nsx_controller_filename: "$NSX_T_CONTROLLER_OVA"
nsx_gw_filename: "$NSX_T_EDGE_OVA"

EOF
cp customize_ova_vars.yml nsxt-ansible

install_ovftool
copy_ovsa_to_OVA_ISO_PATH

cd nsxt-ansible
ansible-playbook $DEBUG -i localhost customize_ovas.yml -e @customize_ova_vars.yml
STATUS=$?

echo ""

# if [ -z "$SUPPORT_NSX_VMOTION" -o "$SUPPORT_NSX_VMOTION" == "false" ]; then
#   echo "Skipping vmks configuration for NSX-T Mgr!!" 
#   echo 'configure_vmks: False' >> answerfile.yml
  
# else
#   echo "Allowing vmks configuration for NSX-T Mgr!!" 
#   echo 'configure_vmks: True' >> answerfile.yml
# fi

# echo ""

