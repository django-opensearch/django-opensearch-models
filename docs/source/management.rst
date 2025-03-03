Management Commands
###################

Delete all indices in OpenSearch or only the indices associate with a model (``--models``):

::

    $ search_index --delete [-f] [--models [app[.model] app[.model] ...]]


Create the indices and their mapping in OpenSearch:

::

    $ search_index --create [--models [app[.model] app[.model] ...]]

Populate the OpenSearch mappings with the Django models data (index need to be existing):

::

    $ search_index --populate [--models [app[.model] app[.model] ...]] [--parallel] [--refresh]

Recreate and repopulate the indices:

::

    $ search_index --rebuild [-f] [--models [app[.model] app[.model] ...]] [--parallel] [--refresh]

Recreate and repopulate the indices using aliases:

::

    $ search_index --rebuild --use-alias [--models [app[.model] app[.model] ...]] [--parallel] [--refresh]

Recreate and repopulate the indices using aliases, but not deleting the indices that previously pointed to the aliases:

::

    $ search_index --rebuild --use-alias --use-alias-keep-index [--models [app[.model] app[.model] ...]] [--parallel] [--refresh]
