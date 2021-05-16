#!/bin/bash

echo "### Installing Homebrew ###"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

echo "### Installing oh-my-zsh ###"
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

echo "### Update Packages ###"
brew update && brew outdated && brew upgrade && brew cleanup

packages=(
    ansible docker golang nvm pyenv pipenv nvim \
    minikube kubectl terraform vagrant virtualbox wget \
    gotomeeting vk-messenger telegram-desktop zoomus \
    visual-studio-code \
    alfred notion teamviewier transmission musescore \
    loom copyclip cleanshot youtube-dl
)

echo "### Install Packages ###"
for package in ${packages[@]}
do
    brew install $package
done
