#!/bin/bash

echo "### Install Apple's Command Line Tools ###"
xcode-select --install

echo "### Install Ansible ###"
python3 -m venv $HOME/.local --system-site-packages
$HOME/.local/bin/pip install --upgrade pip
$HOME/.local/bin/pip install pipx
$HOME/.local/bin/pipx install ansible

echo "### Install Ansible Requirements ###"
$HOME/.local/bin/ansible-galaxy install -r requirements.yml

echo "### Run Ansible Playbook ###"
$HOME/.local/bin/ansible-playbook main.yml --ask-become-pass
