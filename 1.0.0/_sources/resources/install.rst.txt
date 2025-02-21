.. include:: ../links.inc

Install
=======

Default install
---------------

``MNE-LSL`` requires Python version ``3.9`` or higher and is available on
`PyPI <project pypi_>`_. It requires ``liblsl`` which will be either fetch from the path
in the environment variable ``MNE_LSL_LIB``, or from the system directories or
downloaded from the release page on compatible platforms.

.. tab-set::

    .. tab-item:: PyPI

        .. code-block:: console

            $ pip install mne-lsl

    .. tab-item:: Source

        .. code-block:: console

            $ pip install git+https://github.com/mne-tools/mne-lsl

Different liblsl version
------------------------

If you prefer to use a different version of `liblsl <lsl lib c++_>`_ than the
automatically downloaded one, or if your platform is not supported, you can build
`liblsl <lsl lib c++_>`_ from source and provide the path to the library in an
environment variable ``MNE_LSL_LIB``.

liblsl and LabRecorder dependencies
-----------------------------------

On Linux, ``liblsl`` requires ``libpugixml-dev`` and ``LabRecorder`` requires
``qt6-base-dev`` and ``freeglut3-dev``.

.. code-block:: console

    $ sudo apt install -y libpugixml-dev qt6-base-dev freeglut3-dev

Qt
--

``MNE-LSL`` requires a Qt binding for the legacy
:class:`~mne_lsl.stream_viewer.StreamViewer` and for the future ``mne_lsl.Viewer``. All
4 Qt bindings, ``PyQt5``, ``PyQt6``, ``PySide2`` and ``PySide6`` are supported thanks to
``qtpy``. It is up to the user to make sure one of the binding is installed in the
environment.

.. warning::

    The legacy :class:`~mne_lsl.stream_viewer.StreamViewer` was developed and tested
    with ``PyQt5`` only.
