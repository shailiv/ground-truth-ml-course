import json
F = json.load(open('data/facts.json'))
P = print
R = F['regression']
P('REG', {k: R[k] for k in ('target_mean', 'target_median', 'target_p99', 'share_zero', 'total_actual')})
for k, v in R['models'].items():
    P('  ', k.ljust(46), v['mae'], v['rmse'], v['r2'], v['median_abs_error'], v['wape'], v['bias'], v['total_error'])
P(' winners', R['winner_depends_on_the_metric'])
for x in R['paired_differences']:
    P('  PAIR', x['a'], '-', x['b'], x['mae_a_minus_mae_b'], x['ci95'], '->', x['clear_winner'])
P(' typ/avg', {k: v for k, v in R['typical_vs_average'].items() if k not in ('what', 'but_on_mae')})
P(' logeff', [(e['feature'], e['pct_change_in_spend'], e['per']) for e in R['log_model']['effects']])
P(' tiers', R['by_size_tier']['rows'])
P(' conc', R['error_concentration'])
P(' worst', R['worst_misses'][:2])
P(' stayers', {k: v for k, v in R['stayers_only'].items() if k not in ('what', 'noise_floor_is')})
P('DIST', {k: v for k, v in F['distance'].items() if k not in ('what', 'why_raw_fails', 'note')})
P('PCA', {k: v for k, v in F['pca'].items() if k != 'caveat'})
P('NN', F['neural_net'])
T = F['forecast']
P('FC', T['growth_2025_vs_2024'], T['weekday_index'], T['month_index'])
for m, v in T['backtest']['methods'].items():
    P('  BT', m.ljust(40), v)
P('  BT with incidents', {m: v['mape'] for m, v in T['backtest']['with_incidents_left_in'].items()})
P('  reg', T['regression_model'])
P('  int', T['interval'])
P('  shift', T['level_shift']['months'], T['level_shift']['average_of_last_4_same_weekdays'], T['level_shift']['trend_plus_seasonality_regression'])
P('  year', {k: v for k, v in T['one_year_ahead'].items() if k != 'why'})
P('  shuf', {k: v for k, v in T['shuffled_folds_vs_backtest'].items() if k != 'what'})
S = F['series_anomalies']
P('SA', S['days'], S['incident_days'], S['known_holiday_days_in_window'])
P('  naive', {k: v for k, v in S['naive_rule'].items() if k != 'rule'})
for x in S['seasonal_baseline']['by_threshold']:
    P('  seas', x)
for x in S['seasonal_baseline']['by_threshold_ignoring_known_holidays']:
    P('  seas-noholiday', x)
for x in S['seven_day_average']['by_threshold']:
    P('  roll7', x)
P('  leak flagged after days', S['seven_day_average']['days_until_the_slow_leak_is_flagged_at_k3'])
