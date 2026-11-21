import json, sys
F = json.load(open('data/facts.json'))
P = lambda *a: print(*a)
d = F['data']
P('DATA', {k: d[k] for k in ('n_train', 'n_gap', 'n_test', 'churn_rate', 'churn_rate_train', 'churn_rate_test', 'churners_test', 'churn_by_month', 'tracking_rate', 'hit_goal_rate_tracked', 'video_adoption_rate', 'n_feature_columns')})
P('BY', {k: {a: b['churn'] for a, b in v.items()} for k, v in F['churn_by'].items()})
P('BASE', F['baseline'])
for k in ('logreg', 'tree', 'forest', 'boosting'):
    P(k.upper(), F[k]['test'], 'train', F[k].get('train_auc'))
P('BEST POSSIBLE', F['logreg']['best_possible_auc'])
P('COEFS', [(c['feature'], c['coef'], c['odds_ratio'], c.get('avg_probability_shift_pts')) for c in F['logreg']['coefs'][:12]])
P('BOOST', F['boosting']['params'], F['boosting']['tuning']['best'], F['boosting']['tuning']['worst'], F['boosting']['untuned'])
P('CV', F['cv']['logreg'], F['cv']['boosting'])
P('UNC', {k: v for k, v in F['uncertainty'].items() if k != 'method'})
P('SPLIT', {k: v for k, v in F['split'].items() if k != 'note'})
P('DRIFT', {k: F['drift'][k] for k in ('auc_by_month', 'gaming_churn_by_month', 'gaming_may', 'gaming_jun', 'non_gaming_jun', 'all_jun')})
P('LEAK', {k: v for k, v in F['leakage'].items() if k not in ('why', 'leak_metrics_at_half')})
P('THR', [(t['threshold'], t['flagged'], t['tp'], t['fp'], t['fn'], t['precision'], t['recall'], t['accuracy']) for t in F['thresholds']])
P('LIFT', [(x['decile'], x['churners'], x['churn_rate'], x['lift'], x['cum_capture']) for x in F['lift'][:4]])
P('TOPK', F['top_k'])
P('CAL', F['calibration']['logreg'], F['calibration']['overall'], F['calibration']['on_training_months'])
P('TABLE', [(m['model'], m['test_auc'], m['train_auc'], m['top_200_churners']) for m in F['model_table']])
P('GROUPS', [(a['added'], a['test_auc']) for a in F['feature_groups']['cumulative']], F['feature_groups']['each_group_alone'], F['feature_groups']['spread_across_feature_sets'], F['feature_groups']['spread_across_algorithms'])
P('IMP', [(i['feature'], i['auc_drop']) for i in F['importance']['rows'][:7]], [(g['group'], g['auc_drop']) for g in F['importance']['grouped']['rows']])
P('EXPL', F['explain_examples']['average_advertiser_probability'], [(e['label'], e['advertiser_id'], e['predicted'], e['churned'], e['top_pushes'][:4]) for e in F['explain_examples']['examples']])
P('EARLY', F['early_warning'])
E = F['economics']
P('ECON', E['break_even_probability'], E['table'], E['list_from_the_rule'], E['best_list_in_hindsight'], E['default_cutoff_half'])
h = F['happy']
P('HAPPY', h['n_tracked'], h['hit_goal_rate'], h['n_happy'], h['n_unhappy'])
P(' naive', {k: (v['diff_pts'], v['ci95_pts'], v['adoption']) for k, v in h['naive'].items()})
P(' adj', h['adjusted_pts'])
P(' truth', {k: v['effect_pts'] for k, v in h['truth'].items()}, h['truth']['fresh_creatives'])
P(' removed', h['share_of_naive_gap_removed_by_adjusting'])
P('TRACK', {k: v for k, v in F['tracking_story'].items() if k not in ('why', 'adjusted_for')})
P('BADCTRL', {k: v for k, v in F['bad_controls'].items() if k not in ('lesson', 'how_it_works_in_the_simulation', 'question')})
s = F['segments']
P('SEG', [(x['segment'], x['share'], x['churn'], x['uses_auto_bidding'], x['has_conversion_tracking'], x['creative_refresh_days'], x['active_days_28']) for x in s['segments']])
hc = s['honesty_checks']
P(' honesty', hc['agreement_with_a_plain_group_by']['adjusted_rand_index'], hc['stability'], hc['without_the_two_flags']['agreement_with_the_first_clustering'], [(x['share'], x['churn']) for x in hc['without_the_two_flags']['segments']], hc['simple_business_segments'])
v = F['video']
P('VIDEO', v['adoption_rate_test'], v['adopters_test'], [(m['model'], m['test_auc'], m['top_200_adopters']) for m in v['scoreboard']], v['random_200_expected'], v['tuning']['best'], v['boosting_minus_logistic_auc'], v['boosting_minus_logistic_95'], v['boosting_minus_logistic_with_flags_95'], v['compare_with_churn'])
