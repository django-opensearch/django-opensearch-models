# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/django-opensearch/django-opensearch-models/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|-------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| src/django\_opensearch\_models/\_\_init\_\_.py                      |       10 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/apps.py                              |       24 |        0 |        2 |        1 |     96.15% | 16-\>exit |
| src/django\_opensearch\_models/documents.py                         |      103 |        4 |       24 |        1 |     96.06% |68, 71, 112, 227 |
| src/django\_opensearch\_models/exceptions.py                        |        8 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/fields.py                            |      146 |        8 |       38 |        3 |     92.93% |56, 65, 107, 153, 243-247 |
| src/django\_opensearch\_models/indices.py                           |       16 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/management/\_\_init\_\_.py           |        0 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/management/commands/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/management/commands/search\_index.py |      165 |       23 |       84 |        9 |     81.53% |109-110, 134-\>118, 154-155, 162-168, 175-183, 204-206, 215-221, 261-\>269, 301-302 |
| src/django\_opensearch\_models/models.py                            |        0 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/registries.py                        |      100 |       10 |       44 |        5 |     89.58% |39-40, 47-48, 94, 100-101, 109, 115-116, 118-\>111 |
| src/django\_opensearch\_models/search.py                            |       30 |        0 |        6 |        2 |     94.44% |24-\>29, 32-\>36 |
| src/django\_opensearch\_models/signals.py                           |       94 |       10 |       18 |        2 |     89.29% |99-102, 107-108, 166-167, 170-171, 192-\>exit, 201-\>exit |
| src/django\_opensearch\_models/test/\_\_init\_\_.py                 |        2 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/test/testcases.py                    |       26 |        0 |        8 |        0 |    100.00% |           |
| **TOTAL**                                                           |  **724** |   **55** |  **224** |   **23** | **90.08%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/django-opensearch/django-opensearch-models/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/django-opensearch/django-opensearch-models/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/django-opensearch/django-opensearch-models/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/django-opensearch/django-opensearch-models/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fdjango-opensearch%2Fdjango-opensearch-models%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/django-opensearch/django-opensearch-models/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.