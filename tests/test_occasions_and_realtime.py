import datetime
import pytest
from fastapi.testclient import TestClient

from app.main import app, init_db
from app.security.auth import create_jwt, AuthenticatedUser
from app.security.rbac import Role
from app.services.occasions import occasions_service, _compute_days_until, OccasionRecord
from app.services.analytics import analytics_service
from app.integrations.manager import ConnectionRecord, platform_manager


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_occasions_phase7.db"
    monkeypatch.setattr("app.main.DB_PATH", str(test_db))
    monkeypatch.setattr("app.services.analytics.analytics_service._db_path_getter", lambda: str(test_db))
    monkeypatch.setattr("app.integrations.manager.platform_manager._db_path_getter", lambda: str(test_db))
    init_db()


@pytest.fixture
def test_user():
    return AuthenticatedUser(
        user_id="user_p7_test",
        email="owner@kicksdistrict.com",
        role=Role.ADMIN.value,
        tenant_id="tenant_p7_kicks"
    )


@pytest.fixture
def client(test_user):
    c = TestClient(app)
    c.headers.update({"Authorization": f"Bearer {create_jwt(test_user)}"})
    return c


def test_occasions_date_computation_and_sorting():
    """Validates dynamic days_until computation and year-wrap calculation."""
    ref_date = datetime.date(2026, 6, 1)

    # 1. Event in current year after ref_date (Independence Day July 4)
    days_july4, date_july4 = _compute_days_until(7, 4, ref_date)
    assert days_july4 == (datetime.date(2026, 7, 4) - ref_date).days
    assert date_july4.year == 2026

    # 2. Event that already passed in current year (New Year Jan 1) wraps to next year
    days_ny, date_ny = _compute_days_until(1, 1, ref_date)
    assert date_ny.year == 2027
    assert days_ny == (datetime.date(2027, 1, 1) - ref_date).days

    # 3. Dynamic service query
    upcoming = occasions_service.get_upcoming_occasions(ref_date=ref_date, days_ahead=90)
    assert len(upcoming) > 0
    # Verify strictly sorted by days_until
    for i in range(len(upcoming) - 1):
        assert upcoming[i].days_until <= upcoming[i + 1].days_until


def test_occasions_region_filtering():
    """Validates multi-region filtering (US vs IN vs GLOBAL)."""
    ref_date = datetime.date(2026, 1, 1)

    # US query should include US specific occasions and Global, but exclude India-only events
    us_events = occasions_service.get_upcoming_occasions(ref_date=ref_date, days_ahead=365, region="US")
    us_ids = [e.id for e in us_events]
    assert "us_independence" in us_ids
    assert "us_thanksgiving" in us_ids
    assert "republic_day_in" not in us_ids  # India only

    # India query should include Indian national events
    in_events = occasions_service.get_upcoming_occasions(ref_date=ref_date, days_ahead=365, region="IN")
    in_ids = [e.id for e in in_events]
    assert "republic_day_in" in in_ids
    assert "us_thanksgiving" not in in_ids  # US only


def test_occasions_vertical_filtering():
    """Validates industry-specific calendar dates."""
    ref_date = datetime.date(2026, 1, 1)

    # Sneakers vertical
    sneaker_events = occasions_service.get_upcoming_occasions(ref_date=ref_date, days_ahead=365, vertical="sneakers_streetwear")
    sneaker_ids = [e.id for e in sneaker_events]
    assert "air_max_day" in sneaker_ids
    assert "go_skateboarding_day" in sneaker_ids
    assert "world_health_day" not in sneaker_ids

    # Healthcare vertical
    health_events = occasions_service.get_upcoming_occasions(ref_date=ref_date, days_ahead=365, vertical="clinic_healthcare")
    health_ids = [e.id for e in health_events]
    assert "world_health_day" in health_ids
    assert "air_max_day" not in health_ids


def test_occasions_campaign_generation_and_zero_contamination():
    """Generates occasion campaign for a sneaker brand with zero cross-industry contamination."""
    sneaker_profile = {
        "business_name": "Kicks District",
        "industry_primary": "Fashion & Retail",
        "industry_sub": "Sneakers & Streetwear",
        "country": "US",
        "address": "404 Sneaker Alley, Brooklyn, NY",
        "contact_phone": "+1 555-KICKS-01",
        "website_url": "https://kicksdistrict.nyc"
    }

    camp = occasions_service.generate_occasion_campaign(
        tenant_id="tenant_p7_kicks",
        occasion_id="air_max_day",
        business_profile=sneaker_profile,
        custom_offer="Get 20% off all retro Air silhouettes today only"
    )

    assert camp["occasion_id"] == "air_max_day"
    assert "Kicks District" in camp["headline"]
    assert "retro Air silhouettes" in camp["offer"]
    assert "404 Sneaker Alley" in camp["copy"]
    assert "#KicksDistrict" in camp["hashtags"]

    # Verify zero coffee contamination
    for forbidden in ["espresso", "latte", "barista", "cappuccino", "brew", "roast"]:
        assert forbidden not in camp["copy"].lower()


def test_occasions_missing_profile_fails_loudly():
    """Strictly refuses to generate occasion campaign without real business profile (no fake Apex Innovations)."""
    with pytest.raises(ValueError, match="business profile is strictly required"):
        occasions_service.generate_occasion_campaign(
            tenant_id="empty_tenant",
            occasion_id="new_year",
            business_profile={}
        )


def test_channel_health_evaluation():
    """Verifies token expiration status, write scope checking, and overall health grading."""
    tenant = "tenant_health_test"

    # 1. No channels -> overall_health is no_channels
    rep_empty = analytics_service.evaluate_channel_health(tenant)
    assert rep_empty.total_connected == 0
    assert rep_empty.overall_health == "no_channels"

    # 2. Add a healthy channel (expires in 30 days)
    now = datetime.datetime.now(datetime.timezone.utc)
    future_exp = (now + datetime.timedelta(days=30)).isoformat()
    conn_healthy = ConnectionRecord(
        connection_id="conn_li_healthy",
        tenant_id=tenant,
        platform="linkedin",
        account_name="KicksDistrict Official",
        encrypted_access_token="enc_token_123",
        encrypted_refresh_token="enc_refresh_123",
        expires_at=future_exp,
        scopes=["w_member_social", "openid"],
        is_active=True,
        created_at=now.isoformat(),
        updated_at=now.isoformat()
    )
    platform_manager.save_connection(conn_healthy)

    rep1 = analytics_service.evaluate_channel_health(tenant)
    assert rep1.total_connected == 1
    assert rep1.healthy_count == 1
    assert rep1.channels[0].status == "healthy"
    assert rep1.channels[0].has_write_scope is True

    # 3. Add an expiring soon channel (< 24 hours)
    expiring_exp = (now + datetime.timedelta(hours=5)).isoformat()
    conn_expiring = ConnectionRecord(
        connection_id="conn_tw_expiring",
        tenant_id=tenant,
        platform="twitter",
        account_name="@KicksDistrict",
        encrypted_access_token="enc_token_456",
        encrypted_refresh_token="enc_refresh_456",
        expires_at=expiring_exp,
        scopes=["tweet.write"],
        is_active=True,
        created_at=now.isoformat(),
        updated_at=now.isoformat()
    )
    platform_manager.save_connection(conn_expiring)

    rep2 = analytics_service.evaluate_channel_health(tenant)
    assert rep2.total_connected == 2
    assert rep2.expiring_soon_count == 1
    assert rep2.overall_health == "degraded"

    # 4. Add an expired channel
    past_exp = (now - datetime.timedelta(hours=2)).isoformat()
    conn_expired = ConnectionRecord(
        connection_id="conn_ig_expired",
        tenant_id=tenant,
        platform="instagram",
        account_name="kicks_ig",
        encrypted_access_token="enc_token_789",
        encrypted_refresh_token="enc_refresh_789",
        expires_at=past_exp,
        scopes=["instagram_content_publish"],
        is_active=True,
        created_at=now.isoformat(),
        updated_at=now.isoformat()
    )
    platform_manager.save_connection(conn_expired)

    rep3 = analytics_service.evaluate_channel_health(tenant)
    assert rep3.total_connected == 3
    assert rep3.expired_count == 1
    assert rep3.overall_health == "critical"


def test_tenant_analytics_overview(client, test_user):
    """Tests honest analytics: reports 0 when no campaigns exist, computes real approval rates when active."""
    # 1. Empty state
    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["tenant_id"] == test_user.tenant_id
    assert data["total_campaigns"] == 0
    assert data["approval_rate_percent"] == 0.0

    # 2. Add an approved run to verify true calculation
    with analytics_service._get_db() as con:
        con.execute(
            """INSERT INTO runs (id, created_at, updated_at, tenant_id, status, request_json, logs_json, approved)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("run_p7_01", "2026-10-24T10:00:00Z", "2026-10-24T10:05:00Z", test_user.tenant_id, "approved", "{}", "[]", 1)
        )

    res2 = client.get("/api/analytics/overview")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total_campaigns"] == 1
    assert data2["approved_campaigns"] == 1
    assert data2["approval_rate_percent"] == 100.0


def test_phase7_api_endpoints(client, test_user):
    """End-to-end test of Phase 7 API endpoints."""
    # 1. Register business profile first
    prof_payload = {
        "business_name": "Urban Sole Studio",
        "industry_primary": "Retail",
        "industry_sub": "Sneakers & Streetwear",
        "region": "US",
        "city": "Los Angeles",
        "address": "777 Fairfax Ave, LA",
        "contact_phone": "+1 213-555-0199",
        "website_url": "https://urbansole.la"
    }
    res_prof = client.post("/api/business-profile", json=prof_payload)
    assert res_prof.status_code == 200

    # 2. GET /api/occasions/upcoming (auto-detects US region and sneaker vertical from profile)
    res_occ = client.get("/api/occasions/upcoming?days_ahead=120")
    assert res_occ.status_code == 200
    occ_data = res_occ.json()
    assert occ_data["count"] > 0
    assert occ_data["region_applied"] == "US"
    assert "sneakers" in occ_data["vertical_applied"]

    # 3. POST /api/occasions/generate
    first_occ_id = occ_data["occasions"][0]["id"]
    res_gen = client.post("/api/occasions/generate", json={
        "occasion_id": first_occ_id,
        "custom_offer": "Buy one pair, get 50% off second pair",
        "auto_publish": False
    })
    assert res_gen.status_code == 200
    gen_data = res_gen.json()
    assert gen_data["status"] == "generated"
    assert "Urban Sole Studio" in gen_data["campaign"]["headline"]

    # 4. GET /api/channels/health
    res_health = client.get("/api/channels/health")
    assert res_health.status_code == 200
    assert "overall_health" in res_health.json()

    # 5. GET /api/festivals/upcoming (backward compatibility check)
    res_fest = client.get("/api/festivals/upcoming")
    assert res_fest.status_code == 200
    assert "festivals" in res_fest.json()
