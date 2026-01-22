.. _command-ref:

Command Line Reference
======================

The primary method of interacting with the Near-Line Data Store is through a
command line client, which can be installed using the instructions.

Users must specify a command to the ``nlds`` and options and arguments for that 
command.

``nlds [OPTIONS] COMMAND [ARGS]...``

As an overview the commands are:

Commands:
  | ``find     Find and list files.``
  | ``get      Get a single file.``
  | ``getlist  Get a number of files specified in a list.``
  | ``init     Set up the nlds client with a config file on first use.``
  | ``list     List holdings.``
  | ``meta     Alter metadata for a holding.``
  | ``renew    Renew the OAuth tokens and object store access and secret keys``
  | ``put      Put a single file.``
  | ``putlist  Put a number of files specified in a list.``
  | ``stat     List transactions.``

Each command has its own specific options.  The argument is generally the file
or filelist that the user wishes to operate on.  The full command listing is
given below.

.. click:: nlds_client.nlds_client:nlds_client
   :prog: nlds
   :nested: full