"""
Epoching a Stream in real-time
==============================

.. include:: ./../../links.inc

The :class:`~mne_lsl.stream.EpochsStream` object can be used similarly to
:class:`mne.Epochs` to create epochs from a continuous stream of samples around events
of interest.

.. note::

    The :class:`~mne_lsl.stream.EpochsStream` object is designed to work with
    any ``Stream`` object. At the time of writing, only
    :class:`~mne_lsl.stream.StreamLSL` is available, but any object inheriting from the
    abstract :class:`~mne_lsl.stream.BaseStream` object should work.

A :class:`~mne_lsl.stream.EpochsStream` object support peak-to-peak rejection, baseline
correction and detrending.

Event source
------------

A :class:`~mne_lsl.stream.EpochsStream` object requires an event source to create
epochs. 3 event sources are supported:

- a set of ``'stim'`` channels within the attached ``Stream`` object.
- a set of ``'stim'`` channels within a separate ``Stream`` object.
- an irregularly sampled ``Stream`` object.

.. note::

    In the case of an irregularly sampled ``Stream`` object, only numerical streams are
    supported at the moment because interaction with ``str`` streams in Python is not
    as performant as interaction with numerical streams.

Set of ``'stim'`` channels
--------------------------

The set of ``'stim'`` channels from which the events are extracted can be either part
of the regularly sampled ``Stream`` object epoched (argument ``stream``) or part of a
separate regularly sampled ``Stream`` object (argument ``event_stream``). In both case,
the channel(s) type should be ``'stim'`` and the channel(s) should be formatted for
:func:`mne.find_events` to correctly extract the events. The channels to consider are
provided in the argument ``event_channels`` and the events to consider in the argument
``event_id``. Let's create epochs around the event ID ``2`` from the ``'STI 014'``
channel of MNE's sample dataset.
"""

import time
import uuid

import numpy as np
from matplotlib import pyplot as plt
from mne import Epochs, EpochsArray, annotations_from_events, find_events
from mne.io import read_raw_fif

from mne_lsl.datasets import sample
from mne_lsl.lsl import resolve_streams
from mne_lsl.player import PlayerLSL
from mne_lsl.stream import EpochsStream, StreamLSL

fname = sample.data_path() / "mne-sample" / "sample_audvis_raw.fif"
raw = read_raw_fif(fname, preload=False).pick(("meg", "stim")).load_data()
source_id = uuid.uuid4().hex
player = PlayerLSL(
    raw,
    chunk_size=200,
    name="tutorial-epochs-1",
    source_id=source_id,
    annotations=False,
).start()
player.info

# %%
# .. note::
#
#     A ``chunk_size`` of 200 samples is used here to ensure stability and reliability
#     while building the documentation on the CI. In practice, a ``chunk_size`` of 200
#     samples is too large to represent a real-time application.
#
# In the cell above, a mock LSL stream is created using the ``'meg'`` and ``'stim'``
# channels of MNE's sample dataset. Now, we need to create a
# :class:`~mne_lsl.stream.StreamLSL` object connected to this mock LSL stream. The
# channel ``"MEG 2443"`` is marked as bad and the signal is filtered with a low-pass
# filter.

stream = StreamLSL(bufsize=4, name="tutorial-epochs-1", source_id=source_id)
stream.connect(acquisition_delay=0.1, processing_flags="all")
stream.info["bads"] = ["MEG 2443"]  # remove bad channel
stream.filter(None, 40, picks="grad")  # filter signal
stream.info

# %%
# Now, we can create epochs using this stream as source for both the epochs and the
# events. The ``'stim'`` channel ``'STI 014'`` is used to extract the events and epochs
# are created around the event ID ``2`` using the gradiometer channels. The epochs are
# created around the event, from 200 ms before the event to 500 ms after the event. A
# baseline correction is applied using the 200 first ms of the epoch as baseline.

epochs = EpochsStream(
    stream,
    bufsize=20,  # number of epoch held in the buffer
    event_id=2,
    event_channels="STI 014",
    tmin=-0.2,
    tmax=0.5,
    baseline=(None, 0),
    picks="grad",
).connect(acquisition_delay=0.1)
epochs.info

# %%
# Note the ``bufsize`` argument in the cell above. This argument controls the number of
# epochs that are kept in memory. The actual size of the underlying numpy array depends
# on the number of epochs, the number of samples (controlled by ``tmin`` and ``tmax``)
# and the number of channels.
#
# Let's wait for a couple of epochs to enter in the buffer, and then let's convert the
# array to an MNE-Python :class:`~mne.Epochs` object and plot the evoked response.

while epochs.n_new_epochs < 10:
    time.sleep(0.5)

data = epochs.get_data(n_epochs=epochs.n_new_epochs)
epochs_mne = EpochsArray(data, epochs.info, verbose="WARNING")
epochs_mne.average().plot()
plt.show()

# %%

epochs.disconnect()
stream.disconnect()
player.stop()

# %%
# Irregularly sampled stream
# --------------------------
#
# The event source can also be an irregularly sampled stream. In this case, each channel
# represents a separate event. A new value entering the buffer of a channel is
# interpreted as an event, regardless of the value itself. For instance, we can fake
# an irregularly sampled numerical stream using a :class:`~mne_lsl.player.PlayerLSL`
# with a :class:`~mne.io.Raw` object which has :class:`~mne.Annotations` attached to it.

events = find_events(raw, stim_channel="STI 014")
events = events[np.isin(events[:, 2], (1, 2))]  # keep only events with ID 1 and 2
annotations = annotations_from_events(
    events,
    raw.info["sfreq"],
    event_desc={1: "ignore", 2: "event"},
    first_samp=raw.first_samp,
)
annotations.duration += 0.1  # set duration since annotations_from_events sets it to 0
annotations

# %%

raw.set_annotations(annotations)
player = PlayerLSL(
    raw, chunk_size=200, name="tutorial-epochs-2", source_id=source_id, annotations=True
).start()
player.info

# %%
# We now have 2 LSL stream availables on the network, one of which is an irregularly
# sampled numerical streams of events.

resolve_streams()

# %%
# We can now create a :class:`~mne_lsl.stream.StreamLSL` object for each available
# stream on the network.

stream = StreamLSL(bufsize=4, name="tutorial-epochs-2", source_id=source_id)
stream.connect(acquisition_delay=0.1, processing_flags="all")
stream.info["bads"] = ["MEG 2443"]  # remove bad channel
stream.filter(None, 40, picks="grad")  # filter signal
stream.info

# %%

stream_events = StreamLSL(
    bufsize=20, name="tutorial-epochs-2-annotations", source_id=source_id
)
stream_events.connect(acquisition_delay=0.1, processing_flags="all")
stream_events.info

# %%
# Let's first inspect the event stream once a couple of samples have been acquired.

while stream_events.n_new_samples < 3:
    time.sleep(0.5)
data, ts = stream_events.get_data(winsize=stream_events.n_new_samples)
print("Array of shape (n_channels, n_samples): ", data.shape)
data

# %%
# Each channel corresponds to a given annotation, ``0`` to ``'ignore'`` and ``1`` to
# ``'event'``. The value is ``0`` when no annotation is present, and ``x`` when an
# annotation is present, with ``x`` being the duration of the annotation.
#
# Thus, this array can be interpreted as follows:
#
# .. code-block:: python
#
#      array([[0.1, 0. , 0.1],
#            [0. , 0.1, 0. ]])
#
# - An annotation of 0.1 seconds labelled ``'ignore'`` was received at ``ts[0]``.
# - An annotation of 0.1 seconds labelled ``'event'`` was received at ``ts[1]``.
# - An annotation of 0.1 seconds labelled ``'ignore'`` was received at ``ts[2]``.
#
# We can now use those 2 streams to create epochs around the events of interest.

epochs = EpochsStream(
    stream,
    bufsize=20,  # number of epoch held in the buffer
    event_id=None,
    event_channels="event",  # this argument now selects the events of interest
    event_stream=stream_events,
    tmin=-0.2,
    tmax=0.5,
    baseline=(None, 0),
    picks="grad",
).connect(acquisition_delay=0.1)
epochs.info

# %%
# Let's wait for a couple of epochs to enter in the buffer, and then let's convert the
# array to an MNE-Python :class:`~mne.Epochs` object and plot the time-frequency
# representation of the evoked response.

while epochs.n_new_epochs < 10:
    time.sleep(0.5)

data = epochs.get_data(n_epochs=epochs.n_new_epochs)
epochs_mne = EpochsArray(data, epochs.info, tmin=-0.2, verbose="WARNING")
freqs = np.arange(1, 10)
tfr = epochs_mne.average().compute_tfr(
    method="multitaper", freqs=freqs, n_cycles=freqs / 2
)
tfr.plot(baseline=(None, 0), combine="mean")
plt.show()

# %%
# Let's compare this to a :class:`~mne.Epochs` object created from the same number of
# events offline.
#
# .. note::
#
#     The same epochs were not selected between the offline and online processing.

epochs_offline = Epochs(
    raw, events, event_id=dict(event=2), baseline=(None, 0), picks="grad", preload=True
)
epochs_offline.filter(None, 40)
tfr = epochs_offline.average().compute_tfr(
    method="multitaper", freqs=freqs, n_cycles=freqs / 2
)
tfr.plot(baseline=(None, 0), combine="mean")
plt.show()

# %%
# Finally, in this case a single event was kept in the
# :class:`~mne_lsl.stream.EpochsStream`, but if more events are retained, it is
# important to know which one is which. This information is stored in the property
# :attr:`~mne_lsl.stream.EpochsStream.events` of the
# :class:`~mne_lsl.stream.EpochsStream`, which is an internal buffer of the event codes.

epochs.events

# %%
# .. note::
#
#     In the case of an irregularly sampled event stream, the event code represents the
#     channel idx within the event stream.
#
# Free resources
# --------------
#
# When you are done with a :class:`~mne_lsl.player.PlayerLSL`, a
# :class:`~mne_lsl.stream.StreamLSL` or a :class:`~mne_lsl.stream.EpochsStream` don't
# forget to free the resources they use to continuously mock an LSL stream or
# receive new data from an LSL stream.

epochs.disconnect()

# %%

stream.disconnect()

# %%

player.stop()
