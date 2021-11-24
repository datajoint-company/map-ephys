
import numpy as np
import datajoint as dj
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import statsmodels.api as sm
from scipy.stats import pearsonr

from pipeline import psth, psth_foraging, ephys, lab, ccf, histology, experiment, foraging_model
from pipeline.util import (_get_trial_event_times, _get_ephys_trial_event_times,
                           _get_units_hemisphere, _get_unit_independent_variable)
from . import foraging_model_plot


_plt_xlim = [-3, 3]

def _plot_spike_raster(ipsi, contra, vlines=[], shade_bar=None, ax=None, title='', xlim=_plt_xlim):
    if not ax:
        fig, ax = plt.subplots(1, 1)

    ipsi_tr = ipsi['raster'][1]
    for i, tr in enumerate(set(ipsi['raster'][1])):
        ipsi_tr = np.where(ipsi['raster'][1] == tr, i, ipsi_tr)

    contra_tr = contra['raster'][1]
    for i, tr in enumerate(set(contra['raster'][1])):
        contra_tr = np.where(contra['raster'][1] == tr, i, contra_tr)

    ipsi_tr_max = ipsi_tr.max() if ipsi_tr.size > 0 else 0

    ax.plot(ipsi['raster'][0], ipsi_tr, 'r.', markersize=1)
    ax.plot(contra['raster'][0], contra_tr + ipsi_tr_max + 1, 'b.', markersize=1)

    for x in vlines:
        ax.axvline(x=x, linestyle='--', color='k')
    if shade_bar is not None:
        ax.axvspan(shade_bar[0], shade_bar[0] + shade_bar[1], alpha=0.3, color='royalblue')

    ax.set_axis_off()
    ax.set_xlim(xlim)
    ax.set_title(title)


def _plot_psth(ipsi, contra, vlines=[], shade_bar=None, ax=None, title='', xlim=_plt_xlim):
    if not ax:
        fig, ax = plt.subplots(1, 1)

    ax.plot(contra['psth'][1], contra['psth'][0], 'b')
    ax.plot(ipsi['psth'][1], ipsi['psth'][0], 'r')

    for x in vlines:
        ax.axvline(x=x, linestyle='--', color='k')
    if shade_bar is not None:
        ax.axvspan(shade_bar[0], shade_bar[0] + shade_bar[1], alpha=0.3, color='royalblue')

    ax.set_ylabel('spikes/s')
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_xlim(xlim)
    ax.set_xlabel('Time (s)')
    ax.set_title(title)


def plot_unit_psth(unit_key, axs=None, title='', xlim=_plt_xlim):
    """
    Default raster and PSTH plot for a specified unit - only {good, no early lick, correct trials} selected
    condition_name_kw: list of keywords to match for the TrialCondition name
    """

    hemi = _get_units_hemisphere(unit_key)

    ipsi_hit_unit_psth = psth.UnitPsth.get_plotting_data(
        unit_key, {'trial_condition_name': f'good_noearlylick_{"left" if hemi == "left" else "right"}_hit'})

    contra_hit_unit_psth = psth.UnitPsth.get_plotting_data(
        unit_key, {'trial_condition_name':  f'good_noearlylick_{"right" if hemi == "left" else "left"}_hit'})

    ipsi_miss_unit_psth = psth.UnitPsth.get_plotting_data(
        unit_key, {'trial_condition_name': f'good_noearlylick_{"left" if hemi == "left" else "right"}_miss'})

    contra_miss_unit_psth = psth.UnitPsth.get_plotting_data(
        unit_key, {'trial_condition_name':  f'good_noearlylick_{"right" if hemi == "left" else "left"}_miss'})

    # get event start times: sample, delay, response
    periods, period_starts = _get_trial_event_times(['sample', 'delay', 'go'], unit_key, 'good_noearlylick_hit')

    fig = None
    if axs is None:
        fig, axs = plt.subplots(2, 2)

    # correct response
    _plot_spike_raster(ipsi_hit_unit_psth, contra_hit_unit_psth, ax=axs[0, 0],
                       vlines=period_starts,
                       title=title if title else f'Unit #: {unit_key["unit"]}\nCorrect Response', xlim=xlim)
    _plot_psth(ipsi_hit_unit_psth, contra_hit_unit_psth,
               vlines=period_starts, ax=axs[1, 0], xlim=xlim)

    # incorrect response
    _plot_spike_raster(ipsi_miss_unit_psth, contra_miss_unit_psth, ax=axs[0, 1],
                       vlines=period_starts,
                       title=title if title else f'Unit #: {unit_key["unit"]}\nIncorrect Response', xlim=xlim)
    _plot_psth(ipsi_miss_unit_psth, contra_miss_unit_psth,
               vlines=period_starts, ax=axs[1, 1], xlim=xlim)

    return fig


def _plot_spike_raster_foraging(ipsi, contra, offset=0, vlines=[], shade_bar=None, ax=None, title='', xlim=_plt_xlim):
    if not ax:
        fig, ax = plt.subplots(1, 1)

    contra_tr = contra['raster'][1]
    for i, tr in enumerate(contra['trials']):
        contra_tr = np.where(contra['raster'][1] == tr, i, contra_tr)

    ipsi_tr = ipsi['raster'][1]
    for i, tr in enumerate(ipsi['trials']):
        ipsi_tr = np.where(ipsi['raster'][1] == tr, i, ipsi_tr)

    contra_tr_max = contra_tr.max() if contra_tr.size > 0 else 0

    start_at = offset
    ax.plot(contra['raster'][0], contra_tr + start_at + 1, 'b.', markersize=1)
    ax.axhline(y=start_at, linestyle='-', color='k')
    start_at += contra_tr_max

    ax.plot(ipsi['raster'][0], ipsi_tr + start_at, 'r.', markersize=1)
    ax.axhline(y=start_at, linestyle='-', color='k')

    for x in vlines:
        ax.axvline(x=x, linestyle='--', color='k')
    ax.axvline(x=0, linestyle='-', color='k', lw=1.5)

    if shade_bar is not None:
        ax.axvspan(shade_bar[0], shade_bar[0] + shade_bar[1], alpha=0.3, color='royalblue')

    # ax.set_axis_off()
    ax.set_xlim(xlim)
    ax.set_title(title)


def _plot_psth_foraging(ipsi, contra, vlines=[], shade_bar=None, ax=None, title='', label='', xlim=_plt_xlim, **karg):
    if not ax:
        fig, ax = plt.subplots(1, 1)

    ax.plot(contra['bins'], contra['psth'], 'b', label='contra ' + label, **karg)
    ax.plot(ipsi['bins'], ipsi['psth'], 'r', label='ipsi ' + label, **karg)

    for x in vlines:
        ax.axvline(x=x, linestyle='--', color='k')
    ax.axvline(x=0, linestyle='-', color='k', lw=1.5)

    if shade_bar is not None:
        ax.axvspan(shade_bar[0], shade_bar[0] + shade_bar[1], alpha=0.3, color='royalblue')

    ax.set_ylabel('spikes/s')
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_xlim(xlim)
    ax.set_xlabel('Time (s)')
    ax.set_title(title)


def _plot_psths(psths, kargs=[], vlines=[], shade_bar=None, ax=None, title='', label='', xlim=_plt_xlim):
    """
    Plot arbitrary number of psths
    """
    if not ax:
        fig, ax = plt.subplots(1, 1)

    if not kargs:
        kargs = [{'color': 'b'}] * len(psths)

    for psth, karg in zip(psths, kargs):
        ax.plot(psth['bins'], psth['psth'], **karg)

    for x in vlines:
        ax.axvline(x=x, linestyle='--', color='k')
    ax.axvline(x=0, linestyle='-', color='k', lw=1.5)

    if shade_bar is not None:
        ax.axvspan(shade_bar[0], shade_bar[0] + shade_bar[1], alpha=0.3, color='royalblue')

    ax.set_ylabel('spikes/s')
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.set_xlim(xlim)
    ax.set_xlabel('Time (s)')
    ax.set_title(title)


def _set_same_horizonal_aspect_ratio(axs, xlims, gap=0.02):
    """
    Scale axis widths to keep the same horizonal aspect ratio across axs
    assuming axs are already from left to right
    """
    n = len(axs)
    leftmost, b, _, h = axs[0].get_position().bounds
    rightmost = np.array(axs[-1].get_position().bounds)[[0, 2]].sum()  # left + width
    spans = np.array([t_max - t_min for (t_min, t_max) in xlims])
    scaled_widths = (rightmost - leftmost - gap * (n-1)) / sum(spans) * spans
    scaled_lefts = leftmost + np.cumsum([0] + list(scaled_widths[:-1])) + gap * np.arange(n)

    for ax, l, w in zip(axs, scaled_lefts, scaled_widths):
        ax.set_position([l, b, w, h])


def plot_unit_psth_choice_outcome(unit_key={'subject_id': 473361, 'session': 47, 'insertion_number': 1, 'clustering_method': 'kilosort2', 'unit': 541},
                                  align_types=['trial_start', 'go_cue', 'first_lick_after_go_cue', 'iti_start', 'next_trial_start'],
                                  if_raster=True, if_exclude_early_lick=False,
                                  axs=None, title=''):
    """Plot psth grouped by (choice x outcome) for the foraging task.
     
    In general, PSTH is specificied by two things: trial conditions and alignment types. 

    Here, trial conditions include all four combinitions of choice (ipsi or contra) and outcome (hit or miss), 
    whereas align types are defined by the user. See `psth_foraging.AlignType`
    
    Parameters
    ----------
    unit_key : [type]
        [description]
    align_types : list, optional
        list of align_type_name in psth_foraging.AlignType, by default ['trial_start', 'go_cue', 'first_lick_after_go_cue', 'iti_start', 'next_trial_start']
    if_raster : bool, optional
        whether to plot raster, by default True
    axs : [type], optional
        [description], by default None
    title : str, optional
        [description], by default ''
    if_exclude_early_lick : bool, optional
        whether to exclude early licks, by default False

    Returns
    -------
    [type]
        [description]
        
    """

    # for (the very few) sessions without zaber feedback signal, use 'bitcodestart' with manual correction (see compute_unit_psth_and_raster)
    if not ephys.TrialEvent & unit_key & 'trial_event_type = "zaberready"':
        align_types = [a + '_bitcode' if 'trial_start' in a else a for a in align_types]

    hemi = _get_units_hemisphere(unit_key)
    ipsi = "L" if hemi == "left" else "R"
    contra = "R" if hemi == "left" else "L"
    no_early_lick = '_noearlylick' if if_exclude_early_lick else ''

    fig = None
    if axs is None:
        fig = plt.figure(figsize=(len(align_types)/5 * 25, (1+if_raster)/2 * 9))
        axs = fig.subplots(1 + if_raster, len(align_types), sharey='row', sharex='col')
        axs = np.atleast_2d(axs).reshape((1+if_raster, -1))
        plt.subplots_adjust(top=0.8)  

        # Add unit info
        unit_info = (f'{(lab.WaterRestriction & unit_key).fetch1("water_restriction_number")}, '
                    f'{(experiment.Session & unit_key).fetch1("session_date")}, '
                    f'imec {unit_key["insertion_number"]-1}\n'
                    f'Unit #: {unit_key["unit"]}, '
                    f'{(((ephys.Unit & unit_key) * histology.ElectrodeCCFPosition.ElectrodePosition) * ccf.CCFAnnotation).fetch1("annotation")}'
                    )
        fig.text(0.1, 0.9, unit_info)              

    xlims = []

    for ax_i, align_type in enumerate(align_types):

        offset, xlim = (psth_foraging.AlignType & {'align_type_name': align_type}).fetch1('trial_offset', 'xlim')
        xlims.append(xlim)

        # align_trial_offset is added on the get_trials, which effectively
        # makes the psth conditioned on the previous {align_trial_offset} trials
        ipsi_hit_trials = psth_foraging.TrialCondition.get_trials(f'{ipsi}_hit{no_early_lick}', offset) & unit_key
        ipsi_hit_unit_psth = psth_foraging.compute_unit_psth_and_raster(unit_key, ipsi_hit_trials, align_type)

        contra_hit_trials = psth_foraging.TrialCondition.get_trials(f'{contra}_hit{no_early_lick}', offset) & unit_key
        contra_hit_unit_psth = psth_foraging.compute_unit_psth_and_raster(unit_key, contra_hit_trials, align_type)

        ipsi_miss_trials = psth_foraging.TrialCondition.get_trials(f'{ipsi}_miss{no_early_lick}', offset) & unit_key
        ipsi_miss_unit_psth = psth_foraging.compute_unit_psth_and_raster(unit_key, ipsi_miss_trials, align_type)

        contra_miss_trials = psth_foraging.TrialCondition.get_trials(f'{contra}_miss{no_early_lick}', offset) & unit_key
        contra_miss_unit_psth = psth_foraging.compute_unit_psth_and_raster(unit_key, contra_miss_trials, align_type)

        # --- plot psths (all 4 in one plot) ---
        ax_psth = axs[1 if if_raster else 0, ax_i]
        period_starts_hit = _get_ephys_trial_event_times(align_types,
                                                         align_to=align_type,
                                                         trial_keys=psth_foraging.TrialCondition.get_trials(f'LR_hit{no_early_lick}') & unit_key,
                                                         # cannot use *_hit_trials because it could have been offset
                                                         )
        # _, period_starts_miss = _get_ephys_trial_event_times([trialstart, 'go', 'choice', 'trialend'],
        #                                                   ipsi_miss_trials.proj() + contra_miss_trials.proj(), align_event=align_event_type)

        _plot_psth_foraging(ipsi_hit_unit_psth, contra_hit_unit_psth,
                   vlines=period_starts_hit, ax=ax_psth, xlim=xlim, label='rew', linestyle='-')

        _plot_psth_foraging(ipsi_miss_unit_psth, contra_miss_unit_psth,
                   vlines=[], ax=ax_psth, xlim=xlim, label='norew', linestyle = '--')

        ax_psth.set(title=f'{align_type}')
        if ax_i > 0:
            ax_psth.spines['left'].set_visible(False)
            ax_psth.get_yaxis().set_visible(False)

        # --- plot rasters (optional) ---
        if if_raster:
            ax_raster = axs[0, ax_i]
            _plot_spike_raster_foraging(ipsi_hit_unit_psth, contra_hit_unit_psth, ax=ax_raster,
                                           offset=0,
                                           vlines=period_starts_hit,
                                           title='', xlim=xlim)
            _plot_spike_raster_foraging(ipsi_miss_unit_psth, contra_miss_unit_psth, ax=ax_raster,
                                           offset=len(ipsi_hit_unit_psth['trials']) + len(contra_hit_unit_psth['trials']),
                                           vlines=[],
                                           title='', xlim=xlim)
            ax_raster.invert_yaxis()

    # Scale axis widths to keep the same horizontal aspect ratio (time) across axs
    _set_same_horizonal_aspect_ratio(axs[1 if if_raster else 0, :], xlims)
    if if_raster:
        _set_same_horizonal_aspect_ratio(axs[0, :], xlims)
    ax_psth.legend(fontsize=8)

    return fig


def plot_unit_psth_latent_variable_quantile(unit_key={'subject_id': 473361, 'session': 47, 'insertion_number': 1, 'clustering_method': 'kilosort2', 'unit': 541},
                                            model_id=11, n_quantile=5,
                                            align_types=['trial_start', 'go_cue', 'first_lick_after_go_cue', 'iti_start', 'next_trial_start'],
                                            latent_variable='contra_action_value',
                                            axs=None, title=''):
    """
    (for foraging task) Plot psth grouped by quantiles of latent variable from behavioral model fitting

    :param unit_key:
    :param model_id:
    :param n_quantile: numer of quantiles to split
    :param align_types: psth_foraging.AlignType
    :param latent_variable: 'contra_action_value' (default), 'ipsi_choice_prob', 'relative_action_value (contra - ipsi)', 'total_action_value', 'contra_choice_kernel', etc.
    :param axs:
    :param title:
    :return:
    """

    # for (the very few) sessions without zaber feedback signal, use 'bitcodestart' with manual correction (see compute_unit_psth_and_raster)
    if not ephys.TrialEvent & unit_key & 'trial_event_type = "zaberready"':
        align_types = [a + '_bitcode' if 'trial_start' in a else a for a in align_types]

    # Fetch data
    df = _get_unit_independent_variable(unit_key, var_name=latent_variable, model_id=model_id).astype(float)

    # Cut choice probabilities into quantiles
    if any(np.isnan(df[latent_variable])):
        print('No latent variable data or too few unique values')
        return
    df['quantile_rank'] = pd.qcut(df[latent_variable], n_quantile, labels=False, duplicates='drop')
    n_quantile = len(df['quantile_rank'].unique())    # Just in case qcut has 'dropped'

    fig = None
    if axs is None:
        fig = plt.figure(figsize=(len(align_types)/5 * 25, 5))
        axs = fig.subplots(1, len(align_types), sharey='row', sharex='col')
        axs = np.atleast_2d(axs).reshape((1, -1))
        plt.subplots_adjust(top=0.8)
            # Add unit and model info
        latent_var_desc = (psth_foraging.IndependentVariable & {'var_name': latent_variable}).fetch1('desc')
        unit_info = (f'{(lab.WaterRestriction & unit_key).fetch1("water_restriction_number")}, '
                    f'Session {(experiment.Session & unit_key).fetch1("session")}, {(experiment.Session & unit_key).fetch1("session_date")}, '
                    f'imec {unit_key["insertion_number"]-1}\n'
                    f'Unit #{unit_key["unit"]}, '
                    f'{(((ephys.Unit & unit_key) * histology.ElectrodeCCFPosition.ElectrodePosition) * ccf.CCFAnnotation).fetch1("annotation")}\n'
                    f'=== Grouped by: {latent_var_desc} ==='
                    )
        id, model_notation, desc, accuracy, n = (foraging_model.FittedSessionModel * foraging_model.Model.proj(..., '-n_params') & unit_key & {'model_id': model_id}).fetch1(
            'model_id', 'model_notation', 'desc', 'cross_valid_accuracy_test', 'n_trials')
        fig.text(0.1, 0.9, unit_info)
        fig.text(0.5, 0.9, f'model <{id}> {model_notation}\n{desc}\n{n} trials, prediction accuracy (cross-valid) = {accuracy}')

    kargs = [{'color': 'b' if 'contra' in latent_variable else 'r' if 'ipsi' in latent_variable else 'k',
              'alpha': np.linspace(0.2, 1, n_quantile)[rank],
              'label': f'quantile {rank + 1}'} for rank in range(n_quantile)]
    xlims = []

    # -- For each align type --
    for ax_i, align_type in enumerate(align_types):
        offset, xlim = (psth_foraging.AlignType & {'align_type_name': align_type}).fetch1('trial_offset', 'xlim')
        xlims.append(xlim)

        # -- For each quantile group --
        psths = []
        for rank in range(n_quantile):
            # Group trials
            trial_num = df[df.quantile_rank == rank].copy()
            trial_num.trial += offset    # Model and ephys trial number are now aligned. No need for additional offset=-1 here
                                         #    behavior & ephys:   -->  ITI(t-1) --> |  --> choice (t), reward(t)         --> ITI (t) -->       |
                                         #  model:      Q(t-1) --> choice prob(t-1) | --> choice (t), reward(t)  --> Q(t) --> choice prob (t)  |

            # Get psths
            this_trials = (experiment.BehaviorTrial & unit_key & trial_num).proj()
            psths.append(psth_foraging.compute_unit_psth_and_raster(unit_key, this_trials, align_type))

        # -- Plot psths for this align type --
        ax_psth = axs[0, ax_i]
        period_starts_all = _get_ephys_trial_event_times(align_types,
                                                         align_to=align_type,
                                                         trial_keys=experiment.BehaviorTrial & unit_key & df,  # From all trials
                                                         )

        _plot_psths(psths, kargs, ax=ax_psth, xlim=xlim, vlines=period_starts_all)
        ax_psth.set(title=f'{align_type}')

    _set_same_horizonal_aspect_ratio(axs[0, :], xlims)
    ax_psth.legend(fontsize=10, ncol=2)

    return fig


def plot_unit_period_tuning(unit_key={'subject_id': 473361, 'session': 47, 'insertion_number': 1, 'clustering_method': 'kilosort2', 'unit': 541},
                            period='iti_all',
                            independent_variable = ['contra_action_value', 'ipsi_action_value', 'rpe'],
                            model_id=None):
    """
    Plot multivariate linear regression of firing rate of given unit, in given period, using given independent variables
    @param unit_key:
    @param period:
    @param independent_variable:
    @param model_id: if None, use the best aic model in all models
    @return: figure
    """

    # Period activity
    period_activity = psth_foraging.compute_unit_period_activity(unit_key, period)

    # Latent variables
    if model_id is None:
        model_id = (foraging_model.FittedSessionModelComparison.BestModel & unit_key & 'model_comparison_idx=0').fetch1('best_aic')
    all_iv = _get_unit_independent_variable(unit_key, model_id=model_id)

    #TODO Align ephys event with behavior using bitcode! (and save raw bitcodes)
    trial = all_iv.trial   # Original trial numbers but without ignored trials
    trial_with_ephys = trial <= max(period_activity['trial'])
    trial = trial[trial_with_ephys]   # Truncate behavior trial to max ephys length (this assumes the first trial is aligned, see ingest.ephys)
    all_iv = all_iv[trial_with_ephys]  # Also truncate all ivs
    firing = period_activity['firing_rates'][trial - 1]   # Align ephys trial and model trial (e.g., no ignored trials in model fitting)

    # -- Plot all variables over trial --
    fig1, axs = plt.subplots(len(independent_variable) + 2, 1, sharex=True, dpi=150, figsize=(11, 14))
    plt.subplots_adjust(right=0.8, hspace=0.2)

    # Choice history (including ignored trials)
    foraging_model_plot.plot_session_fitted_choice(unit_key, specified_model_ids=model_id, ax=axs[0], remove_ignored=False)

    # Period firing rate
    trial_with_nan = np.arange(np.min(trial), np.max(trial + 1))
    firing_with_nan = np.empty(trial_with_nan.shape)
    firing_with_nan[:] = np.nan
    firing_with_nan[trial - 1] = firing
    axs[1].plot(trial_with_nan, firing_with_nan, 'o-', ms=5)
    axs[1].set_title(f'Mean firing rate in epoch: {period} (spikes / s)')

    # Independent variables
    for ax, iv in zip(axs[2:], independent_variable):
        # To show gaps in ignored trials
        iv_with_nan = np.empty(trial_with_nan.shape)
        iv_with_nan[:] = np.nan
        iv_with_nan[trial - 1] = all_iv[iv] 
        ax.plot(trial_with_nan, iv_with_nan, 'k')
        ax.set_title(iv)
        ax.set_xlabel('Original trial number')

    for ax in axs.flat: ax.label_outer()

    # -- Plot linear regression --
    y = pd.DataFrame({f'{period} firing': firing})
    x = all_iv[independent_variable].astype(float)
    result, fig2 = linear_fit(y, x, if_plot=True)

    return fig1, fig2


def linear_fit(y, x, intercept=True, if_plot=False):
    """
    Simple linear regression Y = [b0] + b1 * x1 + b2 * x2 + ...
    @param y: samples
    @param x: [samples * independent variables] or DataFrame
    @param intercept:
    @param if_plot: whether if_plot
    @return: Dict
    """
    model = sm.OLS(y, sm.add_constant(x) if intercept else x)
    model_fit = model.fit()

    if if_plot:
        n_x = x.shape[1]

        fig = plt.figure(dpi=150, figsize=(10, 5))
        axs = np.atleast_1d(fig.subplots(1, n_x, sharey=True))
        for ax, xx, xname, para, p, t in zip(axs,
                                             model.exog[:, int(intercept):].T,
                                             model.exog_names[int(intercept):],
                                             model_fit.params[int(intercept):],
                                             model_fit.pvalues[int(intercept):],
                                             model_fit.tvalues[int(intercept):]):

            # ax.plot(xx, y, 'o')
            # ax.plot(np.sort(xx), model_fit.predict()[np.argsort(xx)], 'k-', lw=5 if p < 0.05 else 0.5, label=f'$p$ = {p:.2g}\n'
            #                                                                         f'$t$ = {t:.3g}\n'
            #                                                                         f'$r^2$ = {model_fit.rsquared_adj:.2g}')
            (r_pearson, p_pearson) = pearsonr(xx, y.values.flatten())
            sns.regplot(x=xx, y=y, ax=ax, truncate=False,
                        scatter_kws={'alpha': 0.3, 's': 20},
                        line_kws={'lw': 3, 'ls': '-'} if p < 0.05 else {'lw': 1, 'ls': ':'},
                        label=f'Pearson $r$ = {r_pearson:.3g}\n$p$ = {p_pearson:.2g}'
                        )

            ax.set_title(label=f'$p$ = {p:.2g}, $t$ = {t:.3g}', fontsize=13)
            ax.set(xlabel=xname, ylabel=model.endog_names)
            ax.set_aspect(1.0 / ax.get_data_ratio(), adjustable='box')
            ax.legend(handlelength=0, handletextpad=0, fancybox=True, fontsize=10, loc='upper right')

        axs[0].set_title(f'Multivariate linear model: $r^2$ = {model_fit.rsquared_adj:.2g}\n' + axs[0].get_title(), fontsize=13)
        for a in axs: a.label_outer()

    return dict(r_2_adj=model_fit.rsquared_adj, p=model_fit.pvalues, t=model_fit.tvalues, para=model_fit.params), fig
