#!/bin/bash
# Syncs remote "production" db to local development environment

source local_env.sh

psql $DATABASE_NAME $DATABASE_USER -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public"
echo "ssh ${SSH_USER}@${SSH_HOSTNAME} -p $SSH_PORT pg_dump | psql $DATABASE_NAME $DATABASE_USER"
ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT pg_dump | psql $DATABASE_NAME $DATABASE_USER
