.. include:: ../links.inc

Most-used classes
-----------------

The main objects offer efficient communication with numerical streams.

Stream
~~~~~~

A ``Stream`` uses an `MNE <mne stable_>`_-like API to efficiently interacts with a
numerical stream.

.. currentmodule:: mne_lsl.stream

.. autosummary::
    :toctree: ../generated/api
    :nosignatures:

    StreamLSL

Player
~~~~~~

A ``Player`` can mock a real-time stream from any `MNE <mne stable_>`_ readable file.

.. currentmodule:: mne_lsl.player

.. autosummary::
    :toctree: ../generated/api
    :nosignatures:

    PlayerLSL
