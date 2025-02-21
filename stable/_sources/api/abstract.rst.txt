Abstraction layer
-----------------

.. currentmodule:: mne_lsl.stream

An abstraction layer is provided to create a ``Stream`` object that uses a different
communication protocol than LSL. An object inheriting from
:class:`~mne_lsl.stream.BaseStream` will be compatible with other objects from
``mne-lsl``. For instance, it will be possible to epoch the stream with
:class:`~mne_lsl.stream.EpochsStream`.

.. autosummary::
    :toctree: ../generated/api
    :nosignatures:

    BaseStream
