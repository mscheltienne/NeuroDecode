from __future__ import print_function, division

"""
features.py

Feature computation module.


Kyuhwa Lee, 2019
Swiss Federal Institute of Technology Lausanne (EPFL)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import os
import sys
import imp
import mne
import mne.io
import pycnbi
import timeit
import platform
import traceback
import numpy as np
import multiprocessing as mp
import sklearn.metrics as skmetrics
import pycnbi.utils.q_common as qc
import pycnbi.utils.pycnbi_utils as pu
from mne import Epochs, pick_types
from pycnbi import logger
from pycnbi.decoder.rlda import rLDA
from builtins import input
from IPython import embed  # for debugging
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis as LDA


def slice_win(epochs_data, w_starts, w_length, psde, picks=None, epoch_id=None, flatten=True, verbose=False):
    '''
    Compute PSD values of a sliding window

    Params
        epochs_data: [channels] x [samples]
        w_starts: starting indices of sample segments
        w_length: window length in number of samples
        psde: MNE PSDEstimator object
        picks: subset of channels within epochs_data
        epochs_id: just to print out epoch ID associated with PID
        flatten: generate concatenated feature vectors
            If True: X = [windows] x [channels x freqs]
            If False: X = [windows] x [channels] x [freqs]

    Returns:
        [windows] x [channels*freqs] or [windows] x [channels] x [freqs]
    '''

    # raise error for wrong indexing
    def WrongIndexError(Exception):
        sys.stderr.write('\nERROR: %s\n' % Exception)
        sys.exit(-1)

    w_length = int(w_length)

    if epoch_id is None:
        logger.info('[PID %d] Frames %d-%d' % (os.getpid(), w_starts[0], w_starts[-1] + w_length - 1))
    else:
        logger.info('[PID %d] Epoch %d, Frames %d-%d' % (os.getpid(), epoch_id, w_starts[0], w_starts[-1] + w_length - 1))

    X = None
    for n in w_starts:
        n = int(n)
        if n >= epochs_data.shape[1]:
            raise WrongIndexError(
                'w_starts has an out-of-bounds index %d for epoch length %d.' % (n, epochs_data.shape[1]))
        window = epochs_data[:, n:(n + w_length)]

        # dimension: psde.transform( [epochs x channels x times] )
        psd = psde.transform(window.reshape((1, window.shape[0], window.shape[1])))
        psd = psd.reshape((psd.shape[0], psd.shape[1] * psd.shape[2]))
        if picks:
            psd = psd[0][picks]
            psd = psd.reshape((1, len(psd)))

        if X is None:
            X = psd
        else:
            X = np.concatenate((X, psd), axis=0)

        if verbose == True:
            logger.info('[PID %d] processing frame %d / %d' % (os.getpid(), n, w_starts[-1]))

    return X


def get_psd(epochs, psde, wlen, wstep, picks=None, flatten=True, n_jobs=1):
    """
    Offline computation of multi-taper PSDs over a sliding window

    Params
    epochs: MNE Epochs object
    psde: MNE PSDEstimator object
    wlen: window length in frames
    wstep: window step in frames
    picks: channel picks
    flatten: boolean, see Returns section
    n_jobs: nubmer of cores to use, None = use all cores

    Returns
    -------
    if flatten==True:
        X_data: [epochs] x [windows] x [channels*freqs]
    else:
        X_data: [epochs] x [windows] x [channels] x [freqs]
    y_data: [epochs] x [windows]
    picks: feature indices to be used; use all if None

    TODO:
        Accept input as numpy array as well, in addition to Epochs object
    """

    if n_jobs is None:
        n_jobs = mp.cpu_count()
    if n_jobs > 1:
        logger.info('Opening a pool of %d workers' % n_jobs)
        pool = mp.Pool(n_jobs)

    # compute PSD from sliding windows of each epoch
    labels = epochs.events[:, -1]
    epochs_data = epochs.get_data()
    w_starts = np.arange(0, epochs_data.shape[2] - wlen, wstep)
    X_data = None
    y_data = None
    results = []
    for ep in np.arange(len(labels)):
        if n_jobs == 1:
            # no multiprocessing
            results.append(slice_win(epochs_data[ep], w_starts, wlen, psde, picks, ep))
        else:
            # parallel psd computation
            results.append(pool.apply_async(slice_win, [epochs_data[ep], w_starts, wlen, psde, picks, ep]))

    for ep in range(len(results)):
        if n_jobs == 1:
            r = results[ep]
        else:
            r = results[ep].get()  # windows x features
        X = r.reshape((1, r.shape[0], r.shape[1]))  # 1 x windows x features
        if X_data is None:
            X_data = X
        else:
            X_data = np.concatenate((X_data, X), axis=0)

        # speed comparison: http://stackoverflow.com/questions/5891410/numpy-array-initialization-fill-with-identical-values
        y = np.empty((1, r.shape[0]))  # 1 x windows
        y.fill(labels[ep])
        if y_data is None:
            y_data = y
        else:
            y_data = np.concatenate((y_data, y), axis=0)

    # close pool
    if n_jobs > 1:
        pool.close()
        pool.join()

    # flatten channel x frequency feature dimensions?
    if flatten:
        return X_data, y_data
    else:
        xs = X_data.shape
        nch = len(epochs.ch_names)
        return X_data.reshape(xs[0], xs[1], nch, int(xs[2] / nch)), y_data


def get_psd_feature(epochs_train, window, psdparam, picks=None, n_jobs=1):
    """
    input
    =====
    epochs_train: mne.Epochs object or list of mne.Epochs object.
    window: [t_start, t_end]. Time window range for computing PSD.
    psdparam: {fmin:float, fmax:float, wlen:float, wstep:int}.
              fmin, fmax in Hz, wlen in seconds, wstep in number of samples.
    picks: Channels to compute features from.
    
    output
    ======
    dict object containing computed features.
    """

    if type(window[0]) is list:
        sfreq = epochs_train[0].info['sfreq']
        wlen = []
        w_frames = []
        # multiple PSD estimators, defined for each epoch
        if type(psdparam) is list:
            '''
            TODO: implement multi-window PSD for each epoch
            assert len(psdparam) == len(window)
            for i, p in enumerate(psdparam):
                if p['wlen'] is None:
                    wl = window[i][1] - window[i][0]
                else:
                    wl = p['wlen']
                wlen.append(wl)
                w_frames.append(int(sfreq * wl))
            '''
            raise NotImplementedError('Multiple psd function not implemented yet.')
        # same PSD estimator for all epochs
        else:
            for i, e in enumerate(window):
                if psdparam['wlen'] is None:
                    wl = window[i][1] - window[i][0]
                else:
                    wl = psdparam['wlen']
                assert wl > 0
                wlen.append(wl)
                w_frames.append(int(sfreq * wl))
    else:
        sfreq = epochs_train.info['sfreq']
        wlen = window[1] - window[0]
        if psdparam['wlen'] is None:
            psdparam['wlen'] = wlen
        w_frames = int(sfreq * psdparam['wlen'])  # window length in number of samples(frames)

    psde = mne.decoding.PSDEstimator(sfreq=sfreq, fmin=psdparam['fmin'],\
                                     fmax=psdparam['fmax'], bandwidth=None, adaptive=False, low_bias=True,\
                                     n_jobs=1, normalization='length', verbose='WARNING')

    logger.info('\n>> Computing PSD for training set')
    if type(epochs_train) is list:
        X_all = []
        for i, ep in enumerate(epochs_train):
            X, Y_data = get_psd(ep, psde, w_frames[i], psdparam['wstep'], picks, n_jobs=n_jobs)
            X_all.append(X)
        # concatenate along the feature dimension
        # feature index order: window block x channel block x frequency block
        # feature vector = [window1, window2, ...]
        # where windowX = [channel1, channel2, ...]
        # where channelX = [freq1, freq2, ...]
        X_data = np.concatenate(X_all, axis=2)
    else:
        # feature index order: channel block x frequency block
        # feature vector = [channel1, channel2, ...]
        # where channelX = [freq1, freq2, ...]
        X_data, Y_data = get_psd(epochs_train, psde, w_frames, psdparam['wstep'], picks, n_jobs=n_jobs)

    # assign relative timestamps for each feature. time reference is the leading edge of a window.
    w_starts = np.arange(0, epochs_train.get_data().shape[2] - w_frames, psdparam['wstep'])
    t_features = w_starts / sfreq + psdparam['wlen'] + window[0]
    return dict(X_data=X_data, Y_data=Y_data, wlen=wlen, w_frames=w_frames, psde=psde, times=t_features)


def get_timelags(epochs, wlen, wstep, downsample=1, picks=None):
    """
    (DEPRECATED FUNCTION)
    Get concatenated timelag features

    TODO: Unit test.

    Params
    ======
    epochs: input signals
    wlen: window length (# time points) in downsampled data
    wstep: window step in downsampled data
    downsample: downsample signal to be 1/downsample length
    picks: ignored for now

    Returns
    =======
    X: [epochs] x [windows] x [channels*freqs]
    y: [epochs] x [labels]
    """

    wlen = int(wlen)
    wstep = int(wstep)
    downsample = int(downsample)
    X_data = None
    y_data = None
    labels = epochs.events[:, -1]  # every epoch must have event id
    epochs_data = epochs.get_data()
    n_channels = epochs_data.shape[1]
    # trim to the nearest divisible length
    epoch_ds_len = int(epochs_data.shape[2] / downsample)
    epoch_len = downsample * epoch_ds_len
    range_epochs = np.arange(epochs_data.shape[0])
    range_channels = np.arange(epochs_data.shape[1])
    range_windows = np.arange(epoch_ds_len - wlen, 0, -wstep)
    X_data = np.zeros((len(range_epochs), len(range_windows), wlen * n_channels))

    # for each epoch
    for ep in range_epochs:
        epoch = epochs_data[ep, :, :epoch_len]
        ds = qc.average_every_n(epoch.reshape(-1), downsample)  # flatten to 1-D, then downsample
        epoch_ds = ds.reshape(n_channels, -1)  # recover structure to channel x samples
        # for each window over all channels
        for i in range(len(range_windows)):
            w = range_windows[i]
            X = epoch_ds[:, w:w + wlen].reshape(1, -1)  # our feature vector
            X_data[ep, i, :] = X

        # fill labels
        y = np.empty((1, len(range_windows)))  # 1 x windows
        y.fill(labels[ep])
        if y_data is None:
            y_data = y
        else:
            y_data = np.concatenate((y_data, y), axis=0)

    return X_data, y_data


def feature2chz(x, fqlist, ch_names):
    """
    Label channel, frequency pair for PSD feature indices

    Params
    ======
    x: feature index
    fqlist: list of frequency bands
    ch_names: list of complete channel names

    Returns
    =======
    (channel, frequency)

    """

    x = np.array(x).astype('int64').reshape(-1)
    fqlist = np.array(fqlist).astype('float64')
    ch_names = np.array(ch_names)

    n_fq = len(fqlist)
    hz = fqlist[x % n_fq]
    ch = (x / n_fq).astype('int64')  # 0-based indexing

    return ch_names[ch], hz


def cva_features(datadir):
    """
    (DEPRECATED FUNCTION)
    """
    for fin in qc.get_file_list(datadir, fullpath=True):
        if fin[-4:] != '.gdf': continue
        fout = fin + '.cva'
        if os.path.exists(fout):
            logger.info('Skipping', fout)
            continue
        logger.info("cva_features('%s')" % fin)
        qc.matlab("cva_features('%s')" % fin)


def compute_features(cfg):
    '''
    Compute features using config specification.
    '''
    # Preprocessing, epoching and PSD computation
    ftrain = []
    for f in qc.get_file_list(cfg.DATADIR, fullpath=True):
        if f[-4:] in ['.fif', '.fiff']:
            ftrain.append(f)
    if len(ftrain) > 1 and cfg.CHANNEL_PICKS is not None and type(cfg.CHANNEL_PICKS[0]) == int:
        raise RuntimeError(
            'When loading multiple EEG files, CHANNEL_PICKS must be list of string, not integers because they may have different channel order.')
    raw, events = pu.load_multi(ftrain)
    if cfg.REF_CH is not None:
        raise NotImplementedError('Sorry! Channel re-referencing is under development!')
        pu.rereference(raw, cfg.REF_CH[1], cfg.REF_CH[0])
    if cfg.LOAD_EVENTS_FILE is not None:
        events = mne.read_events(cfg.LOAD_EVENTS_FILE)
    triggers = {cfg.tdef.by_value[c]:c for c in set(cfg.TRIGGER_DEF)}

    # Pick channels
    if cfg.CHANNEL_PICKS is None:
        chlist = [int(x) for x in pick_types(raw.info, stim=False, eeg=True)]
    else:
        chlist = cfg.CHANNEL_PICKS
    picks = []
    for c in chlist:
        if type(c) == int:
            picks.append(c)
        elif type(c) == str:
            picks.append(raw.ch_names.index(c))
        else:
            raise RuntimeError(
                'CHANNEL_PICKS has a value of unknown type %s.\nCHANNEL_PICKS=%s' % (type(c), cfg.CHANNEL_PICKS))
    if cfg.EXCLUDES is not None:
        for c in cfg.EXCLUDES:
            if type(c) == str:
                if c not in raw.ch_names:
                    logger.warning('Exclusion channel %s does not exist. Ignored.' % c)
                    continue
                c_int = raw.ch_names.index(c)
            elif type(c) == int:
                c_int = c
            else:
                raise RuntimeError(
                    'EXCLUDES has a value of unknown type %s.\nEXCLUDES=%s' % (type(c), cfg.EXCLUDES))
            if c_int in picks:
                del picks[picks.index(c_int)]
    if max(picks) > len(raw.ch_names):
        raise ValueError('"picks" has a channel index %d while there are only %d channels.' % (max(picks), len(raw.ch_names)))
    if hasattr(cfg, 'SP_CHANNELS') and cfg.SP_CHANNELS is not None:
        logger.warning('SP_CHANNELS parameter is not supported yet. Will be set to CHANNEL_PICKS.')
    if hasattr(cfg, 'TP_CHANNELS') and cfg.TP_CHANNELS is not None:
        logger.warning('TP_CHANNELS parameter is not supported yet. Will be set to CHANNEL_PICKS.')
    if hasattr(cfg, 'NOTCH_CHANNELS') and cfg.NOTCH_CHANNELS is not None:
        logger.warning('NOTCH_CHANNELS parameter is not supported yet. Will be set to CHANNEL_PICKS.')

    # Read epochs
    try:
        # Experimental: multiple epoch ranges
        if type(cfg.EPOCH[0]) is list:
            epochs_train = []
            for ep in cfg.EPOCH:
                epoch = Epochs(raw, events, triggers, tmin=ep[0], tmax=ep[1],
                    proj=False, picks=picks, baseline=None, preload=True,
                    verbose=False, detrend=None)
                # Channels are already selected by 'picks' param so use all channels.
                pu.preprocess(epoch, spatial=cfg.SP_FILTER, spatial_ch=None,
                              spectral=cfg.TP_FILTER, spectral_ch=None, notch=cfg.NOTCH_FILTER,
                              notch_ch=None, multiplier=cfg.MULTIPLIER, n_jobs=cfg.N_JOBS)
                epochs_train.append(epoch)
        else:
            # Usual method: single epoch range
            epochs_train = Epochs(raw, events, triggers, tmin=cfg.EPOCH[0],
                tmax=cfg.EPOCH[1], proj=False, picks=picks, baseline=None,
                preload=True, verbose=False, detrend=None)
            # Channels are already selected by 'picks' param so use all channels.
            pu.preprocess(epochs_train, spatial=cfg.SP_FILTER, spatial_ch=None,
                          spectral=cfg.TP_FILTER, spectral_ch=None, notch=cfg.NOTCH_FILTER, notch_ch=None,
                          multiplier=cfg.MULTIPLIER, n_jobs=cfg.N_JOBS)
    except:
        logger.exception('Problem while epoching.')
        if interactive:
            print('Dropping to a shell.\n')
            embed()
        raise RuntimeError

    label_set = np.unique(triggers.values())

    # Compute features
    if cfg.FEATURES == 'PSD':
        featdata = get_psd_feature(epochs_train, cfg.EPOCH, cfg.PSD, picks=None, n_jobs=cfg.N_JOBS)
    elif cfg.FEATURES == 'TIMELAG':
        '''
        TODO: Implement multiple epochs for timelag feature
        '''
        raise NotImplementedError('MULTIPLE EPOCHS NOT IMPLEMENTED YET FOR TIMELAG FEATURE.')
    elif cfg.FEATURES == 'WAVELET':
        '''
        TODO: Implement multiple epochs for wavelet feature
        '''
        raise NotImplementedError('MULTIPLE EPOCHS NOT IMPLEMENTED YET FOR WAVELET FEATURE.')
    else:
        raise NotImplementedError('%s feature type is not supported.' % cfg.FEATURES)

    featdata['picks'] = picks
    featdata['sfreq'] = raw.info['sfreq']
    featdata['ch_names'] = raw.ch_names
    return featdata
