#!/bin/bash
echo $secret_id
DB_USER=`aws secretsmanager get-secret-value --secret-id $secret_id | jq --raw-output .SecretString | jq -r ."username"`
DB_PASS=`aws secretsmanager get-secret-value --secret-id $secret_id | jq --raw-output .SecretString | jq -r ."password"`
DB_HOST=`aws secretsmanager get-secret-value --secret-id $secret_id | jq --raw-output .SecretString | jq -r ."host"`
echo $DB_NAME
echo $DB_USER
echo $DB_PASS
echo $DB_HOST
docker build --no-cache -t $cluster_id --build-arg DB_USER=$DB_USER --build-arg DB_PASS=$DB_PASS  --build-arg DB_HOST=$DB_HOST  --build-arg DB_NAME=$DB_NAME . 
