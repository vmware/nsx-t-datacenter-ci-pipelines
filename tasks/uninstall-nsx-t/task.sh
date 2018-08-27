#!/bin/bash
set -e

export ROOT_DIR=`pwd`

export TASKS_DIR=$(dirname $BASH_SOURCE)
export PIPELINE_DIR=$(cd $TASKS_DIR/../../ && pwd)
export FUNCTIONS_DIR=$(cd $PIPELINE_DIR/functions && pwd)

echo "Unimplemented !!"

STATUS=$?
popd  >/dev/null 2>&1

exit $STATUS
