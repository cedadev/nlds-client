Installation
============

To use NLDS, first you must install the client software.  This guide will show
you how to install it into a Python virtual-environment (virtualenv) in your
user space or home directory.

1. log into the machine where you wish to install the JDMA client into your user
   space or home directory.

1.  Create a Python virtual environment:
    `python3 -m venv ~/nlds-client`

2.  Activate the nlds-client:
    `source ~/nlds-client/bin/activate`

3.  Install the nlds-client package from github:
    `pip install git+https://github.com/cedadev/nlds-client.git@0.1.1#egg=nlds-client`