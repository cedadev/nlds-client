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

#. It is a good idea to upgrade your version of pip - otherwise some modules may fail to install: |br|
   ``pip install --upgrade pip``

#. Install the nlds-client package from GitHub: |br|
   ``pip install git+https://github.com/cedadev/nlds-client.git``


Upgrading to v1.0.12
============
Here's how to upgrade the NLDS client to v1.0.12:

#. Activate your virtual environment: |br|
   ``source ~/nlds-client/bin/activate``

#. Upgrade using the latest nlds-client package from GitHub: |br|
   ``pip install —upgrade git+https://github.com/cedadev/nlds-client.git@1.0.12``

#. Check if you have the right client by issuing the command: |br|
   ``nlds —version`` |br|
   The output should start with: ``Near Line Data Store client 1.0.12``
   
#. Update your ``~/.nlds-config`` file: |br|
   The line that reads ``"api": "api/0.1"`` should now read ``"api": "api/1.0.0"``
