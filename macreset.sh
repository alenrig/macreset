#!/bin/bash

echo "### Installing Homebrew ###"
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

echo "### Installing oh-my-zsh ###"
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

echo "### Update Packages ###"
brew update && brew outdated && brew upgrade && brew cleanup

packages=(
    ansible docker golang nvm pyenv pipenv nvim \
    minikube kubectl openshift-cli awscli terraform vagrant virtualbox wget \
    gotomeeting vk-messenger telegram-desktop zoom \
    visual-studio-code iterm2 \
    alfred notion transmission musescore \
    loom copyclip cleanshot youtube-dl \
    obsidian slack balenaetcher bartender wireguard \
    fantastical google-drive firefox
)

echo "### Install Packages ###"
for package in ${packages[@]}
do
    brew install $package
done
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash

echo "### Update Configs ###"
cp dots/.zshrc $HOME
cp dots/.vimrc $HOME

mkdir -p $HOME/.config/nvim
cp dots/init.vim /$HOME/.config/nvim

echo "### Update vim ###"
mkdir -p $HOME/.vim/bundle
git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim

echo -e "### Update zsh ###"
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

mkdir -p .oh-my-zsh/custom/themes
git clone https://github.com/dracula/zsh.git $HOME/zsh-dracula-theme
cp -R $HOME/zsh-dracula-theme/{dracula.zsh-theme,lib} $HOME/.oh-my-zsh/custom/themes
rm -rf $HOME/zsh-dracula-theme
