#!/bin/bash

echo "### Install Apple's Command Line Tools ###"
xcode-select --install


echo "### Install Ansible ###"
export PATH="$HOME/Library/Python/3.9/bin:/opt/homebrew/bin:$PATH"
sudo pip3 install --upgrade pip
pip3 install ansible

echo "### Install Ansible Requirements ###"
ansible-galaxy install -r requirements.yaml

echo "### Run Ansible Playbook ###"
ansible-playbook main.yaml --ask-become-pass


# echo "### Update vim ###"
# mkdir -p $HOME/.vim/bundle
# git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

# echo -e "### Update zsh ###"
# git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# mkdir -p .oh-my-zsh/custom/themes
# git clone https://github.com/dracula/zsh.git $HOME/zsh-dracula-theme
# cp -R $HOME/zsh-dracula-theme/{dracula.zsh-theme,lib} $HOME/.oh-my-zsh/custom/themes
# rm -rf $HOME/zsh-dracula-theme
