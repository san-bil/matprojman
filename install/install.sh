#!/bin/bash

echo  "Creating $HOME/bin/matprojman folder..."
mkdir -p $HOME/bin/matprojman
cp -R $( dirname $( dirname $( readlink -f $0 ) ) )/* $HOME/bin/matprojman/

echo -e "Installing requirements...\n"
pip install --user -r $HOME/bin/matprojman/requirements.txt

echo -e "Add the following to your .zshrc or .bashrc file (or whatever analogue for your own shell)\n"
echo -e "########################################################\n\n"
cat $( dirname -f $( dirname $( readlink -f $0 ) ) )/.add_path_example.txt
echo -e "########################################################\n\n"


