from unittest.mock import MagicMock

import pandas as pd
import pytest

from boa.analytics import data_loader


@pytest.fixture
def mock_database(monkeypatch):
    """Provide a mocked SQLAlchemy engine and connection."""
    engine = MagicMock()
    connection = MagicMock()

    engine.connect.return_value.__enter__.return_value = connection

    expected_df = pd.DataFrame({"order_id": ["order_1"]})

    read_sql = MagicMock(return_value=expected_df)

    monkeypatch.setattr(data_loader, "get_engine", lambda: engine)
    monkeypatch.setattr(data_loader.pd, "read_sql_query", read_sql)

    return {
        "engine": engine,
        "connection": connection,
        "read_sql": read_sql,
        "expected_df": expected_df,
    }


@pytest.mark.parametrize(
    "view_name",
    sorted(data_loader.ANALYTICS_VIEWS),
)
def test_load_analytics_view_accepts_supported_views(
    view_name,
    mock_database,
):
    result = data_loader.load_analytics_view(view_name)

    assert result.equals(mock_database["expected_df"])

    mock_database["engine"].connect.assert_called_once()

    mock_database["read_sql"].assert_called_once()

    query = mock_database["read_sql"].call_args.args[0]

    assert str(query) == f"SELECT * FROM analytics.{view_name}"

    assert mock_database["read_sql"].call_args.args[1] == mock_database["connection"]


@pytest.mark.parametrize(
    "view_name",
    [
        "users",
        "orders",
        "vw_unknown",
        "analytics.vw_order_performance",
        "",
        "vw_order_performance; DROP TABLE orders",
    ],
)
def test_load_analytics_view_rejects_unsupported_views(
    view_name,
    mock_database,
):
    with pytest.raises(ValueError, match="Unsupported analytics view"):
        data_loader.load_analytics_view(view_name)

    mock_database["engine"].connect.assert_not_called()
    mock_database["read_sql"].assert_not_called()


@pytest.mark.parametrize(
    ("loader", "expected_view"),
    [
        (
            data_loader.load_order_performance,
            "vw_order_performance",
        ),
        (
            data_loader.load_customer_rfm,
            "vw_customer_rfm",
        ),
        (
            data_loader.load_category_performance,
            "vw_category_performance",
        ),
        (
            data_loader.load_delivery_review_analysis,
            "vw_delivery_review_analysis",
        ),
    ],
)
def test_convenience_loaders_call_correct_view(
    loader,
    expected_view,
    mock_database,
    monkeypatch,
):
    called_views = []

    def fake_load(view_name):
        called_views.append(view_name)
        return mock_database["expected_df"]

    monkeypatch.setattr(data_loader, "load_analytics_view", fake_load)

    result = loader()

    assert called_views == [expected_view]
    assert result.equals(mock_database["expected_df"])


def test_load_customer_order_activity_executes_expected_query(
    mock_database,
):
    result = data_loader.load_customer_order_activity()

    assert result.equals(mock_database["expected_df"])

    mock_database["engine"].connect.assert_called_once()
    mock_database["read_sql"].assert_called_once()

    query = str(mock_database["read_sql"].call_args.args[0])

    assert "analytics.fact_orders AS fo" in query
    assert "analytics.dim_customers AS dc" in query
    assert "dc.customer_unique_id" in query
    assert "fo.order_id" in query
    assert "fo.order_purchase_timestamp" in query
    assert "fo.customer_key = dc.customer_key" in query
    assert "fo.order_status = 'delivered'" in query


def test_load_analytics_view_propagates_query_errors(
    mock_database,
):
    mock_database["read_sql"].side_effect = RuntimeError("Database query failed")

    with pytest.raises(RuntimeError, match="Database query failed"):
        data_loader.load_analytics_view("vw_order_performance")


def test_load_analytics_view_propagates_connection_errors(
    mock_database,
):
    mock_database["engine"].connect.side_effect = RuntimeError(
        "Database connection failed"
    )

    with pytest.raises(RuntimeError, match="Database connection failed"):
        data_loader.load_analytics_view("vw_order_performance")
