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

echo "### Update Configs ###"
cp dots/{.zshrc, .vimrc} $HOME

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
