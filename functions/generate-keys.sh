#!/usr/bin/env bash

set -e -u -x

mkdir -p keys/web keys/worker

openssl genpkey -algorithm RSA -out ./keys/web/tsa_host_key -pkeyopt rsa_keygen_bits:4096
openssl genpkey -algorithm RSA -out ./keys/web/session_signing_key -pkeyopt rsa_keygen_bits:4096
openssl genpkey -algorithm RSA -out ./keys/worker/worker_key -pkeyopt rsa_keygen_bits:4096

chmod 600 ./keys/ -R

ssh-keygen -y -f  ./keys/web/tsa_host_key > ./keys/web/tsa_host_key.pub
ssh-keygen -y -f  ./keys/web/session_signing_key > ./keys/web/session_signing_key.pub
ssh-keygen -y -f  ./keys/worker/worker_key > ./keys/worker/worker_key.pub

cp ./keys/worker/worker_key.pub ./keys/web/authorized_worker_keys
cp ./keys/web/tsa_host_key.pub ./keys/worker