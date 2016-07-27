# dmtg #

The `dmtg` utility is simple Python/Lua utility that creates Magic draft boards for Tabletop Simulator.

## Install ##

Run the following commands in order to install all third-party dependencies:

1. `sudo apt-get install pip virtualenv`: Install library management utilities for Python.
1. `sudo apt-get install libxml2-dev libxslt1-dev python-dev zlib1g-dev`: Install dependencies of the `lxml` library.
1. `virtualenv venv`: Create a virtual environment for all of the Python dependencies.
1. `source venv/bin/activate`: Activate the virtual environment to install dependencies locally.
1. `pip install -r requirements.txt`: Install all Python dependencies into the local virtual environment.
