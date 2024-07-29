from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from math import ceil
from time import sleep
from typing import TYPE_CHECKING

import numpy as np
from mne import pick_info
from mne.event import _find_events, _find_unique_events
from mne.utils import check_version

if check_version("mne", "1.6"):
    from mne._fiff.pick import _picks_to_idx

elif check_version("mne", "1.5"):
    from mne.io.pick import _picks_to_idx

else:
    from mne.io.pick import _picks_to_idx

from ..utils._checks import check_type, ensure_int
from ..utils._docs import fill_doc
from ..utils.logs import logger, warn
from ._base import BaseStream

if TYPE_CHECKING:
    from typing import Optional, Union

    from mne import Info
    from numpy.typing import NDArray

    from .._typing import ScalarArray, ScalarIntArray


@fill_doc
class EpochsStream:
    """Stream object representing a single real-time stream of epochs.

    Note that a stream of epochs is necessarily connected to a regularly sampled stream
    of continuous data, from which epochs are extracted depending on an internal event
    channel or to an external event stream.

    Parameters
    ----------
    stream : ``Stream``
        Stream object to connect to, from which the epochs are extracted. The stream
        must be regularly sampled.
    bufsize : int
        Number of epochs to keep in the buffer. The buffer size is defined by this
        number of epochs and by the duration of individual epochs, defined by the
        argument ``tmin`` and ``tmax``.

        .. note::

            For a new epoch to be added to the buffer, the epoch must be fully
            acquired, i.e. the last sample of the epoch must be received. Thus, an
            epoch is acquired at least ``tmax`` seconds after the event onset.
    event_id : int | dict
        The ID of the events to consider from the event source. The event source can be
        a channel from the connected Stream or a separate event stream. In both case the
        event should be defined either as :class:`int`. If a :class:`dict` is provided,
        it should map event names to event IDs. For example
        ``dict(auditory=1, visual=2)``. If the event source is an irregularly sampled
        stream, the numerical values within the channels are ignored and this argument
        is ignored.
    event_channels : str | list of str
        Channel(s) to monitor for incoming events. The event channel(s) must be part of
        the connected Stream or of the ``event_stream`` if provided. See notes for
        details.
    event_stream : ``Stream`` | None
        Source from which events should be retrieved. If provided, event channels in the
        connected ``stream`` are ignored in favor of the event channels in this separate
        ``event_stream``. See notes for details.

        .. note::

            If a separate event stream is provided, time synchronization between the
            connected stream and the event stream is very important. For
            :class:`~mne_lsl.stream.StreamLSL` objects, provide
            ``processing_flags='all'`` as argument during connection with
            :meth:`~mne_lsl.stream.StreamLSL.connect`.
    %(epochs_tmin_tmax)s
    %(baseline_epochs)s
    %(picks_base)s all channels.
    %(reject_epochs)s
    %(flat)s
    %(epochs_reject_tmin_tmax)s
    detrend : int | str | None
        The type of detrending to use. Can be ``'constant'`` or ``0`` for constant (DC)
        detrend, ``'linear'`` or ``1`` for linear detrend, or ``None`` for no
        detrending. Note that detrending is performed before baseline correction.

    Notes
    -----
    Since events can be provided from multiple source, the arguments ``event_channels``,
    ``event_source`` and ``event_id`` must work together to select which events should
    be considered.

    - if ``event_stream`` is ``None``, the events are extracted from channels within the
      connected ``stream``. This ``stream`` is necessarily regularly sampled, thus the
      event channels must correspond to MNE ``'stim'`` channels, i.e. channels on which
      :func:`mne.find_events` can be applied.
    - if ``event_stream`` is provided and is regularly sampled, the events are extracted
      from channels in the ``event_stream``. The event channels must correspond to MNE
      ``'stim'`` channels, i.e. channels on which :func:`mne.find_events` can be
      applied.
    - if ``event_stream`` is provided and is irregularly sampled, the events are
      extracted from channels in the ``event_stream``. The numerical value within the
      channels are ignored and the appearance of a new value in the stream is considered
      as a new event named after the channel name. Thus, the argument ``event_id`` is
      ignored. This last case can be useful when working with a ``Player`` replaying
      annotations from a file as one-hot encoded events.

    Event streams irregularly sampled and a ``str`` datatype are not yet supported.

    .. note::

        In the 2 last cases where ``event_stream`` is provided, all ``'stim'`` channels
        in the connected ``stream`` are ignored.
    """

    def __init__(
        self,
        stream: BaseStream,
        bufsize: int,
        event_id: Union[int, dict[str, int]],
        event_channels: Union[str, list[str]],
        event_stream: Optional[BaseStream] = None,
        tmin: float = -0.2,
        tmax: float = 0.5,
        baseline: Optional[tuple[Optional[float], Optional[float]]] = (None, 0),
        picks: Optional[Union[str, list[str], int, list[int], ScalarIntArray]] = None,
        reject: Optional[dict[str, float]] = None,
        flat: Optional[dict[str, float]] = None,
        reject_tmin: Optional[float] = None,
        reject_tmax: Optional[float] = None,
        detrend: Optional[Union[int, str]] = None,
    ) -> None:
        check_type(stream, (BaseStream,), "stream")
        if not stream.connected and stream._info["sfreq"] != 0:
            raise RuntimeError(
                "The Stream must be a connected regularly sampled stream before "
                "creating an EpochsStream."
            )
        self._stream = stream
        # mark the stream(s) as being epoched, which will prevent further channel
        # modification and buffer size modifications.
        self._stream._epochs.append(self)
        check_type(tmin, ("numeric",), "tmin")
        check_type(tmax, ("numeric",), "tmax")
        if tmax <= tmin:
            raise ValueError(
                f"Argument 'tmax' (provided: {tmax}) must be greater than 'tmin' "
                f"(provided: {tmin})."
            )
        # make sure the stream buffer is long enough to store an entire epoch, which is
        # simpler than handling the case where the buffer is too short and we need to
        # concatenate chunks to form a single epoch.
        if self._stream._bufsize < tmax - tmin:
            raise ValueError(
                "The buffer size of the Stream must be at least as long as the epoch "
                "duration (tmax - tmin)."
            )
        elif self._stream._bufsize < (tmax - tmin) * 1.2:
            warn(
                "The buffer size of the Stream is longer than the epoch duration, but "
                "not by at least 20%. It is recommended to have a buffer size at least "
                r"20% longer than the epoch duration to avoid data loss."
            )
        self._tmin = tmin
        self._tmax = tmax
        # check the event source(s)
        check_type(event_stream, (BaseStream, None), "event_stream")
        if event_stream is not None and not event_stream.connected:
            raise RuntimeError(
                "If 'event_stream' is provided, it must be connected before creating "
                "an EpochsStream."
            )
        self._event_stream = event_stream
        if self._event_stream is not None:
            self._event_stream._epochs.append(self)
        event_channels = (
            [event_channels] if isinstance(event_channels, str) else event_channels
        )
        check_type(event_channels, (list,), "event_channels")
        _check_event_channels(event_channels, stream, event_stream)
        self._event_channels = event_channels
        # check and store the epochs general settings
        self._bufsize = ensure_int(bufsize, "bufsize")
        if self._bufsize <= 0:
            raise ValueError(
                "The buffer size, i.e. the number of epochs in the buffer, must be a "
                "positive integer."
            )
        self._event_id = _ensure_event_id_dict(event_id)
        _check_baseline(baseline, self._tmin, self._tmax)
        self._baseline = baseline
        _check_reject_flat(reject, flat, self._stream._info)
        self._reject, self._flat = reject, flat
        _check_reject_tmin_tmax(reject_tmin, reject_tmax, tmin, tmax)
        self._reject_tmin, self._reject_tmax = reject_tmin, reject_tmax
        self._detrend = _ensure_detrend_int(detrend)
        # store picks which are then initialized in the connect method
        self._picks_init = picks
        # define acquisition variables which need to be reset on disconnect
        self._reset_variables()

    def __del__(self) -> None:
        """Delete the epoch stream object."""
        logger.debug("Deleting %s", self)
        try:
            self.disconnect()
        except Exception:
            pass

    def __repr__(self) -> str:
        """Representation of the instance."""
        try:
            status = "ON" if self.connected else "OFF"
        except Exception:
            status = "OFF"
        return (
            f"<EpochsStream {status} (n: {self._bufsize} between ({self._tmin}, "
            f"{self._tmax}) seconds> connected to:\n\t{self._stream}"
        )

    def acquire(self) -> None:
        """Pull new epochs in the buffer.

        This method is used to manually acquire new epochs in the buffer. If used, it is
        up to the user to call this method at the desired frequency, else it might miss
        some of the events and associated epochs.

        Notes
        -----
        This method is not needed if the :class:`mne_lsl.stream.EpochsStream` was
        connected with an acquisition delay different from ``0``. In this case, the
        acquisition is done automatically in a background thread.
        """
        self._check_connected("acquire")
        if (
            self._executor is not None and self._acquisition_delay == 0
        ):  # pragma: no cover
            raise RuntimeError(
                "The executor is not None despite the acquisition delay set to "
                f"{self._acquisition_delay} seconds. This should not happen, please "
                "contact the developers on GitHub."
            )
        elif self._executor is not None and self._acquisition_delay != 0:
            raise RuntimeError(
                "Acquisition is done automatically in a background thread. The method "
                "epochs.acquire() should not be called."
            )
        self._acquire()

    def connect(self, acquisition_delay: float = 0.001) -> EpochsStream:
        """Start acquisition of epochs from the connected Stream.

        Parameters
        ----------
        acquisition_delay : float
            Delay in seconds between 2 updates at which the event stream is queried for
            new events, and thus at which the epochs are updated.

            .. note::

                For a new epoch to be added to the buffer, the epoch must be fully
                acquired, i.e. the last sample of the epoch must be received. Thus, an
                epoch is acquired ``tmax`` seconds after the event onset.

        Returns
        -------
        epochs_stream : instance of EpochsStream
            The :class:`~mne_lsl.stream.EpochsStream` instance modified in-place.
        """
        if self.connected:
            warn("The EpochsStream is already connected. Skipping.")
            return self
        if not self._stream.connected:
            raise RuntimeError(
                "The Stream was disconnected between initialization and connection "
                "of the EpochsStream object."
            )
        if self._event_stream is not None and not self._event_stream.connected:
            raise RuntimeError(
                "The event stream was disconnected between initialization and "
                "connection of the EpochsStream object."
            )
        check_type(acquisition_delay, ("numeric",), "acquisition_delay")
        if acquisition_delay < 0:
            raise ValueError(
                "The acquisition delay must be a positive number defining the delay at "
                "which the epochs might be updated in seconds. For instance, 0.2 "
                "corresponds to a query to the event source every 200 ms. 0 "
                f"corresponds to manual acquisition. The provided {acquisition_delay} "
                "is invalid."
            )
        self._acquisition_delay = acquisition_delay
        assert self._n_new_epochs == 0  # sanity-check
        # create the buffer and start acquisition in a separate thread
        self._picks = _picks_to_idx(
            self._stream._info, self._picks_init, "all", "bads", allow_empty=False
        )
        self._info = pick_info(self._stream._info, self._picks)
        self._buffer = np.zeros(
            (
                self._bufsize,
                ceil((self._tmax - self._tmin) * self._info["sfreq"]),
                self._picks.size,
            ),
            dtype=self._stream._buffer.dtype,
        )
        self._executor = (
            ThreadPoolExecutor(max_workers=1) if self._acquisition_delay != 0 else None
        )
        logger.debug("%s: ThreadPoolExecutor started.", self)
        # submit the first acquisition job
        if self._executor is not None:
            self._executor.submit(self._acquire)
        return self

    def disconnect(self) -> None:
        """Stop acquisition of epochs from the connected Stream."""
        if not self.connected:
            warn("The EpochsStream is already disconnected. Skipping.")
            # just in case, let's look through the stream objects attached..
            if hasattr(self._stream, "_epochs") and self in self._stream._epochs:
                self._stream._epochs.remove(self)
            if (
                self._event_stream is not None
                and hasattr(self._event_stream, "_epochs")
                and self in self._event_stream._epochs
            ):
                self._event_stream._epochs.remove(self)
            return
        if hasattr(self, "_executor") and self._executor is not None:
            self._executor.shutdown(wait=True, cancel_futures=True)
        self._reset_variables()
        if hasattr(self._stream, "_epochs") and self in self._stream._epochs:
            self._stream._epochs.remove(self)
        if (
            self._event_stream is not None
            and hasattr(self._event_stream, "_epochs")
            and self in self._event_stream._epochs
        ):
            self._event_stream._epochs.remove(self)

    @fill_doc
    def get_data(
        self,
        picks: Optional[Union[str, list[str], int, list[int], ScalarIntArray]] = None,
    ) -> ScalarArray:
        """Retrieve the latest epochs from the buffer.

        Parameters
        ----------
        %(picks_all)s

        Returns
        -------
        data : array of shape (n_epochs, n_channels, n_samples)
            Data in the buffer.

        Notes
        -----
        The number of newly available epochs stored in the property ``n_new_epochs``
        is reset at every function call, even if all channels were not selected with the
        argument ``picks``.
        """
        picks = _picks_to_idx(self._info, picks, none="all", exclude="bads")
        self._new_new_epochs = 0  # reset the number of new epochs
        return np.transpose(self._buffer[:, :, picks], axes=(0, 2, 1))

    def _acquire(self) -> None:
        """Update function looking for new epochs."""
        try:
            if self._stream._n_new_samples == 0 or (
                self._event_stream is not None
                and self._event_stream._n_new_samples == 0
            ):
                self._submit_acquisition_job()
                return
            # split the different acquisition scenarios to retrieve new events to add to
            # the buffer.
            data, ts = self._stream.get_data()
            if self._event_stream is None:
                picks_events = _picks_to_idx(
                    self._info, self._event_channels, exclude=()
                )
                events = _find_events_in_stim_channels(
                    data[picks_events, :], self._event_channels, self._info["sfreq"]
                )
                events = _prune_events(
                    events,
                    self._event_id,
                    self._buffer.shape[1],
                    ts,
                    self._last_ts,
                    None,
                )
            elif (
                self._event_stream is not None
                and self._event_stream._info["sfreq"] != 0
            ):
                data_events, ts_events = self._event_stream.get_data(
                    picks=self._event_channels
                )
                events = _find_events_in_stim_channels(
                    data_events, self._event_channels, self._info["sfreq"]
                )
                events = _prune_events(
                    events,
                    self._event_id,
                    self._buffer.shape[1],
                    ts,
                    self._last_ts,
                    ts_events,
                )
            elif (
                self._event_stream is not None
                and self._event_stream._info["sfreq"] == 0
            ):
                data_events, ts_events = self._event_stream.get_data(
                    picks=self._event_channels
                )
                events = np.vstack(
                    [
                        np.arange(ts_events.size, dtype=np.int64),
                        np.zeros(ts_events.size, dtype=np.int64),
                        np.argmax(data, axis=1),
                    ],
                    dtype=np.int64,
                )
                events = _prune_events(
                    events, None, self._buffer.shape[1], ts, self._last_ts, ts_events
                )
            else:  # pragma: no cover
                raise RuntimeError(
                    "This acquisition scenario should not happen. Please contact the "
                    "developers."
                )
            if events.shape[0] == 0:  # abort in case we don't have new events to add
                self._submit_acquisition_job()
                return
            # select data, for loop is faster than the fancy indexing ideas tried and
            # will anyway operate on a small number of events most of the time.
            data_selection = np.empty(
                (events.shape[0], self._buffer.shape[1], self._picks.size),
                dtype=data.dtype,
            )
            shift = round(self._tmin * self._info["sfreq"])  # 28.7 ns ± 0.369 ns
            for k, start in enumerate(events[:, 0]):
                start += shift
                data_selection[k] = data[
                    self._picks, start : start + self._buffer.shape[1]
                ].T
            # apply processing
            data_selection = _process_data(data_selection)
            # roll buffer and add new epochs
            self._buffer = np.roll(self._buffer, -events.shape[0], axis=0)
            self._buffer[-events.shape[0] :, :, :] = data_selection
            # update the last ts and the number of new epochs
            self._last = ts[events[-1, 0]]
            self._n_new_epochs += events.shape[0]
        except Exception as error:  # pragma: no cover
            logger.exception(error)
            self._reset_variables()
            if os.getenv("MNE_LSL_RAISE_STREAM_ERRORS", "false").lower() == "true":
                raise error
        else:
            self._submit_acquisition_job()

    def _check_connected(self, name: str) -> None:
        """Check that the epochs stream is connected before calling 'name'."""
        if not self.connected:
            raise RuntimeError(
                "The EpochsStream is not connected. Please connect to the EpochsStream "
                "with the method epochs.connect(...) to use "
                f"{type(self).__name__}.{name}."
            )

    def _reset_variables(self):
        """Reset variables defined after connection."""
        self._acquisition_delay = None
        self._buffer = None
        self._executor = None
        self._info = None
        self._last_ts = None
        self._n_new_epochs = 0
        self._picks = None

    def _submit_acquisition_job(self) -> None:
        """Submit a new acquisition job, if applicable."""
        if self._executor is None:
            return  # either shutdown or manual acquisition
        sleep(self._acquisition_delay)
        try:
            self._executor.submit(self._acquire)
        except RuntimeError:  # pragma: no cover
            pass  # shutdown

    # ----------------------------------------------------------------------------------
    @property
    def connected(self) -> bool:
        """Connection status of the :class:`~mne_lsl.stream.EpochsStream`.

        :type: :class:`bool`
        """
        attributes = (
            "_acquisition_delay",
            "_buffer",
            "_info",
            "_picks",
        )
        if all(getattr(self, attr, None) is None for attr in attributes):
            return False
        else:
            # sanity-check
            assert not any(getattr(self, attr, None) is None for attr in attributes)
            return True

    @property
    def info(self) -> Info:
        """Info of the epoched LSL stream.

        :type: :class:`~mne.Info`
        """
        if not self.connected:
            raise RuntimeError(
                "The EpochsStream information is parsed into an mne.Info object "
                "upon connection. Please connect the EpochsStream to create the "
                "mne.Info."
            )
        return self._info

    @property
    def n_new_epochs(self) -> int:
        """Number of new epochs available in the buffer.

        The number of new epochs is reset at every ``Stream.get_data`` call.

        :type: :class:`int`
        """
        self._check_connected("n_new_epochs")
        return self._n_new_epochs


def _check_event_channels(
    event_channels: list[str],
    stream: BaseStream,
    event_stream: Optional[BaseStream],
) -> None:
    """Check that the event channels are valid."""
    for elt in event_channels:
        check_type(elt, (str,), "event_channels")
        if event_stream is None:
            if elt not in stream._info.ch_names:
                raise ValueError(
                    "The event channel(s) must be part of the connected Stream if "
                    f"an 'event_stream' is not provided. '{elt}' was not found."
                )
            if elt in stream._info["bads"]:
                raise ValueError(
                    f"The event channel '{elt}' should not be marked as bad in the "
                    "connected Stream."
                )
            if stream.get_channel_types(picks=elt)[0] != "stim":
                raise ValueError(f"The event channel '{elt}' should be of type 'stim'.")
        elif event_stream is not None:
            if elt not in event_stream._info.ch_names:
                raise ValueError(
                    "If 'event_stream' is provided, the event channel(s) must be "
                    f"part of 'event_stream'. '{elt}' was not found."
                )
            if elt in event_stream._info["bads"]:
                raise ValueError(
                    f"The event channel '{elt}' in the event stream should not be "
                    "marked as bad."
                )
            if (
                event_stream._info["sfreq"] != 0
                and event_stream.get_channel_types(picks=elt)[0] != "stim"
            ):
                raise ValueError(
                    f"The event channel '{elt}' in the event stream should be of type "
                    "'stim' if the event stream is regularly sampled."
                )


def _ensure_event_id_dict(event_id: Union[int, dict[str, int]]) -> dict[str, int]:
    """Ensure event_ids is a dictionary."""
    check_type(event_id, (int, dict), "event_id")
    raise_ = False
    if isinstance(event_id, int):
        if event_id <= 0:
            raise_ = True
        event_id = {str(event_id): event_id}
    else:
        for key, value in event_id.items():
            check_type(key, (str,), "event_id")
            check_type(value, ("int-like",), "event_id")
            if len(key) == 0:
                raise_ = True
            if isinstance(value, int) and value <= 0:
                raise_ = True
    if raise_:
        raise ValueError(
            "The 'event_id' must be a positive integer or a dictionary mapping "
            "non-empty strings to positive integers."
        )
    return event_id


def _check_baseline(
    baseline: Optional[tuple[Optional[float], Optional[float]]],
    tmin: float,
    tmax: float,
) -> None:
    """Check that the baseline is valid."""
    check_type(baseline, (tuple, None), "baseline")
    if baseline is None:
        return
    if len(baseline) != 2:
        raise ValueError("The baseline must be a tuple of 2 elements.")
    check_type(baseline[0], ("numeric", None), "baseline[0]")
    check_type(baseline[1], ("numeric", None), "baseline[1]")
    if baseline[0] is not None and baseline[0] < tmin:
        raise ValueError(
            "The beginning of the baseline period must be greater than or equal to "
            "the beginning of the epoch period 'tmin'."
        )
    if baseline[1] is not None and tmax < baseline[1]:
        raise ValueError(
            "The end of the baseline period must be less than or equal to the end of "
            "the epoch period 'tmax'."
        )


def _check_reject_flat(
    reject: Optional[dict[str, float]], flat: Optional[dict[str, float]], info: Info
) -> None:
    """Check that the PTP rejection dictionaries are valid."""
    check_type(reject, (dict, None), "reject")
    check_type(flat, (dict, None), "flat")
    ch_types = info.get_channel_types(unique=True)
    if reject is not None:
        for key, value in reject.items():
            check_type(key, (str,), "reject")
            check_type(value, ("numeric",), "reject")
            if key not in ch_types:
                raise ValueError(
                    f"The channel type '{key}' in the rejection dictionary is not part "
                    "of the connected Stream."
                )
            check_type(value, (float,), "reject")
            if value <= 0:
                raise ValueError(
                    f"The peak-to-peak rejection value for channel type '{key}' must "
                    "be a positive number."
                )
    if flat is not None:
        for key, value in flat.items():
            check_type(key, (str,), "flat")
            check_type(value, ("numeric",), "flat")
            if key not in ch_types:
                raise ValueError(
                    f"The channel type '{key}' in the flat rejection dictionary is not "
                    "part of the connected Stream."
                )
            check_type(value, (float,), "flat")
            if value <= 0:
                raise ValueError(
                    f"The flat rejection value for channel type '{key}' must be a "
                    "positive number."
                )


def _check_reject_tmin_tmax(
    reject_tmin: Optional[float], reject_tmax: Optional[float], tmin: float, tmax: float
) -> None:
    """Check that the rejection time window is valid."""
    check_type(reject_tmin, ("numeric", None), "reject_tmin")
    check_type(reject_tmax, ("numeric", None), "reject_tmax")
    if reject_tmin is not None and reject_tmin < tmin:
        raise ValueError(
            "The beginning of the rejection time window must be greater than or equal "
            "to the beginning of the epoch period 'tmin'."
        )
    if reject_tmax is not None and tmax < reject_tmax:
        raise ValueError(
            "The end of the rejection time window must be less than or equal to the "
            "end of the epoch period 'tmax'."
        )
    if (
        reject_tmin is not None
        and reject_tmax is not None
        and reject_tmax <= reject_tmin
    ):
        raise ValueError(
            "The end of the rejection time window must be greater than the beginning "
            "of the rejection time window."
        )


def _ensure_detrend_int(detrend: Optional[Union[int, str]]) -> Optional[int]:
    """Ensure detrend is an integer."""
    if detrend is None:
        return None
    if isinstance(detrend, str):
        if detrend == "constant":
            return 0
        elif detrend == "linear":
            return 1
        else:
            raise ValueError(
                "The detrend argument must be 'constant', 'linear' or their integer "
                "equivalent 0 and 1."
            )
    detrend = ensure_int(detrend, "detrend")
    if detrend not in (0, 1):
        raise ValueError(
            "The detrend argument must be 'constant', 'linear' or their integer "
            "equivalent 0 and 1."
        )
    return detrend


def _find_events_in_stim_channels(
    data: ScalarArray,
    event_channels: list[str],
    sfreq: float,
    *,
    output: str = "onset",
    consecutive: Union[bool, str] = "increasing",
    min_duration: float = 0,
    shortest_event: int = 2,
    mask: Optional[int] = None,
    uint_cast: bool = False,
    mask_type: str = "and",
    initial_event: bool = False,
) -> NDArray[np.int64]:
    """Find events in stim channels."""
    min_samples = min_duration * sfreq
    events_list = []
    for d, ch_name in zip(data, event_channels):
        events = _find_events(
            d[np.newaxis, :],
            first_samp=0,
            verbose="CRITICAL",  # disable MNE's logging
            output=output,
            consecutive=consecutive,
            min_samples=min_samples,
            mask=mask,
            uint_cast=uint_cast,
            mask_type=mask_type,
            initial_event=initial_event,
            ch_name=ch_name,
        )
        # add safety check for spurious events (for ex. from neuromag syst.) by
        # checking the number of low sample events
        n_short_events = np.sum(np.diff(events[:, 0]) < shortest_event)
        if n_short_events > 0:
            warn(
                f"You have {n_short_events} events shorter than the shortest_event. "
                "These are very unusual and you may want to set min_duration to a "
                "larger value e.g. x / raw.info['sfreq']. Where x = 1 sample shorter "
                "than the shortest event length."
            )
        events_list.append(events)
    events = np.concatenate(events_list, axis=0)
    events = _find_unique_events(events)
    return events[np.argsort(events[:, 0])]


def _prune_events(
    events: NDArray[np.int64],
    event_id: Optional[dict[str, int]],
    buffer_size: int,
    ts: NDArray[np.float64],
    last_ts: Optional[float],
    ts_events: Optional[NDArray[np.float64]],
) -> NDArray[np.int64]:
    """Prune events based on criteria and buffer size."""
    # remove events outside of the event_id dictionary
    if event_id is not None:
        sel = np.isin(events[:, 2], list(event_id.values()))
        events = events[sel]
    # get the events position in the stream times
    if ts_events is not None:
        events[:, 0] = np.searchsorted(ts, ts_events[events[:, 0]], side="left")
    # remove events which can't fit an entire epoch
    sel = np.where(events[:, 0] + buffer_size <= ts.size)[0]
    events = events[sel]
    # remove events which have already been moved to the buffer
    if last_ts is not None:
        sel = np.where(ts[events[:, 0]] > last_ts)[0]
        events = events[sel]
    return events


def _process_data(data: ScalarArray) -> ScalarArray:
    """Apply the requested processing to the new epochs."""
    return data
