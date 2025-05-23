Contributing
############

We are glad to welcome any contributor.

Report bugs or propose enhancements through  `github bug tracker`_

_`github bug tracker`: https://github.com/django-opensearch/django-opensearch-models/issues


If you want to contribute, the code is on github:
https://github.com/django-opensearch/django-opensearch-models

Testing
=======


You can run the tests by creating a Python virtual environment, installing
the requirements from ``requirements_test.txt`` (``pip install -r requirements_test``)::

    $ python runtests.py


For integration testing with a running OpenSearch server::

    $ python runtests.py --opensearch [localhost:9200]

TODO
====

- Add support for --using (use another OpenSearch cluster) in management commands.
- Add management commands for mapping level operations (like update_mapping....).
- Generate ObjectField/NestField properties from a Document class.
- More examples.
- Better ``OSTestCase`` and documentation for testing


