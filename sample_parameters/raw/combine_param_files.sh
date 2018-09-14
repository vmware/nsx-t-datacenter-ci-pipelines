#!/bin/bash
nsx_yaml="nsx.yml"
nsx_yaml_tmp="nsx.yml.tmp"
param_file="nsx_pipeline_config.yml"
cp $nsx_yaml $nsx_yaml_tmp
echo "" >> $nsx_yaml_tmp
echo "" >> $nsx_yaml_tmp
cat $nsx_yaml_tmp pks.yml > ../PKS_only/${param_file}
cat $nsx_yaml_tmp pas.yml > ../PAS_only/${param_file}
cat $nsx_yaml_tmp pas_pks.yml > ../PAS_and_PKS/${param_file}
rm $nsx_yaml_tmp
