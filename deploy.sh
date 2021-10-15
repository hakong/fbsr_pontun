#!/bin/bash
# Deploys code to target server

source local_env.sh

scp -P $SSH_PORT schema.sql ${SSH_USERNAME}@${SSH_HOSTNAME}: 
tar -f - -c --exclude="__pycache__" --exclude="local_config.py" backend mailer.py | ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT tar -x -f -
ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT killall gunicorn
ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT killall python
tar -f - -c scripts | ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT tar -x -f -

ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT rm -r build
cd frontend
npm run-script build
tar -f - -c build | ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT tar -x -f -
ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT rm -r frontend-build
ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT mv build frontend-build
cd ..

cd admin
npm run-script build
tar -f - -c build | ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT tar -x -f -
ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT rm -r admin-build
ssh ${SSH_USERNAME}@${SSH_HOSTNAME} -p $SSH_PORT mv build admin-build


