"""
Introduction to the Player API
==============================

.. include:: ./../../links.inc

During the development of a project, it's very helpful to test on a mock LSL stream
replicating an experimental condition. The :class:`~mne_lsl.player.PlayerLSL` can create
a mock LSL stream from any `MNE <mne stable_>`_ readable file.

.. note::

    For now, the mock capabilities are restricted to streams with a continuous sampling
    rate. Streams with an irregular sampling rate corresponding to event streams are not
    yet supported.
"""

# %%
# Create a mock LSL Stream
# ------------------------
#
# A :class:`~mne_lsl.player.PlayerLSL` requires a valid path to an existing file which
# can be read by `MNE <mne stable_>`_. In this case, the sample data
# ``sample-ant-raw.fif`` recorded on an ANT Neuro 64 channel EEG amplifier.

import time

import numpy as np
from matplotlib import pyplot as plt
from mne import pick_types, set_log_level

from mne_lsl.datasets import sample
from mne_lsl.lsl import StreamInlet, resolve_streams
from mne_lsl.player import PlayerLSL as Player
from mne_lsl.stream import StreamLSL as Stream

set_log_level("WARNING")

fname = sample.data_path() / "sample-ant-raw.fif"
player = Player(fname)
player.start()

# %%
# Once started, a :class:`~mne_lsl.player.PlayerLSL` will continuously stream data from
# the file until stopped. If the end of file is reached, it will loop back to the
# beginning thus inducing a discontinuity in the signal.

streams = resolve_streams()
print(streams[0])

# %%
# You can connect to the stream as you would with any other LSL stream, e.g. with a
# :class:`mne_lsl.lsl.StreamInlet`:

inlet = StreamInlet(streams[0])
inlet.open_stream()
data, ts = inlet.pull_chunk()
print(data.shape)  # (n_samples, n_channels)
del inlet

# %%
# or with a :class:`mne_lsl.stream.StreamLSL`:

stream = Stream(bufsize=2, name=player.name)
stream.connect()
stream.info
time.sleep(1)
data, ts = stream.get_data(winsize=1)
print(data.shape)  # (n_channels, n_samples)

# %%

data, ts = stream.get_data(winsize=1, picks="ECG")
f, ax = plt.subplots(1, 1, constrained_layout=True)
ax.plot(ts, np.squeeze(data))
ax.set_title("ECG channel")
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Voltage (?)")
plt.show()

# %%
# Streaming unit
# --------------
#
# Note the lack of unit on the Y-axis  of the previous plot. By convention,
# `MNE-Python <mne stable_>`_ stores data in SI units, i.e. Volts for EEG, ECG, EOG, EMG
# channels.

data, ts = stream.get_data(winsize=1, picks="Fz")
f, ax = plt.subplots(1, 1, constrained_layout=True)
ax.plot(ts, np.squeeze(data))
ax.set_title("Fz (EEG) channel")
ax.set_xlabel("Time (seconds)")
ax.set_ylabel("Voltage (V)")
plt.show()

# %%
# But most systems do not stream in SI units as it can be inconvenient to work with very
# small floats. For instance, an ANT amplifier stream in microvolts. Thus, to replicate
# our experimental condition, the correct streaming unit must be set with
# :meth:`mne_lsl.player.PlayerLSL.set_channel_units`.
#
# .. note::
#
#     The methods impacting the measurement information (e.g. channel name, channel
#     units) can not be used on a stream which is started.

del stream
player.stop()
mapping = {
    player.ch_names[k]: "microvolts"
    for k in pick_types(player.info, eeg=True, eog=True, ecg=True)
}
player.set_channel_units(mapping)
player.start()

# %%

stream = Stream(bufsize=2, name=player.name)
stream.connect()
time.sleep(1)
data_rescale, ts_rescale = stream.get_data(winsize=1, picks="Fz")
f, ax = plt.subplots(2, 1, constrained_layout=True)
ax[0].plot(ts, np.squeeze(data))
ax[1].plot(ts_rescale, np.squeeze(data_rescale))
ax[0].set_title("Fz channel (window 1)")
ax[1].set_title("Fz channel (window 2)")
ax[0].set_ylabel("Voltage (V)")
ax[1].set_ylabel("Voltage (µV)")
ax[0].set_xlim(ts[0] - 1, ts_rescale[-1] + 1)
ax[1].set_xlim(ts[0] - 1, ts_rescale[-1] + 1)
plt.show()

# %%
#
# .. note::
#
#     The value range seems important for EEG channels, but the sample dataset is not
#     filtered. Thus, a large DC offset is present.
#
# The :class:`~mne_lsl.stream.StreamLSL` object will be able to interpret the channel
# unit and will report that the EEG, EOG, ECG channels are streamed in microvolts while
# the trigger channel is streamed in volts.

ecg_idx = pick_types(stream.info, ecg=True)[0]
stim_idx = pick_types(stream.info, stim=True)[0]
units = stream.get_channel_units()
print(
    f"ECG channel type: '{units[ecg_idx][0]}' (Volts)\n with the multiplication "
    f"factor {units[ecg_idx][1]} (1e-6, micro).\n"
)
print(
    f"Stim channel type: '{units[stim_idx][0]}' (Volts)\n with the multiplication "
    f"factor {units[stim_idx][1]} (1e0, none).\n"
)

# %%
# Context manager
# ---------------
#
# A :class:`~mne_lsl.player.PlayerLSL` can also be used as a context manager, to handle
# the :meth:`mne_lsl.player.PlayerLSL.start` and :meth:`mne_lsl.player.PlayerLSL.stop`.

del stream
player.stop()

with player:
    stream = Stream(bufsize=2)
    stream.connect()
    print(stream.info)
    stream.disconnect()
