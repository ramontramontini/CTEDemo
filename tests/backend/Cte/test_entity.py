"""Tests for Cte entity — CT-e document aggregate root."""

import pytest

from src.domain.cte.entity import Cte
from src.domain.cte.enums import CteStatus


class TestCteEntity:
    """Cte entity tests."""

    def test_has_required_fields(self):
        cte = Cte._create_raw(
            access_key="26251010758386000159570200000000011000000010",
            freight_order_number="12345678901234",
            status=CteStatus.GERADO,
            xml="<xml/>",
            original_payload={"FreightOrder": "12345678901234"},
        )
        assert cte.id is not None
        assert len(cte.access_key) == 44
        assert cte.freight_order_number == "12345678901234"
        assert cte.status == CteStatus.GERADO
        assert cte.xml == "<xml/>"
        assert cte.original_payload == {"FreightOrder": "12345678901234"}
        assert cte.created_at is not None

    def test_status_is_gerado(self):
        cte = Cte._create_raw(
            access_key="26251010758386000159570200000000011000000010",
            freight_order_number="12345678901234",
            status=CteStatus.GERADO,
            xml="<xml/>",
            original_payload={},
        )
        assert cte.status == CteStatus.GERADO

    def test_encapsulation_private_attrs(self):
        cte = Cte._create_raw(
            access_key="26251010758386000159570200000000011000000010",
            freight_order_number="12345678901234",
            status=CteStatus.GERADO,
            xml="<xml/>",
            original_payload={},
        )
        with pytest.raises(AttributeError):
            cte.access_key = "x" * 44

    def test_is_gerado_returns_true_for_gerado(self):
        cte = Cte._create_raw(
            access_key="26251010758386000159570200000000011000000010",
            freight_order_number="12345678901234",
            status=CteStatus.GERADO,
            xml="<xml/>",
            original_payload={},
        )
        assert cte.is_gerado() is True

    def test_is_gerado_returns_false_for_erro(self):
        cte = Cte._create_raw(
            access_key="26251010758386000159570200000000011000000010",
            freight_order_number="12345678901234",
            status=CteStatus.ERRO,
            xml="<xml/>",
            original_payload={},
        )
        assert cte.is_gerado() is False

    def test_formatted_access_key(self):
        cte = Cte._create_raw(
            access_key="26251010758386000159570200000000011000000060",
            freight_order_number="12345678901234",
            status=CteStatus.GERADO,
            xml="<xml/>",
            original_payload={},
        )
        expected = "26 2510 10758386000159 57 020 000000001 1 00000006 0"
        assert cte.formatted_access_key() == expected

    def test_repr(self):
        cte = Cte._create_raw(
            access_key="26251010758386000159570200000000011000000010",
            freight_order_number="12345678901234",
            status=CteStatus.GERADO,
            xml="<xml/>",
            original_payload={},
        )
        r = repr(cte)
        assert "Cte" in r
        assert "12345678901234" in r
