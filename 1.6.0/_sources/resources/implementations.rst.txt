.. include:: ../links.inc

Implementation details
======================

Processing
----------

The :class:`~mne_lsl.stream.StreamLSL` and :class:`~mne_lsl.stream.EpochsStream` object
support processing in real-time of their internal buffers. The processing is done
sequentially and this page presents the available processing and their application
order.

StreamLSL
~~~~~~~~~

Processing is applied to new samples available in the
:class:`~mne_lsl.lsl.StreamInlet` before rolling the buffer of the
:class:`~mne_lsl.stream.StreamLSL` object and adding those new processed samples to it.
The processing is defined in the private ``_acquire`` method of the class
:class:`~mne_lsl.stream.StreamLSL`, method called by the background acquisition thread
(automatic acquisition) or by the method :meth:`mne_lsl.stream.StreamLSL.acquire`
(manual acquisition).

1. Add channels that were added with
   :meth:`mne_lsl.stream.StreamLSL.add_reference_channels`. The channels are added as an
   array of zeros at the end of the buffer along the channel axis.
2. Apply the rereferencing schema requested with
   :meth:`mne_lsl.stream.StreamLSL.set_eeg_reference`.
3. Apply filters added with :meth:`mne_lsl.stream.StreamLSL.filter` and
   :meth:`mne_lsl.stream.StreamLSL.notch_filter`. The filters are applied one at a time,
   in the order they were added.

.. image:: ../_static/resources/stream-processing.svg
    :align: right
    :alt: Stream processing flowchart
    :width: 100%

EpochsStream
~~~~~~~~~~~~

Processing is applied to new events and samples available to a
:class:`~mne_lsl.stream.EpochsStream` before rolling the buffer of the
:class:`~mne_lsl.stream.EpochsStream` object and adding new epochs to it.
The processing is defined in the private ``_acquire`` method of the class
:class:`~mne_lsl.stream.EpochsStream`, method called by the background acquisition
thread (automatic acquisition) or by the method
:meth:`mne_lsl.stream.EpochsStream.acquire` (manual acquisition); and in the private
``_process_data`` function which operates on the newly acquired data array of shape
``(n_epochs, n_samples, n_channels)``.

.. note::

    `MNE-Python <mne stable_>`_ offers similar processing to a :class:`~mne.io.Raw` and
    :class:`~mne.Epochs` object. However, ``mne-lsl`` differs in this regard by offering
    some processing at the :class:`~mne_lsl.stream.StreamLSL` level and some at the
    :class:`~mne_lsl.stream.EpochsStream` level. For instance, filters are applied
    to a :class:`~mne_lsl.stream.StreamLSL` object while baseline correction is
    applied to a :class:`~mne_lsl.stream.EpochsStream` object.

1. Select which events are new since the last acquisition and which events are retained.
   For instance, an event too close to the end of the buffer is discarded for now since
   it is not possible to cut an entire epoch from it. This event will be acquired and
   added to the buffer as soon as it will be possible to cut an entire epoch from it.
2. Process the newly acquired data array of shape ``(n_epochs, n_samples, n_channels)``.

   a. Apply PTP and flatness rejection defined by the arguments ``reject``, ``flat``,
      ``reject_tmin`` and ``reject_tmax``.
   b. Apply baseline correction defined by the arguments ``baseline``, ``tmin`` and
      ``tmax``.
   c. Apply detrending defined by the argument ``detrend``.

.. image:: ../_static/resources/epochs-processing.svg
    :align: right
    :alt: Stream processing flowchart
    :width: 100%
