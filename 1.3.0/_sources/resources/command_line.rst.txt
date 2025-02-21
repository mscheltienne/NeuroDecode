.. include:: ../links.inc

Command line
============

A ``Player``, or the legacy :class:`~mne_lsl.stream_viewer.StreamViewer`, can be
called from the command line. For each command, the flag ``-h`` or ``--help`` provides
additional information.

Player
------

An `MNE <mne stable_>`_ readable file can be streamed with a `~mne_lsl.player.PlayerLSL`
with the command:

.. code-block:: console

    $ mne_lsl_player file

With the arguments:

* ``file`` (mandatory): :term:`file-like <python:file object>`, file to stream (must be
  (readable with :func:`mne.io.read_raw`).
* ``-c``, ``--chunk_size`` (optional, default ``16``): :class:`int`, number of samples
  pushed at once.
* ``-n``, ``--name`` (optional, default ``MNE-LSL-Player``): :class:`str`, name of the
  LSL stream.
* ``--annotations`` (optional): enable streaming of annotations on a second
  :class:`~mne_lsl.lsl.StreamOutlet`.

StreamViewer
------------

A legacy :class:`~mne_lsl.stream_viewer.StreamViewer` can be opened with the command:

.. code-block:: console

    $ mne_lsl_stream_viewer

With the arguments:

- ``-s``, ``--stream_name`` (optional): :class:`str`, name of the stream to connect to.

.. note::

    If ``stream_name`` is not provided, a prompt is displayed to select a stream among
    the available ones.

The :class:`~mne_lsl.stream_viewer.StreamViewer` opens 2 windows:

- A controller to select the channels to plot and set different plotting parameters.
- A plotting window using the ``pyqtgraph`` backend displaying the signal in real-time.
