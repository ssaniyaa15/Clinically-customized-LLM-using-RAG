from monitoring.concept_drift import ConceptDriftMonitor, ConceptDriftSuite


def test_adwin_update_interface() -> None:
    monitor = ConceptDriftMonitor()
    out = monitor.update(0.1)
    assert isinstance(out, bool)


def test_concept_suite_update_all() -> None:
    suite = ConceptDriftSuite.build()
    result = suite.update_all(0.2)
    assert set(result.keys()) == {"adwin", "ddm", "eddm"}

