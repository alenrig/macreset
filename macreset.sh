#!/bin/bash

echo "### Install Apple's Command Line Tools ###"
xcode-select --install

echo "### Install Ansible ###"
#export PATH="$HOME/Library/Python/3.9/bin:/opt/homebrew/bin:$PATH"
pip3 install --upgrade pip
pip3 install ansible

echo "### Install Ansible Requirements ###"
ansible-galaxy install -r requirements.yml

echo "### Run Ansible Playbook ###"
ansible-playbook main.yml --ask-become-pass
