#!/bin/bash

echo $0

echo "Creating $HOME/bin/matprojman folder..."
mkdir -p $HOME/bin/matprojman
echo "cp -R `readlink -f \`dirname \`dirname $0\`\``/* $HOME/bin/matprojman/"

echo "Installing requirements..."
pip install --user -r $HOME/bin/matprojman/requirements.txt

echo "Add the following to your .zshrc or .bashrc file (or whatever analogue for your own shell)"
cat `readlink -f \`dirname \`dirname $0\`\``/.add_path_example.txt


