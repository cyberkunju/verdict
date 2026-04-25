from verdict_pipeline.score import compute_scores


def test_compute_scores_produces_expected_ranges() -> None:
    result = compute_scores(
        hr_baseline=74.0,
        hr_peak=95.0,
        hr_delta=21.0,
        hrv_rmssd=18.0,
        au15_max=2.4,
        au14_max=1.1,
        au6_present=False,
        au24_max=1.8,
        f0_baseline=120.0,
        f0_peak=144.0,
        f0_delta=24.0,
        jitter_percent=2.4,
        shimmer_db=1.7,
        speech_rate_wpm=132.0,
        hedging_count=3,
        pronoun_drop_rate=0.22,
        word_count=40,
        certainty_count=1,
        specificity_score=0.45,
        affect_negative=1,
        rppg_timeline=[{"t": i, "hr": 74.0 + i} for i in range(10)],
    )

    assert 0 <= result.deception <= 100
    assert 0 <= result.sincerity <= 100
    assert 0 <= result.stress <= 100
    assert 0 <= result.confidence <= 100
    assert len(result.timeline) >= 10
    assert set(result.ci.keys()) == {"deception", "sincerity", "stress", "confidence"}
