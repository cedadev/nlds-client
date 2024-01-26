.. _status_codes:

Status Codes 
============

When the NLDS is asked to PUT or GET some data, the transaction goes through a 
number of states from initialisation to completion.  
The state of a transaction can be queried by using the ``nlds stat`` command
in the ``nlds_client``.

Transaction states
------------------

.. csv-table ::
    :file: status_codes.csv
    :widths: 10 30 60
    :header-rows: 1