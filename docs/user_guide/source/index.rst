.. Near-Line Data Store client documentation master file, created by
   sphinx-quickstart on Thu Feb  2 16:17:53 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Near-Line Data Store - Client documentation
===========================================

The Near-Line Data Store (NLDS) is a multi-tiered storage solution that uses 
Object Storage as a front end cache to a tape library. It catalogs the data as 
it is ingested and permits multiple versions of files. It has a microservice 
architecture using a message broker to communicate between the parts.
Interaction with NLDS is via a HTTP API, with a Python library and command-line 
client provided to users for programmatic or interactive use.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   installation.rst
   configuration.rst
   step_by_step.rst
   tutorial.rst
   catalog_organisation.rst
   status_codes.rst
   command_ref.rst
   license.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Acknowledgements
================

NLDS was developed at the `Centre for Environmental Data Analysis <https://www.ceda.ac.uk>`_
with support from the ESiWACE2 project. The project ESiWACE2 has received 
funding from the European Union's Horizon 2020 research and innovation programme
under grant agreement No 823988. 

.. image:: _images/esiwace2.png
   :width: 300
   :alt: ESiWACE2 Project Logo

.. image:: _images/ceda.png
   :width: 300
   :alt: CEDA Logo


NLDS is Open-Source software with a BSD-2 Clause License.  The license can be
read :ref:`here <license>`.