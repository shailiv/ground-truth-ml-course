import json
F = json.load(open('data/facts.json'))
P = print
S = F['slices']
for k in ('by_size', 'by_account_manager', 'by_tenure'):
    for row in S[k]:
        P('SLICE', {a: row[a] for a in ('slice', 'n', 'churn_rate', 'churners', 'auc', 'flagged_in_top_400', 'precision_when_flagged', 'recall', 'avg_predicted', 'avg_actual', 'spend_lost_to_churn', 'spend_lost_that_was_flagged')})
P('RANK', S['rank_by_what'])
N = F['noise']
P('MOE', N['margin_of_error_for_a_churn_rate']['rows'])
P('AA', N['aa_test']['by_group_size'])
for c in N['comparisons']:
    P('CMP', c)
for row in F['learning_curve']['rows']:
    P('LC', row)
U = F['uplift']
P('UP exp', U['experiment_readout'])
P('UP quad', U['four_kinds_of_advertiser_share'])
for k, v in U['policies_call_400'].items():
    P('UP400', k, v)
for k, v in U['policies_call_800'].items():
    P('UP800', k, v)
P('UP who risk', U['who_the_risk_list_calls'], 'uplift', U['who_the_uplift_list_calls'])
T = F['time_to_event']
P('TTE', {k: T[k] for k in ('n', 'churned_so_far', 'share_censored', 'naive_average_lifetime_of_those_who_churned_weeks', 'naive_share_churned')})
P('KM', T['kaplan_meier']['weeks'], T['kaplan_meier']['share_still_active'], T['kaplan_meier']['median_lifetime_weeks'], T['kaplan_meier']['true_median_lifetime_weeks'])
P('RISKQ', T['risk_by_quarter_of_tenure']['rows'])
P('SHORT', T['the_classification_shortcut'])
L = F['panel_leak']
P('PANEL rf', L['random_forest'], 'lr', L['logistic_regression'], 'rf+id', L['random_forest_with_the_id_column_left_in'], L['positive_rate'])
D = F['dirty_tables']
for k, v in D.items():
    P('DIRTY', k, {a: b for a, b in v.items() if a not in ('what', 'the_check')})
B = F['before_after']
P('DID', B['averages'], B['three_answers'], B['the_assumption'], {k: v for k, v in B['when_the_assumption_fails'].items() if k not in ('what', 'reading')})
P('DID weekly', B['weekly_hit_rate']['got_the_flow'], B['weekly_hit_rate']['comparison'])
