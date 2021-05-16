" =====================================================
" Plugins Manager
" =====================================================
set nocompatible
filetype plugin on
syntax on

set laststatus=2
set ttyfast
set undofile
set noshowmode
set omnifunc=syntaxcomplete#Complete
set rtp+=~/.vim/bundle/Vundle.vim

call vundle#begin()

"--------------=== Navigation ===---------------
Plugin 'scrooloose/nerdtree'

"--------------=== Languages support ===---------------
"--- Universal ---
Plugin 'jiangmiao/auto-pairs'		" автодополнение скобок

" - Git -
Plugin 'airblade/vim-gitgutter'

" --- LaTeX ---
Plugin 'lervag/vimtex'
Plugin 'KeitaNakamura/tex-conceal.vim'

"--------------=== Other ===---------------
Plugin 'lifepillar/vim-cheat40'

Plugin 'bling/vim-airline'
Plugin 'vim-airline/vim-airline-themes'

Plugin 'fisadev/FixedTaskList.vim'      " Pending tasks list

Plugin 'tpope/vim-surround'             " Parentheses, brackets, quotes, XML tags, and more
Plugin 'tpope/vim-fugitive'		" git on airline
Plugin 'tpope/vim-repeat'		" Repeat plugin by dot command
Plugin 'tpope/vim-commentary'           " Simple commentary

Plugin 'powerman/vim-plugin-ruscmd'     " русификатор команд

" ---=== Themes ===---
Plugin 'dracula/vim'


Plugin 'VundleVim/Vundle.vim'

call vundle#end()            " required
filetype plugin indent on    " required


"=====================================================
" General Settings
"=====================================================
set t_Co=256
syntax on
colorscheme dracula
highlight Normal ctermbg=NONE
set termguicolors

set noerrorbells
set number
set relativenumber
set path+=**		" search for every subdirectory
set nowrap
set nobackup
set noundofile
set nowritebackup
set encoding=utf8
set fileencoding=utf8
set mousehide
set history=50		" keep 50 lines of command line history
set ruler		" show the cursor position all the time
set showcmd		" display incomplete commands
set autoindent		" always set autoindenting on
set wildmenu		" show all matching files after Tab
set wcm=<Tab>
set foldnestmax=2

let g:auto_save = 1

" --- Search ---
set hlsearch
set incsearch
set ignorecase
set smartcase

" allow backspacing over everything in insert mode
set backspace=indent,eol,start

" The matchit plugin makes the % command work better, but it is not backwards compatible.
packadd matchit

" In many terminal emulators the mouse works just fine, thus enable it.
if has('mouse')
  set mouse=a
endif

" настройки Vim-Airline
set laststatus=2
let g:airline_powerline_fonts = 1
let g:airline_theme = 'dracula'
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#formatter = 'unique_tail'


"=====================================================
" Keys Bindings
"=====================================================
" ===== Nerd Tree Options =====
" close Nerd Tree if it is a last opened window
autocmd bufenter * if (winnr("$") == 1 && exists("b:NERDTree") && b:NERDTree.isTabTree()) | q | endif
" показать NERDTree на F2
map <F2> :NERDTreeToggle<CR>
"игноррируемые файлы с расширениями (python, latex)
let NERDTreeIgnore=['\~$', '\.pyc$', '\.pyo$', '\.class$', 'pip-log\.txt$', '\.o$',
\ '\.aux$', '\.bbl$', '\.bcf$', '\.blg$', '\.pdf$', '\.toc$', '\.log$',
\ '\.gz$', '\.run*']

" === TaskList ===
map <F3> :TaskList<CR>

" === Git Fugitive ===
nnoremap <F4> :Gstatus<CR>

" === Spell check ===
menu SetSpell.ru  :set spl=ru spell<CR>
menu SetSpell.en  :set spl=en spell<CR>
menu SetSpell.off :set nospell<CR>
map <F8> :emenu SetSpell.<Tab>
imap <F9> <Esc> z=<CR>i
map <F9> z=<CR>

"=== Escape insert mode via 'jj' ===
imap jj <ESC>

" автокомплит через <Ctrl+Space>
inoremap <C-space> <C-x><C-o>


"=================================
" LaTeX settings
"=================================
autocmd FileType tex setlocal expandtab shiftwidth=4 tabstop=8 textwidth=80
\ smartindent updatetime=1
let g:tex_flavor='latex'
set conceallevel=2
let g:tex_conceal="abdgm"

"=================================
" Shell settings
"=================================
autocmd FileType sh setlocal expandtab shiftwidth=2 tabstop=4
\ softtabstop=2 smartindent

"=================================
" YML settings
"=================================
autocmd FileType yaml setlocal expandtab shiftwidth=2 tabstop=4
\ softtabstop=2 smartindent
