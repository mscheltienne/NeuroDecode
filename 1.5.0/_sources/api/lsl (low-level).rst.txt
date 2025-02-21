.. include:: ../links.inc

LSL (low-level)
---------------

.. currentmodule:: mne_lsl.lsl

If the high-level API is not sufficient, the low-level API interface directly with
`liblsl <lsl lib_>`_, with a similar API to `pylsl <lsl python_>`_.

Compared to `pylsl <lsl python_>`_, ``mne_lsl.lsl`` pulls a chunk of *numerical* data
faster thanks to ``numpy``. In numbers, pulling a 1024 samples chunk with 65 channels in
double precision (``float64``) to python takes:

* 4.33 ms ± 37.5 µs with ``pylsl`` default behavior
* 471 ns ± 1.7 ns with ``pylsl`` using a :class:`~numpy.ndarray` as ``dest_obj`` to
  prevent memory re-allocation
* 268 ns ± 0.357 ns with ``mne_lsl.lsl`` which uses :func:`numpy.frombuffer` under the
  hood

More importantly, ``pylsl`` dewfault behavior pulls a chunk in linear time ``O(n)``,
scalings with the number of values; while ``mne_lsl.lsl`` pulls a chunk in constant time
``O(1)``. Additional details on the differences with ``pylsl`` and ``mne_lsl`` can be
found :ref:`here<resources/pylsl:Differences with pylsl>`.

.. autosummary::
    :toctree: ../generated/api
    :nosignatures:

    StreamInfo
    StreamInlet
    StreamOutlet
    library_version
    protocol_version
    local_clock
    resolve_streams
