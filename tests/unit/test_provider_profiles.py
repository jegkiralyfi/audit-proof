from packages.llm.profiles import canonical_provider_id, export_provider_profiles, recommended_provider_for_lane


def test_provider_profiles_export_contains_known_profiles():
    payload = export_provider_profiles()
    ids = {item['provider_id'] for item in payload['profiles']}
    assert 'heuristic' in ids
    assert 'gemini' in ids


def test_canonical_provider_id_handles_aliases_and_custom():
    assert canonical_provider_id('claude') == 'anthropic'
    assert canonical_provider_id('custom:my.module:Provider') == 'custom'


def test_recommended_provider_for_lane_prefers_ranked_compatible_provider():
    rec = recommended_provider_for_lane('quant_experimental', {'ranking': [{'provider': 'heuristic', 'exact_accuracy': 1.0, 'micro_false_positive_rate': 0.0, 'micro_false_negative_rate': 0.0}]})
    assert rec is not None
    assert rec['provider'] == 'heuristic'
