"""
Payment Discrepancy Analysis
============================

Investigates the relationship between credit-card instalments
and payment discrepancies among delivered orders.

Models:
    1. Logistic regression with continuous log-transformed order value.
    2. Logistic regression with categorical order-value quartiles.

Outcome:
    discrepancy = 1 when the absolute difference between payment
    value and expected order value exceeds R$0.01.

Expected order value:
    SUM(order item price + freight value)

Population:
    Delivered orders with exactly one credit-card payment record.

Important:
    These models investigate statistical associations.
    They do not establish causation.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from boa.config.database import engine

# ============================================================
# 1. CONFIGURATION
# ============================================================

REFERENCE_INSTALLMENT = "1 installment"

INSTALLMENT_BINS = [
    0,
    1,
    3,
    6,
    12,
    float("inf"),
]

INSTALLMENT_LABELS = [
    "1 installment",
    "2-3 installments",
    "4-6 installments",
    "7-12 installments",
    "More than 12 installments",
]

DISCREPANCY_THRESHOLD = 0.01


# ============================================================
# 2. SQL QUERY
# ============================================================

QUERY = """
WITH item_totals AS (
    SELECT
        order_id,
        SUM(price + freight_value) AS expected_order_value
    FROM analytics.fact_order_items
    GROUP BY order_id
),

payment_totals AS (
    SELECT
        order_id,
        COUNT(*) AS payment_count,
        MAX(payment_type) AS payment_type,
        MAX(payment_installments) AS payment_installments,
        SUM(payment_value) AS payment_value
    FROM analytics.fact_payments
    GROUP BY order_id
),

eligible_orders AS (
    SELECT
        o.order_id,
        i.expected_order_value,
        p.payment_installments,
        p.payment_value,

        ROUND(
            p.payment_value - i.expected_order_value,
            2
        ) AS payment_difference

    FROM analytics.fact_orders o

    INNER JOIN item_totals i
        ON o.order_id = i.order_id

    INNER JOIN payment_totals p
        ON o.order_id = p.order_id

    WHERE o.order_status = 'delivered'
      AND p.payment_count = 1
      AND p.payment_type = 'credit_card'
      AND p.payment_installments IS NOT NULL
      AND p.payment_installments > 0
),

quartiled_orders AS (
    SELECT
        *,

        NTILE(4) OVER (
            ORDER BY expected_order_value
        ) AS order_value_quartile

    FROM eligible_orders
)

SELECT
    order_id,
    expected_order_value,
    payment_installments,
    payment_value,
    payment_difference,
    order_value_quartile

FROM quartiled_orders;
"""


# ============================================================
# 3. DATA PREPARATION
# ============================================================


def load_data() -> pd.DataFrame:
    """Retrieve eligible orders from PostgreSQL."""

    return pd.read_sql_query(QUERY, engine)


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Create model variables and validate the dataset."""

    df = df.copy()

    # Binary target variable.
    df["discrepancy"] = (df["payment_difference"].abs() > DISCREPANCY_THRESHOLD).astype(
        int
    )

    # Instalment categories.
    df["installment_group"] = pd.cut(
        df["payment_installments"],
        bins=INSTALLMENT_BINS,
        labels=INSTALLMENT_LABELS,
        include_lowest=True,
    )

    # Use one instalment as the reference category.
    df["installment_group"] = pd.Categorical(
        df["installment_group"],
        categories=INSTALLMENT_LABELS,
        ordered=False,
    )

    # Continuous order-value variable.
    df["log_order_value"] = np.log1p(df["expected_order_value"])

    # Treat quartiles as categorical variables.
    df["order_value_quartile"] = df["order_value_quartile"].astype("category")

    if df["installment_group"].isna().any():
        raise ValueError("Some records have missing installment groups.")

    if df["order_value_quartile"].isna().any():
        raise ValueError("Some records have missing order-value quartiles.")

    if (df["expected_order_value"] <= 0).any():
        raise ValueError("Expected order values must be positive.")

    return df


# ============================================================
# 4. DATASET SUMMARY
# ============================================================


def print_dataset_summary(df: pd.DataFrame) -> None:
    """Display basic information about the analytical dataset."""

    print("\n" + "=" * 65)
    print("PAYMENT DISCREPANCY ANALYSIS")
    print("=" * 65)

    print("\nDATASET SUMMARY")
    print("-" * 65)

    print(f"Eligible orders: {len(df):,}")

    print(f"Discrepant orders: {df['discrepancy'].sum():,}")

    print(f"Matched orders: {(df['discrepancy'] == 0).sum():,}")

    print(f"Overall discrepancy rate: {df['discrepancy'].mean() * 100:.3f}%")

    print("\nINSTALMENT GROUP DISTRIBUTION")
    print("-" * 65)

    distribution = df.groupby("installment_group", observed=False).agg(
        total_orders=("order_id", "count"),
        discrepant_orders=("discrepancy", "sum"),
    )

    distribution["discrepancy_rate_pct"] = (
        distribution["discrepant_orders"] / distribution["total_orders"] * 100
    )

    print(distribution.round(3).to_string())


# ============================================================
# 5. MODEL RESULT REPORTING
# ============================================================


def print_model_results(
    model,
    model_name: str,
) -> None:
    """Print coefficients, odds ratios and confidence intervals."""

    confidence_intervals = model.conf_int()

    results = pd.DataFrame(
        {
            "coefficient": model.params,
            "odds_ratio": np.exp(model.params),
            "p_value": model.pvalues,
            "ci_lower": np.exp(confidence_intervals[0]),
            "ci_upper": np.exp(confidence_intervals[1]),
        }
    )

    print("\n" + "=" * 80)
    print(model_name)
    print("=" * 80)

    print("\nADJUSTED ODDS RATIOS")
    print("-" * 80)

    print(results.round(4).to_string())

    print("\nMODEL DIAGNOSTICS")
    print("-" * 80)

    print(f"Observations: {int(model.nobs):,}")
    print(f"Log-likelihood: {model.llf:.4f}")
    print(f"Deviance: {model.deviance:.4f}")
    print(f"Pearson chi-square: {model.pearson_chi2:.4f}")
    print(
        f"Pearson chi-square / residual df: {model.pearson_chi2 / model.df_resid:.4f}"
    )
    print(f"Degrees of freedom: {model.df_resid:.0f}")

    print("\nFULL MODEL SUMMARY")
    print("-" * 80)

    print(model.summary())


# ============================================================
# 6. MODEL 1: CONTINUOUS ORDER VALUE
# ============================================================


def fit_continuous_model(df: pd.DataFrame):
    """
    Model 1:
        Discrepancy ~ Instalment group + log(order value)
    """

    formula = (
        "discrepancy ~ "
        "log_order_value + "
        "C(installment_group, "
        "Treatment(reference='1 installment'))"
    )

    model = smf.glm(
        formula=formula,
        data=df,
        family=sm.families.Binomial(),
    ).fit(cov_type="HC3")

    print_model_results(
        model,
        "MODEL 1: CONTINUOUS LOG-TRANSFORMED ORDER VALUE",
    )

    return model


# ============================================================
# 7. MODEL 2: CATEGORICAL ORDER VALUE QUARTILES
# ============================================================


def fit_quartile_model(df: pd.DataFrame):
    """
    Model 2:
        Discrepancy ~ Instalment group + Order-value quartile
    """

    formula = (
        "discrepancy ~ "
        "C(installment_group, "
        "Treatment(reference='1 installment')) "
        "+ C(order_value_quartile, Treatment(reference=1))"
    )

    model = smf.glm(
        formula=formula,
        data=df,
        family=sm.families.Binomial(),
    ).fit(cov_type="HC3")

    print_model_results(
        model,
        "MODEL 2: CATEGORICAL ORDER-VALUE QUARTILES",
    )

    return model


# ============================================================
# 8. MODEL COMPARISON
# ============================================================


def compare_models(model_1, model_2) -> None:
    """
    Compare model fit and adjusted instalment effects.

    Both models must be fitted on the same observations.
    """

    if model_1.nobs != model_2.nobs:
        raise ValueError("Models must use the same number of observations.")

    def calculate_diagnostics(model):
        observations = int(model.nobs)
        parameter_count = len(model.params)

        null_deviance = model.null_deviance

        deviance_explained = (
            1 - model.deviance / null_deviance if null_deviance > 0 else np.nan
        )

        return {
            "observations": observations,
            "parameters": parameter_count,
            "log_likelihood": model.llf,
            "deviance": model.deviance,
            "null_deviance": null_deviance,
            "deviance_explained": deviance_explained,
            "AIC": model.aic,
            "BIC": (-2 * model.llf + np.log(observations) * parameter_count),
            "pearson_dispersion": (model.pearson_chi2 / model.df_resid),
        }

    diagnostics = pd.DataFrame(
        {
            "Model 1": calculate_diagnostics(model_1),
            "Model 2": calculate_diagnostics(model_2),
        }
    )

    print("\n" + "=" * 80)
    print("MODEL FIT COMPARISON")
    print("=" * 80)

    print(diagnostics.round(4).to_string())

    # Compare adjusted instalment effects.
    def extract_installment_effects(model):
        confidence_intervals = model.conf_int()

        results = []

        for parameter in model.params.index:
            if not parameter.startswith("C(installment_group"):
                continue

            results.append(
                {
                    "parameter": parameter,
                    "odds_ratio": np.exp(model.params[parameter]),
                    "ci_lower": np.exp(confidence_intervals.loc[parameter, 0]),
                    "ci_upper": np.exp(confidence_intervals.loc[parameter, 1]),
                    "p_value": model.pvalues[parameter],
                }
            )

        return pd.DataFrame(results).set_index("parameter")

    effects_1 = extract_installment_effects(model_1)
    effects_2 = extract_installment_effects(model_2)

    comparison = effects_1.join(
        effects_2,
        how="outer",
        lsuffix="_model_1",
        rsuffix="_model_2",
    )

    print("\n" + "=" * 80)
    print("ADJUSTED INSTALMENT ODDS RATIO COMPARISON")
    print("=" * 80)

    print(comparison.round(4).to_string())

    print("\nINTERPRETATION GUIDE")
    print("-" * 80)
    print(
        "Odds ratios above 1 indicate higher odds of discrepancy "
        "relative to the reference group."
    )
    print(
        "Odds ratios below 1 indicate lower odds of discrepancy "
        "relative to the reference group."
    )
    print(
        "Confidence intervals containing 1 indicate that the "
        "estimated effect is not statistically distinguishable "
        "from the reference at the 5% level."
    )
    print(
        "A lower AIC or BIC indicates a better fit-adjusted "
        "information criterion among these candidate models."
    )
    print(
        "Deviance explained is calculated as 1 minus model "
        "deviance divided by null deviance. It is not an "
        "ordinary least-squares R-squared."
    )
    print("These results describe associations, not causal effects.")


# ============================================================
# 9. MAIN EXECUTION
# ============================================================


def main():

    print("Loading data from PostgreSQL...")

    df = load_data()

    print("Preparing analytical dataset...")

    df = prepare_data(df)

    print_dataset_summary(df)

    # Fit both models and retain their results.
    model_1 = fit_continuous_model(df)
    model_2 = fit_quartile_model(df)

    # Compare model fit and instalment effects.
    compare_models(model_1, model_2)


if __name__ == "__main__":
    main()
