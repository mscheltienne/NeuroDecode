:hide-toc:

.. include:: ./links.inc

MNE-LSL
=======

Open-source Python package for real-time brain signal streaming framework
based on the `Lab Streaming Layer (LSL) <lsl intro_>`_.

Install
-------

``MNE-LSL`` is available on `PyPI <project pypi_>`_ and `conda-forge <project conda_>`_.

.. tab-set::

    .. tab-item:: MNE installers

        As of `MNE-Python <mne stable_>`_ 1.6, ``mne-lsl`` is distributed in the
        `MNE standalone installers <mne installers_>`_.

        The installers create a conda environment with the entire MNE-ecosystem
        setup, and more! This installation method is recommended for beginners.

    .. tab-item:: PyPI

        ``mne-lsl`` can be installed from `PyPI <project pypi_>`_ using pip:

        .. code-block:: console

            $ pip install mne-lsl

    .. tab-item:: Conda

        ``mne-lsl`` can be installed from `conda-forge <project conda_>`_ using conda:

        .. code-block:: console

            $ conda install -c conda-forge mne-lsl

    .. tab-item:: Source

        ``mne-lsl`` can be installed from `GitHub <project github_>`_ or from the Source
        distribution. In this case, the installation will build `liblsl <lsl lib_>`_.

        .. code-block:: console

            $ pip install git+https://github.com/mne-tools/mne-lsl

        If you wish to skip building `liblsl <lsl lib_>`_, you can set the environment
        variable ``MNE_LSL_SKIP_LIBLSL_BUILD`` to ``1`` before running the installation,
        and use the environment variable ``MNE_LSL_LIB`` or ``PYLSL_LIB`` to specify the
        path to the `liblsl <lsl lib_>`_ library on your system.

        .. code-block:: console

            $ MNE_LSL_SKIP_LIBLSL_BUILD=1 pip install git+https://github.com/mne-tools/mne-lsl

Supporting institutions
-----------------------

.. image:: _static/partners/FCBG.svg
    :align: right
    :alt: FCBG - HNP - MEEG/BCI Platform
    :width: 100

The development of ``MNE-LSL`` is supported by the
`Fondation Campus Biotech Geneva <fcbg_>`_.

.. toctree::
    :hidden:

    resources/install.rst
    api/index.rst
    resources/command_line.rst
    resources/implementations.rst
    generated/tutorials/index.rst
    generated/examples/index.rst

.. toctree::
    :hidden:
    :caption: Development

    development/contributing.rst
    development/changes/index.rst
