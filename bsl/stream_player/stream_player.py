import time
from pathlib import Path
import multiprocessing as mp

import mne
import pylsl
import numpy as np

from .. import logger
from ..triggers import TriggerDef
from ..utils import find_event_channel
from ..utils._docs import fill_doc


@fill_doc
class StreamPlayer:
    """
    Class for playing a recorded file on LSL network in another process.

    Parameters
    ----------
    %(player_stream_name)s
    %(player_fif_file)s
    %(player_repeat)s
    %(trigger_file)s  # TODO change doc.
    %(player_chunk_size)s
    %(player_high_resolution)s
    """

    def __init__(self, stream_name, fif_file, repeat=float('inf'),
                 trigger_def=None, chunk_size=16, high_resolution=False):
        self._stream_name = str(stream_name)
        self._fif_file = StreamPlayer._check_fif_file(fif_file)
        self._repeat = StreamPlayer._check_repeat(repeat)
        self._trigger_def = StreamPlayer._check_trigger_def(trigger_def)
        self._chunk_size = StreamPlayer._check_chunk_size(chunk_size)
        self._high_resolution = bool(high_resolution)

        self._process = None
        self._state = mp.Value('i', 0)

    def start(self, blocking=True):
        """
        Start streaming data on LSL network in a new process.

        Parameters
        ----------
        blocking : `bool`
            If ``True``, waits for the child process to start streaming data.
        """
        raw = mne.io.read_raw_fif(self._fif_file, preload=True, verbose=False)

        logger.info('Streaming started.')
        self._process = mp.Process(
            target=self._stream,
            args=(self._stream_name, raw, self._repeat,
                  self._trigger_def, self._chunk_size, self._high_resolution,
                  self._state))
        self._process.start()

        if blocking:
            while self._state.value == 0:
                pass

    def stop(self):
        """
        Stop the streaming, by terminating the process.
        """
        if self._process is None:
            logger.warning('StreamPlayer was not started. Skipping.')
            return

        with self._state.get_lock():
            self._state.value = 0

        logger.info('Waiting for StreamPlayer %s process to finish.',
                    self._stream_name)
        self._process.join(10)

        if self._process.is_alive():
            logger.error('StreamPlayer process not finishing.. killing.')
            self._process.kill()

        self._process = None

    def _stream(self, stream_name, raw, repeat, trigger_def, chunk_size,
                high_resolution, state):
        """
        The function called in the new process.
        Instance a _Streamer and start streaming.
        """
        streamer = _Streamer(
            stream_name, raw, repeat, trigger_def, chunk_size,
            high_resolution, state)
        streamer.stream()

    # --------------------------------------------------------------------
    @staticmethod
    def _check_fif_file(fif_file):
        """
        Check if the provided fif_file is valid.
        """
        try:
            fif_file = Path(fif_file)
            mne.io.read_raw_fif(fif_file, preload=False, verbose=None)
            return fif_file
        except Exception:
            raise ValueError(
                'Argument fif_file must be a path to a valid MNE raw file. '
                'Provided: %s.', fif_file)

    @staticmethod
    def _check_repeat(repeat):
        """
        Checks that repeat is either infinity or a strictly positive integer.
        """
        if repeat == float('inf'):
            return repeat
        elif isinstance(repeat, (int, float)):
            repeat = int(repeat)
            if 0 < repeat:
                return repeat
            else:
                logger.error(
                    'Argument repeat must be a strictly positive integer. '
                    'Provided: %s -> Changing to +inf.', repeat)
                return float('inf')
        else:
            logger.error(
                'Argument repeat must be a strictly positive integer. '
                'Provided: %s -> Changing to +inf.', repeat)
            return float('inf')

    @staticmethod
    def _check_trigger_def(trigger_def):
        """
        Checks that the trigger file is either a path to a valid trigger
        definition file, in which case it is loader and pass as a TriggerDef,
        or a TriggerDef instance. Else sets it as None.
        """
        if trigger_def is None:
            return trigger_def
        elif isinstance(trigger_def, TriggerDef):
            return trigger_def
        elif isinstance(trigger_def, (str, Path)):
            trigger_def = Path(trigger_def)
            if not trigger_def.exists():
                logger.error(
                    'Argument trigger_def is a path that does not exist. '
                    'Provided: %s -> Ignoring.', trigger_def)
                return None
            trigger_def = TriggerDef(trigger_def)
            return trigger_def
        else:
            logger.error(
                'Argument trigger_def must be a TriggerDef instance or a path '
                'to a trigger definition ini file. '
                'Provided: %s -> Ignoring.', type(trigger_def))
            return None

    @staticmethod
    def _check_chunk_size(chunk_size):
        """
        Checks that chunk_size is a strictly positive integer.
        """
        if isinstance(chunk_size, (int, float)):
            try:
                chunk_size = int(chunk_size)
            except OverflowError:
                logger.error(
                    'Argument chunk_size must be a strictly positive integer. '
                    'Provided: %s -> Changing to 16.', chunk_size)
                return 16
            if chunk_size <= 0:
                logger.error(
                    'Argument chunk_size must be a strictly positive integer. '
                    'Provided: %s -> Changing to 16.', chunk_size)
                return 16
            if chunk_size not in (16, 32):
                logger.warning(
                    'The chunk size %i is different from the usual '
                    'values 16 or 32.', chunk_size)
            return chunk_size
        else:
            logger.error(
                'Argument chunk_size must be a strictly positive integer. '
                'Provided: %s -> Changing to 16.', chunk_size)
            return 16

    # --------------------------------------------------------------------
    @property
    def stream_name(self):
        """
        Stream's server name, displayed on LSL network.

        :type: `str`
        """
        return self._stream_name

    @property
    def fif_file(self):
        """
        Path to the ``.fif`` file to play.

        :type: `str` | `~pathlib.Path`
        """
        return self._fif_file

    @property
    def repeat(self):
        """
        Number of times the stream player will loop on the FIF file before
        interrupting. Default ``float('inf')`` can be passed to never interrupt
        streaming.

        :type: `int` | ``float('ìnf')``
        """
        return self._repeat

    @property
    def trigger_def(self):
        """
        Trigger def instance converting event numbers into event strings.

        :type: `~bsl.triggers.TriggerDef`
        """
        return self._trigger_def

    @property
    def chunk_size(self):
        """
        Size of a chunk of data ``[samples]``.

        :type: `int`
        """
        return self._chunk_size

    @property
    def high_resolution(self):
        """
        If True, use an high resolution counter instead of a sleep.

        :type: `bool`
        """
        return self._high_resolution

    @property
    def process(self):
        """
        Launched process.

        :type: `multiprocessing.Process`
        """
        return self._process

    @property
    def state(self):
        """
        Streaming state of the player:
            - ``0``: Not streaming.
            - ``1``: Streaming.

        :type: `multiprocessing.Value`
        """
        return self._state


@fill_doc
class _Streamer:
    """
    Class for playing a recorded file on LSL network.

    Parameters
    ----------
    %(player_stream_name)s
    %(player_fif_file)s
    %(player_chunk_size)s
    %(trigger_file)s
    """

    def __init__(self, stream_name, raw, repeat, trigger_def,
                 chunk_size, high_resolution, state):
        self._stream_name = stream_name
        self._raw = raw
        self._repeat = repeat
        self._trigger_def = trigger_def
        self._chunk_size = chunk_size
        self._high_resolution = high_resolution
        self._state = state

        self._sinfo = _Streamer._create_lsl_info(
            stream_name=self._stream_name,
            channel_count=len(self._raw.ch_names),
            nominal_srate=self._raw.info['sfreq'],
            ch_names=self._raw.ch_names)
        self._tch = find_event_channel(inst=self._raw)
        self._scale_raw_data()
        self._outlet = pylsl.StreamOutlet(
            self._sinfo, chunk_size=self._chunk_size)

    def _scale_raw_data(self):
        """
        Assumes raw data is in Volt and convert to microvolts.

        # TODO: Base the scaling on the units in the raw info
        """
        idx = np.arange(self._raw._data.shape[0]) != self._tch
        self._raw._data[idx, :] = self._raw.get_data()[idx, :] * 1E6

    def stream(self):
        """
        Stream data on LSL network.
        """
        idx_chunk = 0
        t_chunk = self._chunk_size / self._raw.info['sfreq']
        finished = False

        if self._high_resolution:
            t_start = time.perf_counter()
        else:
            t_start = time.time()

        played = 0

        with self._state.get_lock():
            self._state.value = 1

        # Streaming loop
        while self._state.value == 1:

            idx_current = idx_chunk * self._chunk_size
            idx_next = idx_current + self._chunk_size
            chunk = self._raw._data[:, idx_current:idx_next]
            data = chunk.transpose().tolist()

            if idx_current >= self._raw._data.shape[1] - self._chunk_size:
                finished = True

            _Streamer._sleep(self._high_resolution, idx_chunk, t_start,
                             t_chunk)

            self._outlet.push_chunk(data)
            logger.debug(
                '[%8.3fs] sent %d samples (LSL %8.3f)'
                % (time.perf_counter(), len(data), pylsl.local_clock()))

            self._log_event(chunk)
            idx_chunk += 1

            if finished:
                idx_chunk = 0
                finished = False
                if self._high_resolution:
                    t_start = time.perf_counter()
                else:
                    t_start = time.time()
                played += 1

                if played < self._repeat:
                    logger.info('Reached the end of data. Restarting.')
                else:
                    logger.info('Reached the end of data. Stopping.')
                    break

    def _log_event(self, chunk):
        """
        Look for an event on the data chunk and log it.
        """
        if self._tch is not None:
            event_values = set(chunk[self._tch]) - set([0])

            if len(event_values) > 0:
                if self._trigger_def is None:
                    logger.info(f'Events: {event_values}')
                else:
                    for event in event_values:
                        if event in self._trigger_def.by_value:
                            logger.info(
                                f'Events: {event} '
                                f'({self._tdef.by_value[event]})')
                        else:
                            logger.info(
                                f'Events: {event} (Undefined event {event})')

    # --------------------------------------------------------------------
    @staticmethod
    def _create_lsl_info(stream_name, channel_count, nominal_srate, ch_names):
        """
        Extract information from raw and set the LSL server's information
        needed to create the LSL stream.
        """
        sinfo = pylsl.StreamInfo(
            stream_name, channel_count=channel_count, channel_format='float32',
            nominal_srate=nominal_srate, type='EEG', source_id=stream_name)

        desc = sinfo.desc()
        channel_desc = desc.append_child("channels")
        for channel in ch_names:
            channel_desc.append_child('channel')\
                        .append_child_value('label', str(channel))\
                        .append_child_value('type', 'EEG')\
                        .append_child_value('unit', 'microvolts')

        desc.append_child('amplifier')\
            .append_child('settings')\
            .append_child_value('is_slave', 'false')

        desc.append_child('acquisition')\
            .append_child_value('manufacturer', 'BSL')\
            .append_child_value('serial_number', 'N/A')

        return sinfo

    @staticmethod
    def _sleep(high_resolution, idx_chunk, t_start, t_chunk):
        """
        Determine the time to sleep.
        """
        # if a resolution over 2 KHz is needed.
        if high_resolution:
            t_sleep_until = t_start + idx_chunk * t_chunk
            while time.perf_counter() < t_sleep_until:
                pass
        # time.sleep() can have 500 us resolution.
        else:
            t_wait = t_start + idx_chunk * t_chunk - time.time()
            if t_wait > 0.001:
                time.sleep(t_wait)
