import pandas as pd

from preprocessing.imputation_qc import _fit_imputer, _flag_outliers_iqr, impute_and_qc


def test_fit_imputer_fills_missing_values() -> None:
    df = pd.DataFrame({"a": [1.0, None, 3.0], "b": [4.0, 5.0, None]})
    imputed, _ = _fit_imputer(df)
    assert int(imputed.isna().sum().sum()) == 0


def test_flag_outliers_iqr() -> None:
    df = pd.DataFrame({"x": [1, 2, 3, 4, 1000]})
    flags = _flag_outliers_iqr(df, threshold=1.0)
    assert any(flag.startswith("x@row") for flag in flags)


def test_impute_and_qc_report() -> None:
    df = pd.DataFrame({"a": [1.0, None, 3.0], "b": [10.0, 11.0, 1000.0]})
    result = impute_and_qc(df)
    assert result.imputation_report["missing_before"] == 1
    assert result.imputation_report["missing_after"] == 0
    assert "a" in result.imputation_report["numeric_columns"]

