#!/bin/bash
set -e


export ROOT_DIR=`pwd`

export TASKS_DIR=$(dirname $BASH_SOURCE)
export PIPELINE_DIR=$(cd $TASKS_DIR/../../ && pwd)
export FUNCTIONS_DIR=$(cd $PIPELINE_DIR/functions && pwd)
export SCRIPT_DIR=$(dirname $0)

python $TASKS_DIR/nsx_t_gen.py --router_config true --generate_cert false

STATUS=$?

exit $STATUS
