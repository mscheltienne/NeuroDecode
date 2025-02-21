"""
Replaying a file in a separate process
======================================

With a :class:`~mne_lsl.player.PlayerLSL` object, you can replay an MNE-Python readable
file as a valid LSL stream. This is very useful for testing or debugging purposes. The
created LSL stream is managed in the main process, as a separate thread. Thus, if the
code running the main process is hogging all of the CPU resources, then the
:class:`~mne_lsl.player.PlayerLSL` object may not be able to keep up with the LSL stream
and to push (publish) new data when it should. This is why it is often useful to run the
:class:`~mne_lsl.player.PlayerLSL` object in a separate process.

Single process execution
------------------------

Let's start by demonstrating the issue with a single process where the main thread is
hogging all of the CPU resources, leaving almost nothing for the
:class:`~mne_lsl.player.PlayerLSL` thread to run and mock the LSL stream.
"""

# sphinx_gallery_thumbnail_path = '_static/tutorials/multiprocessing.png'

import multiprocessing as mp
import time

from mne.io import read_raw_fif

from mne_lsl.datasets import sample
from mne_lsl.player import PlayerLSL as Player


raw = read_raw_fif(sample.data_path() / "sample-ecg-raw.fif", preload=False)
raw.crop(0, 3).load_data()
player = Player(raw, chunk_size=200, n_repeat=1, name="example-process")
player

# %%
# .. note::
#
#     Note that we use a ``chunk_size`` of 200 samples which does replicate a real-time
#     scenario where the LSL stream is usually using finer granularity (specific to the
#     device and LSL stream application). However, this large chunk size provides
#     stability to the documentation build on our CIs.
#
# The smaller the chunk size, the more resources are needed by the
# :class:`~mne_lsl.player.PlayerLSL` object to keep up with the LSL stream. This is why
# with a chunk size of 200 samples, we don't observe a difference between a main thread
# giving time to the player to run (scenario 1, while loop with :func:`time.sleep` calls
# to create idle time) and a main thread hogging all of the CPU resources (scenario 2,
# while loop without any idle time).

# scenario 1: give time to the player to run
start = time.time()
player.start()
while player.running:
    time.sleep(0.5)
stop = time.time()
print(f"Elapsed time (free time): {stop - start:.2f} s")

# scenario 2: hog all of the CPU resources
start = time.time()
player.start()
while player.running:
    pass
stop = time.time()
print(f"Elapsed time (hogging): {stop - start:.2f} s")

# clean-up resources
del player

# %%
# If you run the code above with a ``chunk_size`` of 10 samples, or of 1 sample, you
# will observe the following difference in elapsed time:
#
# - chunk size of 10 samples:
#
#   - 3.5 seconds for scenario 1 (due to one extra sleep call)
#   - 7.4 seconds for scenario 2
#
# - chunk size of 1 sample:
#
#   - 3.5 seconds for scenario 1 (due to one extra sleep call)
#   - 68.8 seconds for scenario 2
#
# Multi-process execution
# -----------------------
#
# To avoid this problem, we can run the :class:`~mne_lsl.player.PlayerLSL` object in a
# separate process. This way, the main process can hog all of the CPU resources without
# affecting the player process.
#
# This can be achieved in the following ways:
#
# - use the command-line entry point to run the player in a separate terminal
#
#   .. code-block:: bash
#
#       $ mne_lsl_player sample-ecg-raw.fif --chunk-size 1 --n-repeat 1
#
# - use the python API to run the player in a separate python interpreter
# - use the python API and the ``multiprocessing`` module to run the player in a
#   separate process
#
# Here, we demonstrate the last option.
#
# .. note::
#
#     On Windows, the ``process`` creation and execurtion must be protected behind an
#     ``if __name__ == "__main__":`` block. This is not necessary on Unix systems, on
#     which this documentation is built.


def player_process(raw):
    """Process which runs the player."""
    from mne_lsl.player import PlayerLSL

    player = PlayerLSL(raw, chunk_size=200, n_repeat=1, name="example-process-2")
    player.start()
    while player.running:
        pass


process = mp.Process(target=player_process, args=(raw,))
process.start()
print("Player started in a separate process!")
process.join()

# %%
# This is still a bit too simplistic. The process takes time to actually start, thus
# when the print is emitted, the player has not yet started. To fix this, we can use a
# shared variable to signal when the player has started. This shared variable can also
# be used to interrupt the player process from the main process.


def player_process(raw, status):
    """Process which runs the process."""
    from mne_lsl.player import PlayerLSL

    player = PlayerLSL(raw, chunk_size=200, name="example-process-3")
    player.start()
    status.value = 1
    while status.value:
        pass
    player.stop()


manager = mp.Manager()
# integer value, used to store 0 or 1 to turn off the player
status = manager.Value("i", 0)
process = mp.Process(target=player_process, args=(raw, status))
process.start()
while status.value != 1:
    pass  # wait for the player to actually start
print("Player started in a separate process!")
status.value = 0  # stops the player
process.join()
