"""
Introduction to real-time LSL streams
=====================================

.. include:: ./../../links.inc

.. _SSP projectors: https://mne.tools/dev/documentation/implementation.html#signal-space-projection-ssp

LSL is an open-source networked middleware ecosystem to stream, receive, synchronize,
and record neural, physiological, and behavioral data streams acquired from diverse
sensor hardware. It reduces complexity and barriers to entry for researchers, sensor
manufacturers, and users through a simple, interoperable, standardized API to connect
data consumers to data producers while abstracting obstacles such as platform
differences, stream discovery, synchronization and fault-tolerance.
Source: `LabStreamingLayer website <lsl_>`_.

In real-time applications, a server emits a data stream, and one or more clients connect
to the server to receive this data. In LSL terminology, the server is referred to as a
:class:`~mne_lsl.lsl.StreamOutlet`, while the client is referred to as a
:class:`~mne_lsl.lsl.StreamInlet`. The power of LSL resides in its ability to facilitate
interoperability and synchronization among streams. Clients have the capability to
connect to multiple servers, which may be running on the same or different computers
(and therefore different platforms/operating systems), and synchronize the streams
originating from these various servers.

MNE-LSL enhances the LSL API by offering a high-level interface akin to the
`MNE-Python <mne stable_>`_ API. While this tutorial concentrates on the high-level API,
detailed coverage of the low-level LSL API is provided in
:ref:`this separate tutorial <tut-low-level-api>`.

Concepts
--------

In essence, a real-time LSL stream can be envisioned as a perpetual recording, akin to
a :class:`mne.io.Raw` instance, characterized by an indeterminate length and providing
access solely to current and preceding samples. In memory, it can be depicted as a ring
buffer, also known as a circular buffer, a data structure employing a single, unchanging
buffer size, seemingly interconnected end-to-end.

.. image:: ../../_static/tutorials/circular-buffer-light.png
    :align: center
    :class: only-light

.. image:: ../../_static/tutorials/circular-buffer-dark.png
    :align: center
    :class: only-dark

Within a ring buffer, there are two pivotal pointers:

* The "head" pointer, also referred to as "start" or "read," indicates the subsequent
  data block available for reading.
* The "tail" pointer, known as "end" or "write," designates the forthcoming data block
  to be replaced with fresh data.

In a ring buffer configuration, when the "tail" pointer aligns with the "head" pointer,
data is overwritten before it can be accessed. Conversely, the "head" pointer cannot
surpass the "tail" pointer; it will always lag at least one sample behind. In all cases,
it falls upon the user to routinely inspect and fetch samples from the ring buffer,
thereby advancing the "head" pointer.

Within MNE-LSL, the :class:`~mne_lsl.stream.StreamLSL` object manages a ring buffer
internally, which is continuously refreshed with new samples. Notably, the two pointers
are concealed, with the head pointer being automatically adjusted to the latest received
sample. Given the preference for accessing the most recent information in neural,
physiological, and behavioral real-time applications, this operational approach
streamlines interaction with LSL streams and mitigates the risk of users accessing
outdated data.

Mocking an LSL stream
---------------------

To build real-time applications or showcase their functionalities, such as in this
tutorial, it's essential to generate simulated LSL streams. This involves creating a
:class:~mne_lsl.lsl.StreamOutlet and regularly sending data through it.

Within MNE-LSL, the :class:`~mne_lsl.player.PlayerLSL` generates a simulated LSL stream
utilizing data from a :class:`mne.io.Raw` file or object. This stream inherits its
description and channel specifications from the associated :class:`~mne.Info`. This
information encompasses channel properties, channel locations, filters, digitization,
and `SSP projectors`_. The :class:~mne_lsl.player.PlayerLSL subsequently publishes data
at regular intervals and seamlessly loops back to the starting point once the end of the
file is reached.
"""

import time

from matplotlib import pyplot as plt
from mne import set_log_level

from mne_lsl.datasets import sample
from mne_lsl.player import PlayerLSL as Player
from mne_lsl.stream import StreamLSL as Stream

set_log_level("WARNING")

# %%

fname = sample.data_path() / "sample-ant-raw.fif"
player = Player(fname).start()
player.info

# %%
# Once the :meth:`~mne_lsl.player.PlayerLSL.start` is called, data is published at
# regular intervals. The interval duration depends on the sampling rate and on the
# number of samples pushed at once, defined by the ``chunk_size`` argument of the
# :class:`~mne_lsl.player.PlayerLSL` object.
#
# .. note::
#
#     The default setting for chunk_size is ``64``, which helps prevent overly frequent
#     data transmission and minimizes CPU utilization. Nonetheless, in real-time
#     applications, there may be advantages to employing smaller chunk sizes for data
#     publication.

sfreq = player.info["sfreq"]
chunk_size = player.chunk_size
interval = chunk_size / sfreq  # in seconds
print(f"Interval between 2 push operations: {interval} seconds.")

# %%
# A :class:`~mne_lsl.player.PlayerLSL` can also stream annotations attached to the
# :class:`mne.io.Raw` object. Annotations are streamed on a second irregularly sampled
# :class:`~mne_lsl.lsl.StreamOutlet`. See
# :ref:`this separate tutorial <tut-player-annotations>` for additional information.
#
# Subscribing to an LSL stream
# ----------------------------
#
# With the mock LSL stream operational in the background, we can proceed to subscribe to
# this stream and access both its description and the data stored within its buffer. The
# :class:`~mne_lsl.stream.StreamLSL` object operates both the underlying
# :class:`~mne_lsl.lsl.StreamInlet` and the ring buffer, which size must be
# explicitly set upon creation.
#
# .. note::
#
#     A :class:`~mne_lsl.stream.StreamLSL` can connect to a single LSL stream. Thus, if
#     multiple LSL stream are present on the network, it's crucial to uniquely identify
#     a specific LSL stream using the ``name``, ``stype``, and ``source_id`` arguments
#     of the :class:`~mne_lsl.stream.StreamLSL` object.
#
# The stream description is automatically parsed into an :class:`mne.Info` upon
# connection with the method :meth:`mne_lsl.stream.StreamLSL.connect`.

stream = Stream(bufsize=2).connect()
stream.info

# %%
# Interaction with a :class:`~mne_lsl.stream.StreamLSL` is similar to the interaction
# with a :class:`mne.io.Raw`. In this example, the stream is mocked from a 64 channels
# EEG recording with an ANT Neuro amplifier. It includes 63 EEG, 2 EOG, 1 ECG, 1 EDA, 1
# STIM channel, and uses CPz as reference.

ch_types = stream.get_channel_types(unique=True)
print(f"Channel types included: {', '.join(ch_types)}")

# %%
# Operations such as channel selection, re-referencing, and filtering are performed
# directly on the ring buffer. For instance, we can select the EEG channels, add the
# missing reference channel and re-reference using a common average referencing scheme
# which will reduce the ring buffer to 64 channels.
#
# .. note::
#
#     By design, once a re-referencing operation is performed or if at least one filter
#     is applied, it is not possible anymore to select a subset of channels with the
#     methods :meth:`~mne_lsl.stream.StreamLSL.pick` or
#     :meth:`~mne_lsl.stream.StreamLSL.drop_channels`. Note that the re-referencing is
#     not reversible while filters can be removed with the method
#     :meth:`~mne_lsl.stream.StreamLSL.del_filter`.

stream.pick("eeg")  # channel selection
assert "CPz" not in stream.ch_names  # reference absent from the data stream
stream.add_reference_channels("CPz")
stream.set_eeg_reference("average")
stream.info

# %%
# .. note::
#
#     As for MNE-Python, methods can be chained, e.g.
#
#     .. code-block:: python
#
#         stream.pick("eeg").add_reference_channels("CPz")
#
# The ring buffer is accessed with the method :meth:`~mne_lsl.stream.StreamLSL.get_data`
# which returns both the samples and their associated timestamps. In LSL terminology, a
# sample is an array of shape (n_channels,).

picks = ("Fz", "Cz", "Oz")  # channel selection
f, ax = plt.subplots(3, 1, sharex=True, constrained_layout=True)
for _ in range(3):  # acquire 3 separate window
    # figure how many new samples are available, in seconds
    winsize = stream.n_new_samples / stream.info["sfreq"]
    # retrieve and plot data
    data, ts = stream.get_data(winsize, picks=picks)
    for k, data_channel in enumerate(data):
        ax[k].plot(ts, data_channel)
    time.sleep(0.5)
for k, ch in enumerate(picks):
    ax[k].set_title(f"EEG {ch}")
ax[-1].set_xlabel("Timestamp (LSL time)")
plt.show()

# %%
# .. warning::
#
#     Note that the first of the 3 chunks plotted is longer. This is because
#     execution of the channel selection and re-referencing operations took a finite
#     amount of time to complete while in the background, the
#     :class:`~mne_lsl.stream.StreamLSL` was still acquiring new samples. Note also that
#     :py:attr:`~mne_lsl.stream.StreamLSL.n_new_samples` is reset to 0 after each call
#     to :meth:`~mne_lsl.stream.StreamLSL.get_data`, but it is not reset if the "tail"
#     pointer overtakes the "head" pointer, in other words, it is not reset if the
#     number of new samples since the last :meth:`~mne_lsl.stream.StreamLSL.get_data`
#     call exceeds the buffer size.
#
# Free resources
# --------------
#
# When you are done with a :class:`~mne_lsl.player.PlayerLSL` or
# :class:`~mne_lsl.stream.StreamLSL`, don't forget to free the resources they both use
# to continuously mock an LSL stream or receive new data from an LSL stream.

stream.disconnect()

# %%

player.stop()
