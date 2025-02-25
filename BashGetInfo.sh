#!/bin/bash

sshpass -p $3 ssh -oHostKeyAlgorithms=+ssh-dss "$2"@"$1" "timeout 120 bash -s" < $4
# sshpass -p $3 ssh "$2@$1" "echo Password | sudo -S dnf update"