import time
import multiprocessing as mp

import pylsl
import numpy as np

from .. import logger
from ..triggers import TriggerDef
from ..utils.io import read_raw_fif
from ..utils.preprocess.events import find_event_channel


class StreamPlayer:
    """
    Class for playing a recorded file on LSL network in another process.

    Parameters
    ----------
    stream_name : str
        The stream's name, displayed on LSL network.
    fif_file : str
        The absolute path to the .fif file to play.
    chunk_size : int
        The number of samples to send at once (usually 16-32 is good enough).
    trigger_file : str
        The absolute path to the file containing the table converting event
        numbers into event strings.

    Notes
    -----
    It instances a Streamer in a new process and call Streamer.stream().
    """

    def __init__(self, stream_name, fif_file, chunk_size,
                 trigger_file=None):

        self._stream_name = str(stream_name)
        self._fif_file = fif_file
        self._chunk_size = StreamPlayer._check_chunk_size(chunk_size)
        self._trigger_file = trigger_file
        self._process = None

    def start(self, repeat=np.float('inf'), high_resolution=False):
        """
        Start streaming data on LSL network in a new process by calling
        stream().

        Parameters
        ----------
        repeat : float
            The number of times to replay the data.
        high_resolution : bool
            If True, it uses perf_counter() instead of sleep() for higher time
            resolution. However, it uses more CPU.
        """
        logger.info('Streaming started.')
        self._process = mp.Process(target=self._stream,
                                   args=(repeat, high_resolution))
        self._process.start()

    def stop(self):
        """
        Stop the streaming, by terminating the process.
        """
        if self._process is not None and self._process.is_alive():
            logger.info(
                f"Stop streaming data from: '{self.stream_name}'.")
            self._process.kill()
            self._process = None

    def _stream(self, repeat, high_resolution):
        """
        The function called in the new process.
        Instance a Streamer and start streaming.
        """
        streamer = _Streamer(
            self._stream_name, self._fif_file,
            self._chunk_size, self._trigger_file)
        streamer.stream(repeat, high_resolution)

    # --------------------------------------------------------------------
    @staticmethod
    def _check_chunk_size(chunk_size):
        """
        Checks that the chunk size is a strictly positive integer.
        """
        chunk_size = int(chunk_size)
        if chunk_size <= 0:
            logger.error(
                'The chunk size must be a positive integer. Usual: 16, 32.')
            raise ValueError

        if chunk_size not in (16, 32):
            logger.warning(
                'The chunk size is different from the usual 16 or 32.')

        return chunk_size

    # --------------------------------------------------------------------
    @property
    def stream_name(self):
        """
        The stream's name, displayed on LSL network.
        """
        return self._stream_name

    @stream_name.setter
    def stream_name(self, stream_name):
        if self._process is None:
            self._stream_name = str(stream_name)
        else:
            logger.error(
                f'StreamPlayer is currently streaming on {self._stream_name}. '
                'Stop the stream before changing the name. Skipping.')

    @property
    def fif_file(self):
        """
        The absolute path to the .fif file to play.
        """
        return self._fif_file

    @fif_file.setter
    def fif_file(self, fif_file):
        if self._process is None:
            self._fif_file = fif_file
        else:
            logger.error(
                f'StreamPlayer is currently streaming on {self._stream_name}. '
                'Stop the stream before changing the FIF file. Skipping.')

    @property
    def chunk_size(self):
        """
        The size of a chunk of data [samples].
        """
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, chunk_size):
        if self._process is None:
            self._chunk_size = StreamPlayer._check_chunk_size(chunk_size)
        else:
            logger.error(
                f'StreamPlayer is currently streaming on {self._stream_name}. '
                'Stop the stream before changing the chunk size. Skipping.')

    @property
    def trigger_file(self):
        """
        The absolute path to the file containing the table converting event
        numbers into event strings.
        """
        return self._trigger_file

    @trigger_file.setter
    def trigger_file(self, trigger_file):
        if self._process is None:
            self._trigger_file = trigger_file
        else:
            logger.error(
                f'StreamPlayer is currently streaming on {self._stream_name}. '
                'Stop the stream before changing the trigger file. Skipping.')

    @property
    def process(self):
        """
        The launched process.
        """
        return self._process

    @process.setter
    def process(self, process):
        logger.warning("The stream process cannot be changed directly.")


class _Streamer:
    """
    Class for playing a recorded file on LSL network.

    Parameters
    ----------
    stream_name : str
        The stream's name, displayed on LSL network.
    fif_file : str
        The absolute path to the .fif file to play.
    chunk_size : int
        The number of samples to send at once (usually 16-32 is good enough).
    trigger_file : str
        The absolute path to the file containing the table converting event
        numbers into event strings.
    """

    def __init__(self, stream_name, fif_file, chunk_size, trigger_file=None):
        self._stream_name = str(stream_name)
        self._chunk_size = StreamPlayer._check_chunk_size(chunk_size)

        try:
            self._tdef = TriggerDef(trigger_file)
        except Exception:
            self._tdef = None

        self._load_data(fif_file)

    def _load_data(self, fif_file):
        """
        Load the data to play from a fif file.
        Multiplies all channel except trigger by 1e6 to convert to uV.

        Parameters
        ----------
        fif_file : str
            The absolute path to the .fif file to play.
        """
        self._raw, self._events = read_raw_fif(fif_file)
        self._tch = find_event_channel(inst=self._raw)
        self._sample_rate = self._raw.info['sfreq']
        self._ch_count = len(self._raw.ch_names)
        idx = np.arange(self._raw._data.shape[0]) != self._tch
        self._raw._data[idx, :] = self._raw.get_data()[idx, :] * 1E6
        # TODO: Base the scaling on the units in the raw info

        self._set_lsl_info(self._stream_name)
        self._outlet = pylsl.StreamOutlet(
            self._sinfo, chunk_size=self._chunk_size)
        self._show_info()

    def _set_lsl_info(self, stream_name):
        """
        Set the LSL server's infos needed to create the LSL stream.

        Parameters
        ----------
        stream_name : str
            The stream's name, displayed on LSL network.
        """
        sinfo = pylsl.StreamInfo(
            stream_name, channel_count=self._ch_count,
            channel_format='float32', nominal_srate=self._sample_rate,
            type='EEG', source_id=stream_name)

        desc = sinfo.desc()
        channel_desc = desc.append_child("channels")
        for channel in self._raw.ch_names:
            channel_desc.append_child('channel')\
                        .append_child_value('label', str(channel))\
                        .append_child_value('type', 'EEG')\
                        .append_child_value('unit', 'microvolts')

        desc.append_child('amplifier')\
            .append_child('settings')\
            .append_child_value('is_slave', 'false')

        desc.append_child('acquisition')\
            .append_child_value('manufacturer', 'NeuroDecode')\
            .append_child_value('serial_number', 'N/A')

        self._sinfo = sinfo

    def _show_info(self):
        """
        Display the informations about the created LSL stream.
        """
        logger.info(f'Stream name: {self._stream_name}')
        logger.info(f'Sampling frequency {self._sample_rate = :.3f} Hz')
        logger.info(f'Number of channels : {self._ch_count}')
        logger.info(f'Chunk size : {self._chunk_size}')
        for i, channel in enumerate(self._raw.ch_names):
            logger.info(f'{i} {channel}')
        logger.info(f'Trigger channel : {self._tch}')

    def stream(self, repeat=np.float('inf'), high_resolution=False):
        """
        Stream data on LSL network.

        Parameters
        ----------
        repeat : int
            The number of times to replay the data (Default=inf).
        high_resolution : bool
            If True, it uses perf_counter() instead of sleep() for higher time
            resolution. However, it uses more CPU.
        """
        idx_chunk = 0
        t_chunk = self._chunk_size / self._sample_rate
        finished = False

        if high_resolution:
            t_start = time.perf_counter()
        else:
            t_start = time.time()

        # start streaming
        played = 0
        while True:

            idx_current = idx_chunk * self._chunk_size
            idx_next = idx_current + self._chunk_size
            chunk = self._raw._data[:, idx_current:idx_next]
            data = chunk.transpose().tolist()

            if idx_current >= self._raw._data.shape[1] - self._chunk_size:
                finished = True

            self._sleep(high_resolution, idx_chunk, t_start, t_chunk)

            self._outlet.push_chunk(data)
            logger.debug(
                '[%8.3fs] sent %d samples (LSL %8.3f)'
                % (time.perf_counter(), len(data), pylsl.local_clock()))

            self._log_event(chunk)
            idx_chunk += 1

            if finished:
                idx_chunk = 0
                finished = False
                if high_resolution:
                    t_start = time.perf_counter()
                else:
                    t_start = time.time()
                played += 1

                if played < repeat:
                    logger.info('Reached the end of data. Restarting.')
                else:
                    logger.info('Reached the end of data. Stopping.')
                    break

    def _sleep(self, high_resolution, idx_chunk, t_start, t_chunk):
        """
        Determine the time to sleep.
        """
        if high_resolution:
            # if a resolution over 2 KHz is needed
            t_sleep_until = t_start + idx_chunk * t_chunk
            while time.perf_counter() < t_sleep_until:
                pass
        else:
            # time.sleep() can have 500 us resolution.
            t_wait = t_start + idx_chunk * t_chunk - time.time()
            if t_wait > 0.001:
                time.sleep(t_wait)

    def _log_event(self, chunk):
        """
        Look for an event on the data chunk and log it.
        """
        if self._tch is not None:
            event_values = set(chunk[self._tch]) - set([0])

            if len(event_values) > 0:
                if self._tdef is None:
                    logger.info(f'Events: {event_values}')
                else:
                    for event in event_values:
                        if event in self._tdef.by_value:
                            logger.info(
                                f'Events: {event} '
                                f'({self._tdef.by_value[event]})')
                        else:
                            logger.info(
                                f'Events: {event} (Undefined event {event})')
