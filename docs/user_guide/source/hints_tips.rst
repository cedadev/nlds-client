.. _hints_tips:

Hints and Tips
==============

This page is a list of hints and tips for using the NLDS effectively.

* :ref:`Getting all files in a holding <holding_files>`
* :ref:`Restarting transactions with FAILED files <fail_restart>`
* :ref:`Using the limit option <use_limit>`

.. _holding_files:

Getting all files in a holding
------------------------------

At first glance of the :ref:`command line reference<command-ref>`, it might not seem 
obvious how *all* the files in a holding can be retrieved all at once.  This is likely 
to be a common operation and, luckily, there are two different ways to do it:

#. Using a regular expression with the ``get`` command.
#. Generating a list using the ``find`` command and then using the ``getlist`` command to retrieve the files in the list.

Using a regular expression with the ``get`` command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

NLDS supports regular expressions (regex) for the parameters of certain commands, and 
the ``get`` command is one of those, with regex supported for the ``path`` parameter.  
This can be used to get all the files from a holding, by specifying the holding either
by ``id``, ``label`` or ``tag``.  If ``id``, ``label`` or ``tag`` is not specified, then
an error will be returned by NLDS.  This is to prevent returning many, or all, of the 
user's files when using regular expressions, as this would take a long time on the NLDS
server and lead to timeouts.

To ``get`` all the files in a holding use of the following:

.. code-block:: text

    > nlds get -i <holding id> -x ".*"
    > nlds get -l <label> -x ".*"
    > nlds get -t <key:value> -x ".*"

The regular expression can be more complicated, for example to get all the files below
a particular directory hierarchy:

.. code-block:: text

    > nlds get -i <holding id> -x "/path/to/the/files/you/want/to/retrieve/.*"

Generating a list using the ``find`` command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Another way to get all the files from a holding, or a selected subsection, is to first
generate a list of the files in the holding.  This can be done with the ``find`` 
command, using the ``-1`` or ``--simple`` command option to output a list where there is
one file per line.  This can be piped to a file using the ``>`` standard Linux pipe.

.. code-block:: text

    > nlds find -i <holding_id> -1 > filelist.txt
    > nlds find -l <label> -1 > filelist.txt
    > nlds find -t <key:value> -1 > filelist.txt

This can now be used with ``getlist`` to retrieve the files:

.. code-block:: text

    > nlds getlist -i <holding_id> filelist.txt -r <target directory>
    > nlds getlist -l <label> filelist.txt -r <target directory>
    > nlds getlist -t <key:value> filelist.txt -r <target directory>

Here the ``<holding_id>``, ``<label>`` or ``<key:value>`` is specified to guarantee that
the files in the filelist are retrieved from the holding from which the filelist was 
generated.  If one of these parameters was not given then the **newest** file that 
matches each filepath in the filelist would be retrieved.  This is because NLDS will 
retrieve the newest version of a file, unless the holding is identified.  Remember that 
filepaths have to be unique within a holding, but a filepath can be present in multiple 
holdings.

.. _fail_restart:

Restarting transactions with FAILED files
-----------------------------------------

Every so often, there will be a problem with NLDS, or the user will not have given a 
file read permission, or something else will go wrong, and a request to ``put`` files
will not ``COMPLETE`` fully.  Instead it will have the status of 
``COMPLETE_WITH_ERRORS`` and an indication as to how much, in percentage, the 
transaction finished.  NLDS will try to do as much as it can, and then report on the 
files it could not ingest.

Users can use the list of Failed Files to generate a filelist that can then be 
resubmitted to the same holding that the original list was ``put`` to.

For example:

.. code-block:: text

    > nlds putlist filelist.txt -l TestHolding

This will ``put`` a list of files to NLDS, in a holding called ``TestHolding``.  By 
using ``stat`` to query the status of this transaction, we can see that it has the 
status ``COMPLETE_WITH_ERRORS``

.. code-block:: text

    > nlds stat -b TestHolding
    State of transaction for user:nrmassey, group:cedaproc, id:34
        id              : 34
        user            : nrmassey
        group           : cedaproc
        action          : put
        transaction id  : 74f8d8fe-48e2-448d-ba8e-d1d156bd461e
        label           : TestHolding
        creation time   : 2025-01-08 12:13:39
        state           : COMPLETE_WITH_ERRORS
        last update     : 2025-01-08 15:58:06
        complete        :  50%

By using the ``-E``, a list of errors can be shown:

.. code-block:: text

    > nlds stat -i 34 -E
    State of transaction for user:nrmassey, group:cedaproc, id:34
        id              : 34
        user            : nrmassey
        group           : cedaproc
        action          : putlist
        transaction id  : ce2baf0a-2436-4e59-ac22-449000dee399
        label           : TestHolding
        creation time   : 2025-05-07 15:29:16
        state           : COMPLETE_WITH_ERRORS
        last update     : 2025-05-07 15:29:35
        complete        :  50%
        errors in sub records ->
        +   id           : 927
            failed files ->
            +   filepath : /Users/nrmassey/animals/minx.txt
                reason   : Path:/Users/nrmassey/animals/minx.txt is inaccessible.
            +   filepath : /Users/nrmassey/animals/pony.txt
                reason   : Path:/Users/nrmassey/animals/pony.txt is inaccessible.
            +   filepath : /Users/nrmassey/animals/unicorn.txt
                reason   : Path:/Users/nrmassey/animals/unicorn.txt is inaccessible.

Then by using the ``-F`` command with ``stat`` a list of the failed files can be output.

.. code-block:: text

    > nlds stat -i 34 -F
    /Users/nrmassey/animals/minx.txt
    /Users/nrmassey/animals/pony.txt
    /Users/nrmassey/animals/unicorn.txt

This can now be piped to a file and then resubmitted using ``putlist`` to the holding 
with the label ``TestHolding``:

.. code-block:: text

    > nlds stat -i 34 -F > resub_list.txt
    > nlds putlist -l TestHolding resub_list.txt
    putlist transaction accepted for processing.
        user            : nrmassey
        group           : cedaproc
        action          : putlist
        job label       : TestHolding
        transaction id  : 14ef54b6-fba0-46f4-b6b2-9fdfb28194b9
        label           : TestHolding

.. _use_limit:

Use the limit option
--------------------

NLDS ``find``, ``list`` and ``stat`` can produce a long output, which can take a while for the server 
to process.  Using the ``limit`` and ``ascending`` and ``descending`` options can help 
to prune the output, and speed up the processing on the server.  The ``limit`` option
has an effect at the database query level, which explains the speed-up when used with
``find``, ``list`` and ``stat``.

For example to return the 10 most recent transactions:

.. code-block:: text

    > nlds stat -L 10 -9

To return the 20 oldest holdings:

.. code-block:: text

    > nlds list -L 20 -0

To return the details of the 12 newest files that match a regular expression:

.. code-block:: text

    > nlds find -L 12 -x -p "/Users/nrmassey/animals/.*" 

The default is to list queries in descending order - i.e. newest first.
There is a default limit of ``1000``.  If a user wishes to return more than ``1000`` 
files, holdings or transactions, then they must specify ``-L <limit>``.