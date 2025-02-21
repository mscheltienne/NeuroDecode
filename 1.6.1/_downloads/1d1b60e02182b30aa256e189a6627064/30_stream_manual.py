"""
Automatic vs Manual acquisition
===============================

.. include:: ./../../links.inc

The :class:`~mne_lsl.stream.StreamLSL` object offers 2 mode of acquisition: automatic or
manual. In automatic mode, the stream object acquires new chunks of samples at a
regular interval. In manual mode, the user has to call the
:meth:`~mne_lsl.stream.StreamLSL.acquire` to acquire new chunks of samples from the
network. The automatic or manual acquisition is selected via the ``acquisition_delay``
argument of :meth:`~mne_lsl.stream.StreamLSL.connect`:

- a non-zero positive integer value will set the acquisition to automatic mode with the
  specified delay in seconds.
- ``0`` will set the acquisition to manual mode.

Automatic acquisition
---------------------

When the stream is set to automatically acquire new samples at a regular interval, a
background thread is created with :class:`concurrent.futures.ThreadPoolExecutor`. The
background thread is periodically receives a job to acquire new samples from the
network.

.. important::

    If the main thread is hogging all of the CPU resources, the delay between two
    acquisition job might be longer than the specified delay. The background thread
    will always do its best to acquire new samples at the specified delay, but it is not
    able to do so if the CPU is busy.
"""

import uuid
from time import sleep

from matplotlib import pyplot as plt

from mne_lsl.datasets import sample
from mne_lsl.player import PlayerLSL
from mne_lsl.stream import StreamLSL

# create a mock LSL stream for this tutorial
fname = sample.data_path() / "sample-ant-raw.fif"
source_id = uuid.uuid4().hex
player = PlayerLSL(fname, chunk_size=200, source_id=source_id).start()
player.info

# %%
# .. note::
#
#     A ``chunk_size`` of 200 samples is used here to ensure stability and reliability
#     while building the documentation on the CI. In practice, a ``chunk_size`` of 200
#     samples is too large to represent a real-time application.

stream = StreamLSL(bufsize=2, source_id=source_id).connect(acquisition_delay=0.1)
sleep(2)  # wait for new samples
print(f"New samples acquired: {stream.n_new_samples}")
stream.disconnect()

# %%
# Manual acquisition
# -------------------
#
# In manual acquisition mode, the user has to call the
# :meth:`~mne_lsl.stream.StreamLSL.acquire` to get new samples from the network. In this
# mode, all operation happens in the main thread and the user has full control over when
# to acquire new samples.

stream = StreamLSL(bufsize=2, source_id=source_id).connect(acquisition_delay=0)
sleep(2)  # wait for new samples
print(f"New samples acquired (before stream.acquire()): {stream.n_new_samples}")
stream.acquire()
print(f"New samples acquired (after stream.acquire()): {stream.n_new_samples}")

# %%
# However, it is also now up to the user to make sure he acquires new samples regularly
# and does not miss part of the stream. The created :class:`~mne_lsl.lsl.StreamInlet`
# has its buffer set to the same value as the :class:`~mne_lsl.stream.StreamLSL` object.

stream.acquire()
data1, ts1 = stream.get_data(picks="Cz")
sleep(4)  # wait for 2 buffers
stream.acquire()
data2, ts2 = stream.get_data(picks="Cz")

f, ax = plt.subplots(1, 1, layout="constrained")
ax.plot(ts1 - ts1[0], data1.squeeze(), color="blue", label="acq 1")
ax.plot(ts2 - ts1[0], data2.squeeze(), color="red", label="acq 2")
ax.legend()
ax.set_xlabel("Time (s)")
ax.set_ylabel("EEG amplitude")
plt.show()

# %%
# Free resources
# --------------
#
# When you are done with a :class:`~mne_lsl.player.PlayerLSL` or
# :class:`~mne_lsl.stream.StreamLSL`, don't forget to free the resources they both use
# to continuously mock an LSL stream or receive new data from an LSL stream.

stream.disconnect()

# %%

player.stop()
