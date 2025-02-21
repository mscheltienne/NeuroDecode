"""
.. _tut-low-level-api:

Low-level LSL API
=================

.. include:: ./../../links.inc

.. _lsl language bindings: https://github.com/sccn/labstreaminglayer/tree/master/LSL

LSL is a library designed for streaming time series data across different platforms and
programming languages. The `core library <lsl lib_>`_ is primarily written in C++, and
bindings are accessible for Python, C#, Java, MATLAB, and Unity, among others. You can
find a comprehensive list `here <lsl language bindings_>`_.

MNE-LSL provides a reimplementation of the `python binding <lsl python_>`_, known as
``pylsl``, within the ``mne_lsl.lsl`` module. It introduces additional functionalities
to simplify the low-level interaction with LSL streams. Moreover, it enhances the
detection of liblsl on your system and can retrieve a compatible version online if
necessary. The differences between ``pylsl`` and ``mne_lsl.lsl`` are detailed
:ref:`here<resources/pylsl:Differences with pylsl>`.
"""

# sphinx_gallery_thumbnail_path = '_static/tutorials/lsl.png'

import time
import uuid

import numpy as np

from mne_lsl.lsl import (
    StreamInfo,
    StreamInlet,
    StreamOutlet,
    local_clock,
    resolve_streams,
)

# %%
# Creating a stream
# -----------------
#
# To create a stream, you must first define its properties. This is achieved by creating
# a :class:`~mne_lsl.lsl.StreamInfo` object, which specifies the stream's name, type,
# source and properties. Convenience methods are available to set the channel
# properties, including :meth:`~mne_lsl.lsl.StreamInfo.set_channel_info`, which uses a
# :class:`mne.Info` object as source.

sinfo = StreamInfo(
    name="my-stream",
    stype="eeg",
    n_channels=3,
    sfreq=1024,
    dtype="float32",
    source_id=uuid.uuid4().hex,
)
sinfo.set_channel_names(["Fz", "Cz", "Oz"])
sinfo.set_channel_types("eeg")
sinfo.set_channel_units("microvolts")

# %%
# Once the :class:`~mne_lsl.lsl.StreamInfo` object is created, a
# :class:`~mne_lsl.lsl.StreamOutlet` can be instantiated to create the stream.

outlet = StreamOutlet(sinfo)

# %%
# Discover streams
# ----------------
#
# At this point, the :class:`~mne_lsl.lsl.StreamOutlet` is available on the network. The
# function :func:`~mne_lsl.lsl.resolve_streams` discovers all available streams on the
# network. This operation is commonly named the stream resolution.
#
# .. note::
#
#     The stream resolution can be restricted by providing the ``name``, ``stype``, and
#     ``source_id`` arguments.

streams = resolve_streams()
assert len(streams) == 1
streams[0]

# %%
# The resolution retrieves only the stream basic properties. The channel properties,
# stored in the stream description in an XML element tree, are absent from a
# :class:`~mne_lsl.lsl.StreamInfo` returned by the resolution function.

assert streams[0].get_channel_names() is None

# %%
# Connect to a Stream
# -------------------
#
# To connect to a stream, a :class:`~mne_lsl.lsl.StreamInlet` object must be created
# using the resolved :class:`~mne_lsl.lsl.StreamInfo`. Once the stream is opened with
# :meth:`~mne_lsl.lsl.StreamInlet.open_stream`, the connection is established and
# both the properties and data become available.

inlet = StreamInlet(streams[0])
inlet.open_stream()
sinfo = inlet.get_sinfo()  # retrieve stream information with all properties

# %%

sinfo.get_channel_names()

# %%

sinfo.get_channel_types()

# %%

sinfo.get_channel_units()

# %%
# An :class:`mne.Info` can be obtained directly with
# :meth:`~mne_lsl.lsl.StreamInfo.get_channel_info`. If the information contained in the
# XML element tree can not be parsed, default values are used. For instance, the channel
# names are replaced by the channel numbers similarly to :func:`mne.create_info`.

sinfo.get_channel_info()

# %%
# Push/Pull operations
# --------------------
#
# For new data to be received, it first need to be pushed on the
# :class:`~mne_lsl.lsl.StreamOutlet`. 2 methods are available:
#
# * :meth:`~mne_lsl.lsl.StreamOutlet.push_sample` to push an individual sample of shape
#   (n_channels,)
# * :meth:`~mne_lsl.lsl.StreamOutlet.push_chunk` to push a chunk of samples of shape
#   (n_samples, n_channels)

outlet.push_sample(np.array([1, 2, 3]))

# %%
# Once pushed, samples become available at the client end. 2 methods are available to
# retrieve samples:
#
# * :meth:`~mne_lsl.lsl.StreamInlet.pull_sample` to pull an individual sample of shape
#   (n_channels,)
# * :meth:`~mne_lsl.lsl.StreamInlet.pull_chunk` to pull a chunk of samples of shape
#   (n_samples, n_channels)

# give a bit of time to the documentation build after the execution of the last cell
time.sleep(0.01)
assert inlet.samples_available == 1
data, ts = inlet.pull_sample()
assert inlet.samples_available == 0
data

# %%
# LSL clock
# ---------
#
# The local system timestamp is retrieved with :func:`~mne_lsl.lsl.local_clock`. This
# local timestamp can be compared with the LSL timestamp from acquired data.

now = local_clock()
print(f"Timestamp of the acquired data: {ts}")
print(f"Current time: {now}")
print(f"Delta: {now - ts} seconds")

# %%
# Free resources
# --------------
#
# When you are done with a :class:`~mne_lsl.lsl.StreamInlet` or
# :class:`~mne_lsl.lsl.StreamOutlet`, don't forget to free the resources they both use.

inlet.close_stream()
del inlet
del outlet
