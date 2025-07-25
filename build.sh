#!/bin/bash
# Install Python 3.11 manually (as a fallback if runtime.txt is ignored)
curl -O https://www.python.org/ftp/python/3.11.9/Python-3.11.9.tgz
tar -xzf Python-3.11.9.tgz
cd Python-3.11.9
./configure --prefix=$HOME/python-3.11.9
make
make install

# Update PATH
export PATH=$HOME/python-3.11.9/bin:$PATH
python3 --version

# Install requirements using new Python
pip3 install -r requirements.txt
