"""Tests for MemoryCtePublisher — Fila mock."""

from datetime import datetime, timezone

from src.infrastructure.messaging.memory_cte_publisher import MemoryCtePublisher


class TestMemoryCtePublisher:
    """MemoryCtePublisher stores events in memory."""

    def test_publish_records_event(self):
        publisher = MemoryCtePublisher()
        publisher.publish("FO-001", "ACCESS-KEY-001", {"key": "value"})
        assert len(publisher.published_events()) == 1

    def test_publish_multiple_events_preserved_in_order(self):
        publisher = MemoryCtePublisher()
        publisher.publish("FO-001", "AK-001", {})
        publisher.publish("FO-002", "AK-002", {})
        publisher.publish("FO-003", "AK-003", {})
        events = publisher.published_events()
        assert len(events) == 3
        assert events[0]["freight_order_number"] == "FO-001"
        assert events[1]["freight_order_number"] == "FO-002"
        assert events[2]["freight_order_number"] == "FO-003"

    def test_published_event_contains_required_fields(self):
        publisher = MemoryCtePublisher()
        publisher.publish("FO-001", "AK-001", {"data": "test"})
        event = publisher.published_events()[0]
        assert event["freight_order_number"] == "FO-001"
        assert event["access_key"] == "AK-001"
        assert event["payload"] == {"data": "test"}
        assert "published_at" in event
        assert isinstance(event["published_at"], datetime)
