=================================
Django OpenSearch Models Test App
=================================

Simple django app for test some django-opensearch-models features.


Installation
------------

In a python virtualenv run::

    $ pip install -r requirements.txt


You need an OpenSearch server running. Then change the OpenSearch
connections setting in example/settings.py.

.. code:: python

    OPENSEARCH_DSL={
        'default': {
            'hosts': 'localhost:9200'
        },
    }

To launch a functional server::

    $ ./manage.py migrate
    $ ./manage.py createsuperuser

You can use django-autofixture for populate django models with fake data::

    $ ./manage.py loadtestdata test_app.Manufacturer:10 test_app.Car:100 test_app.Ad:500

Then build the OpenSearch index with::

    $ ./manage.py search_index --rebuild

And run the server (there is django admin but not any views yet)::

    $ ./manage.py runserver
