# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/django-opensearch/django-opensearch-models/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                |    Stmts |     Miss |   Branch |   BrPart |      Cover |   Missing |
|-------------------------------------------------------------------- | -------: | -------: | -------: | -------: | ---------: | --------: |
| src/django\_opensearch\_models/\_\_init\_\_.py                      |       10 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/apps.py                              |       24 |        0 |        2 |        1 |     96.15% | 16-\>exit |
| src/django\_opensearch\_models/documents.py                         |       98 |        5 |       24 |        2 |     94.26% |63, 66, 94, 161, 196 |
| src/django\_opensearch\_models/exceptions.py                        |        8 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/fields.py                            |      136 |       15 |       46 |        5 |     84.62% |47, 56, 64, 88-95, 100, 146, 236-240 |
| src/django\_opensearch\_models/indices.py                           |       16 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/management/\_\_init\_\_.py           |        0 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/management/commands/\_\_init\_\_.py  |        0 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/management/commands/search\_index.py |      147 |       23 |       76 |        7 |     80.27% |107-108, 144-145, 152-158, 165-173, 194-196, 205-211, 264-265 |
| src/django\_opensearch\_models/models.py                            |        0 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/registries.py                        |      100 |       10 |       44 |        5 |     89.58% |39-40, 47-48, 94, 100-101, 109, 115-116, 118-\>111 |
| src/django\_opensearch\_models/search.py                            |       30 |        0 |        6 |        2 |     94.44% |24-\>29, 32-\>36 |
| src/django\_opensearch\_models/signals.py                           |       82 |        9 |       16 |        5 |     85.71% |95-98, 103-104, 132-\>exit, 141-\>exit, 154-155, 180-\>exit, 189-\>exit, 198 |
| src/django\_opensearch\_models/test/\_\_init\_\_.py                 |        2 |        0 |        0 |        0 |    100.00% |           |
| src/django\_opensearch\_models/test/testcases.py                    |       26 |        0 |        8 |        0 |    100.00% |           |
| **TOTAL**                                                           |  **679** |   **62** |  **222** |   **27** | **87.68%** |           |


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