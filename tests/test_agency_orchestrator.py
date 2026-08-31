"""Unit tests for Autonomous AI Agency Orchestrator."""

import pytest
from src.agency.orchestrator import AutonomousAgencyOrchestrator
from src.database.db import get_db_session


def test_agency_orchestrator_initialization():
    orchestrator = AutonomousAgencyOrchestrator()
    assert orchestrator is not None
    assert len(orchestrator.activity_logs) > 0


def test_agency_orchestrator_state():
    orchestrator = AutonomousAgencyOrchestrator()
    with get_db_session() as session:
        state = orchestrator.get_mission_control_state(session)
        assert "stats" in state
        assert "activity_feed" in state
        assert "recent_leads" in state
