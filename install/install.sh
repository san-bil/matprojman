#!/bin/bash

echo "Creating $HOME/bin/matprojman folder..."
mkdir -p $HOME/bin/matprojman
echo "cp -R `dirname \`dirname $0\``/* $HOME/bin/matprojman/"

echo "Installing requirements..."
pip install --user -r $HOME/bin/matprojman/requirements.txt

echo "Add the following to your .zshrc or .bashrc file (or whatever analogue for your own shell)"
cat `dirname \`dirname $0\``/.add_path_example.txt


