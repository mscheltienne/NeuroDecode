"""
Stream timestamps
=================

.. include:: ./../../links.inc

An LSL stream is composed of samples received at a given time. Each device, each source,
advertises its own time. If the source and the client are on the same physical computer,
e.g. with a :class:`mne_lsl.lsl.StreamOutlet` and a :class:`mne_lsl.lsl.StreamInlet`,
the same clock is used. But if the source and the client are on different computers,
e.g. connected on a local ethernet network, the delay between the source and the client
might be important.
"""

# %%
# Estimate the delay
# ------------------
#
# At a low-level, a :class:`~mne_lsl.lsl.StreamInlet` has a
# :meth:`~mne_lsl.lsl.StreamInlet.time_correction` method to estimate the time offset.
#
# .. note::
#
#     For this tutorial purposes, a mock LSL stream is created using a
#     :class:`~mne_lsl.player.PlayerLSL`. See
#     :ref:`sphx_glr_generated_tutorials_10_player.py` for additional information on
#     mock LSL streams.

import time

from matplotlib import pyplot as plt

from mne_lsl.datasets import sample
from mne_lsl.lsl import StreamInlet, resolve_streams
from mne_lsl.player import PlayerLSL as Player
from mne_lsl.stream import StreamLSL as Stream

fname = sample.data_path() / "sample-ant-raw.fif"
player = Player(fname)
player.start()

streams = resolve_streams(name=player.name)
inlet = StreamInlet(streams[0])
inlet.open_stream()
print(inlet.time_correction())
del inlet

# %%
# With the example above, the time offset is very small because the source
# (:class:`~mne_lsl.player.PlayerLSL`) and the client
# (:class:`~mne_lsl.lsl.StreamInlet`) are both local, i.e. present on the same computer.

# %%
# Timestamps in the Stream API
# ----------------------------
#
# A :class:`~mne_lsl.stream.StreamLSL` returns both the samples and the associated
# timestamps when queried with :meth:`~mne_lsl.stream.StreamLSL.get_data`.

stream = Stream(2, name=player.name)
stream.connect()
time.sleep(2)
data, ts = stream.get_data(picks="ECG")
f, ax = plt.subplots(1, 1, figsize=(10, 5), constrained_layout=True)
ax.plot(ts, data[0, :])
ax.set_ylabel("ECG")
ax.set_xlabel("Timestamps LSL")

# %%
# TODO: Add a stream from XDF file with jitter and add the processing flags.

# %%
# Free resources
# --------------
# When you are done with a :class:`~mne_lsl.player.PlayerLSL` or
# :class:`~mne_lsl.stream.StreamLSL`, don't forget to free the resources they both use
# to continuously mock an LSL stream or receive new data from an LSL stream.

stream.disconnect()
player.stop()
