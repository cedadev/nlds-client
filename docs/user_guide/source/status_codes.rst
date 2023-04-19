.. _status_codes:

Status Codes 
============

When the NLDS is asked to PUT or GET some data, the transaction goes through a 
number of states from initialisation to completion.  
The state of a transaction can be queried by using the ``nlds stat`` command
in the ``nlds_client``.

Transaction states
------------------

+------+----------------------------+------------------------------------------+
|``-1``|``'INITIALISING'``          |  Transaction is starting                 |
|      |                            |                                          |
+------+----------------------------+------------------------------------------+
|``0`` |``'ROUTING'``               |  Transaction is in the message queue     |
|      |                            |                                          |
+------+----------------------------+------------------------------------------+
|``1`` |``'SPLITTING'``             |  Transaction is being split into smaller |
|      |                            |  transactions.  The user doesn't have to |
|      |                            |  worry about this.                       |
+------+----------------------------+------------------------------------------+
|``2`` |``'INDEXING'``              |  Scanning the files and directories in   |
|      |                            |  the PUT transaction.                    |
+------+----------------------------+------------------------------------------+
|``3`` |``'CATALOG_PUTTING'``       |  Recording the scanned files into the    |
|      |                            |  catalog entry for the transaction.      |
+------+----------------------------+------------------------------------------+
|``4`` |``'TRANSFER_PUTTING'``      |  Putting the files to the NLDS, actually |
|      |                            |  transferring the data.                  |
+------+----------------------------+------------------------------------------+
|``5`` |``'CATALOG_ROLLBACK'``      |  Remove, from the catalog, any           |
|      |                            |  inaccessible files in the transaction.  |
+------+----------------------------+------------------------------------------+
|``6`` |``'CATALOG_GETTING'``       |  Get a catalog entry.                    |
|      |                            |                                          |
+------+----------------------------+------------------------------------------+
|``7`` |``'TRANSFER_GETTING'``      |  Getting the files from the NLDS.        |
|      |                            |                                          |
+------+----------------------------+------------------------------------------+
|``8`` |``'COMPLETE'``              |  Transaction has completed successfully. |
|      |                            |                                          |
+------+----------------------------+------------------------------------------+
|``9`` |``'FAILED'``                |  Transaction has failed completely.      |
|      |                            |                                          |
+------+----------------------------+------------------------------------------+
|``10``|``'COMPLETE_WITH_ERRORS'``  |  Transaction has completed, but with some|
|      |                            |  errors.                                 |
+------+----------------------------+------------------------------------------+
|``11``|``'COMPLETE_WITH_WARNINGS'``|  Transaction has completed, but with some|
|      |                            |  warnings                                |
+------+----------------------------+------------------------------------------+