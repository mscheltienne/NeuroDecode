.. include:: ../links.inc

Contribution guide
==================

Thanks for taking the time to contribute! MNE-LSL is an open-source project sustained
mostly by volunteer effort. We welcome contributions from anyone as long as they abide
by our `Code of Conduct`_.

You can propose a change; a bugfix, a docstring improvement or a new feature; by
following those steps:

- `Fork the MNE-LSL repository`_ on GitHub
- Clone your fork locally
- (optional, recommended) Create a new branch for your changes
- Make your changes locally and push them to your fork
- `Open a pull request`_ with a clear title and description

Install in editable mode
------------------------

To modify MNE-LSL, it is recommended to install it in a separate environment in editable
mode. This way, you can test your changes without having to reinstall the package each
time. To install MNE-LSL in editable mode, run:

.. code-block:: console

    $ pip install -e .[all]

.. note::

    The ``[all]`` extra installs all optional dependencies, including those required for
    testing and documentation.

Code style
----------

MNE-LSL enforces style rules which are checked by the `pre-commit`_ framework. The rules
are configured in the project's ``pyproject.toml``. To install the pre-commit hooks,
run:

.. code-block:: console

    $ pre-commit install

Once installed, the hooks will run automatically before each commit. If you want to
manually run the hooks, you can use:

.. code-block:: console

    $ pre-commit run --all-files

.. note::

    If a PR is opened with failing pre-commit checks, the CIs will attempt to fix the
    failures automatically with an autofix commit.

Documentation
-------------

The documentation uses `Sphinx`_ and `numpydoc`_ to generate the HTML pages. The
`numpydoc`_ convention is used. To build the documentation locally, navigate to the
``doc`` directory and run:

.. code-block:: console

    $ make html

The HTML pages will be generated in the ``doc/_build/html`` directory. You can run the
following command to open a browser with the documentation:

.. code-block:: console

    $ make view

Finally, building the tutorials and examples is a slow process. To skip running the
examples and tutorials, run:

.. code-block:: console

    $ make html-noplot

Tests
-----

The unit tests are written using `pytest`_ and can be run from the root of the
repository with:

.. code-block:: console

    $ pytest mne_lsl

When adding a feature or fixing a bug, it is important to write a short test to ensure
that the code behaves as expected. Separate features should be tested in separate tests
to help keep the test function code short and readable. Finally, a test should use short
files and run as quickly as possible. Any tests that takes more than 5 seconds to run
locally should be marked with the ``@pytest.mark.slow`` decorator.

Tests are stored in the ``tests`` directory in each module. As much as possible, the
tests within a module should not test a different module, but this is obviously not
simple or mandatory as many modules require the creation of mock LSL stream to run the
tests.

Fixtures used in a single module should be defined within the module itself. If a
fixture is used in multiple modules, it should be defined in the ``mne_lsl/conftest.py``
file.

Finally, writing reliable tests with mock LSL stream or
:class:`~mne_lsl.lsl.StreamInlet` and :class:`~mne_lsl.lsl.StreamOutlet` can be tricky.
Here are a couple of tips to help you write reliable tests:

- If you create a mock LSL stream with :class:`~mne_lsl.player.PlayerLSL`, use the
  fixture ``chunk_size`` which returns a large chunk size suitable for CIs.
- If you need to create inlets or outlets, always close the inlets first before closing
  or destroying the outlets.

  .. note::

    A :class:`~mne_lsl.stream.StreamLSL` or :class:`~mne_lsl.player.PlayerLSL` have
    underlying LSL inlets and outlets. Don't forget to call
    :meth:`mne_lsl.stream.StreamLSL.disconnect` followed by
    :class:`mne_lsl.player.PlayerLSL.stop` at the end of your test.

- If you need to create :class:`~mne_lsl.lsl.StreamInlet` or
  :class:`~mne_lsl.lsl.StreamOutlet`
  directly, use the ``close_io`` fixture which returns a function to call at the end of
  your test to remove the inlets outlets.
- If the objects in your test use separate threads for acquisition or processing, don't
  forget to include sleep periods to ensure that the threads have time to work.

.. _fork the mne-lsl repository: https://github.com/mne-tools/mne-lsl/fork
.. _open a pull request: https://github.com/mne-tools/mne-lsl/compare
.. _numpydoc: https://numpydoc.readthedocs.io
.. _pre-commit: https://pre-commit.com
.. _pytest: https://docs.pytest.org
.. _sphinx: https://www.sphinx-doc.org
