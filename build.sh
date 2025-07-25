#!/bin/bash

# Always start from the repo root
cd "$(dirname "$0")"

# Optional: Print current dir and its contents for debugging
echo "Working Directory: $(pwd)"
echo "Files:"
ls -la

# Install Python 3.11 manually
curl -O https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xzf Python-3.11.9.tgz
cd Python-3.11.9
./configure --prefix=$HOME/python-3.11.9
make
make install

# Go back to root after installing Python
cd ..

# Update PATH so new Python is used
export PATH=$HOME/python-3.11.9/bin:$PATH
python3 --version

# Install requirements
pip3 install --upgrade pip setuptools
pip3 install -r requirements.txt
