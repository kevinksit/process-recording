import pandas as pd
import numpy as np
import xarray as xr

def min_subtract(traces):
    return traces - traces.min(axis=1).reshape(-1,1) + 1 # to avoid 0, added 02Jan2024 KS

def baseline_subtract(cut_traces, baseline_length):
    baseline = cut_traces[:,:,:baseline_length].mean(axis=2)
    psths_baselined = cut_traces - baseline.reshape(*cut_traces.shape[:2], 1)
    return psths_baselined

def percentile_dff(traces, q=10):
    f0s = np.percentile(traces, q, axis=1, keepdims=true)
    traces = (traces-f0s)/f0s
    return traces

def rolling_baseline_dff(traces, q=10, window=300):
    f0s = pd.dataframe(traces.t).rolling(window, min_periods=1, center=true).quantile(q/100)
    f0s = f0s.values.t
    traces = (traces-f0s)/f0s
    return traces

def make_trialwise(traces, trial_lengths):
    traces = np.split(traces, np.cumsum(trial_lengths[:-1]), axis=1)
    shortest = min(map(lambda x: x.shape[1], traces))
    traces = np.array([a[:, :shortest] for a in traces])
    return traces

def stim_align_trialwise(trialwise_traces, times_trial, new_start):
    """
    aligns to stimulus onset that is synchronous for all cells (eg. visual stimulus). takes
    trialwise data (eg. trial x cell x time array) and rolls data around to other side array.
    use stim_align_cellwise for stimuli that are specific to each cell (eg. holographic stimulus
    like a stim-test).

    args:
        trialwise_traces (array-like): trial x cell x time array of traces data, typicall from make_trialwise
        times (array-like): list of stim times for each cell, must match exactly, not sure how it
                            handles nans yet...
        new_start (int): frame number where the psths will be aligned to
    """
    psth = np.zeros_like(trialwise_traces)
    
    for i in range(trialwise_traces.shape[0]):
        psth[i,:,:] = np.roll(trialwise_traces[i,:,:], -int(times_trial[i])+new_start, axis=1)
        
    return psth
    
def stim_align_cellwise(trialwise_traces, times_cell, new_start):
    """
    make stim-aligned psths from trialwise data (eg. trial x cell x time array). the 
    advantage of doing it this way (trialwise) is the trace for each cell gets rolled around
    to the other side of the array, thus eliminating the need for nan padding.

    args:
        trialwise_traces (array-like): trial x cell x time array of traces data, typicall from make_trialwise
        times (array-like): list of stim times for each cell, must match exactly, not sure how it
                            handles nans yet...
        new_start (int): frame number where the psths will be aligned to
    """
    psth = np.zeros_like(trialwise_traces)

    for i in range(trialwise_traces.shape[0]):
        psth[i,:,:] = np.array([np.roll(cell_trace, -amt+new_start) for cell_trace, amt in zip(trialwise_traces[i,:,:], times_cell.astype(int))])

    return psth

def cut_psths(stim_aligned, length=25):
    cut_psths = stim_aligned[:,:,:length]
    return cut_psths

def make_dataframe(traces, fr, stim_id, stim_name='trial_id'):
    # make the dataframe
    df = xr.dataarray(traces.t).to_dataset(dim='dim_0').to_dataframe()
    df = df.reset_index(level=['dim_1', 'dim_2'])
    df = pd.melt(df, ('dim_1', 'dim_2'))
    df = df.rename(columns = {'dim_1':'cell', 'dim_2':'trial', 'variable':'frame', 'value':'df'})
    df['time'] = df['frame']/fr

    # add stims/trial ids
    df = df.join(pd.series(stim_id, name=stim_name, dtype=int), on='trial')
    return df

def df_add_trialwise(df, vals, col_name, **kwargs):
    return _df_add(df, vals, col_name, on='trial', **kwargs)

def df_add_cellwise(df, vals, col_name, **kwargs):
    return _df_add(df, vals, col_name, on='cell', **kwargs)

def _df_add(df, vals, col_name, on, **kwargs):
    if col_name in df:
        df = df.drop([col_name], axis=1)
    df = df.join(pd.series(vals, name=col_name, **kwargs), on=on)
    return df

def stims2names(unique_ids, trialwise_names):
    return np.array(list(map(lambda x: unique_ids[x], trialwise_names)))

def unravel(traces: np.ndarray):
    """go from trials x time x cell to cells x total time."""
    return traces.transpose((1, 0, 2)).reshape((traces.shape[1], -1))

def reravel(traces: np.ndarray, length):
    return traces.reshape((traces.shape[0], -1, length)).transpose((1, 0, 2))

def roll_ind(a, r):
    rows, column_indices = np.ogrid[:a.shape[0], :a.shape[1]]

    r[r < 0] += a.shape[1]
    column_indices = column_indices - r[:, np.newaxis]

    return a[rows, column_indices]