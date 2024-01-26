.. |br| raw:: html

  <br/>

.. _installation:

Installation
============
To use the NLDS, first you must install the client software.  This guide will show
you how to install it into a Python virtual-environment (virtualenv) in your
user space or home directory.

#. Log onto the machine where you wish to install the NLDS client into your 
   user space or home directory.

#. Create a Python virtual environment: |br|
   ``python3 -m venv ~/nlds-client``

#. Activate your new virtual environment: |br|
   ``source ~/nlds-client/bin/activate``

#. Install the nlds-client package from github: |br|
   ``pip install git+https://github.com/cedadev/nlds-client.git``
