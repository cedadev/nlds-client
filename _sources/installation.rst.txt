.. |br| raw:: html

  <br/>

.. _installation:

Installation
============

.. note::
   In January 2026, a more intuitive method of installation using PyPi was rolled out to NLDS users.  The instructions below are for this new installation method.

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

#. Install the nlds-client package from PyPi: |br|
   ``pip install nlds-client``


Upgrading to v1.0.17
--------------------

.. note::
   In January 2026, hosting of the NLDS client was moved to PyPi.  Previous installations of ``nlds-client`` from GitHub may have to be removed using ``pip uninstall``.

#. Activate your virtual environment: |br|
   ``source ~/nlds-client/bin/activate``

#. Upgrade using the latest nlds-client package from GitHub: |br|
   ``pip install --upgrade nlds-client``

#. If the above point produces an error, then you may need to uninstall your previous version of ``nlds-client`` and install the new one:
   ``pip uninstall nlds-client`` |br|
   ``pip install nlds-client``

#. Check if you have the right client by issuing the command: |br|
   ``nlds --version`` |br|
   The output should start with: ``Near Line Data Store client 1.0.12``
   
#. You may need to update your NLDS client config.  This can be done using the ``init`` command:
   ``nlds init`` |br|
   This will ask for your user name and password, regenerate your OAuth access tokens and object storage keys, and make any necessary changes in your config file.
