import pytest
from datetime import datetime, timezone
from src.core.activity import Activity, ActivityStatus

@pytest.fixture
def valid_activity():
    return Activity(
        name="Taller de Agricultura",
        description="Taller sobre técnicas agrícolas sostenibles",
        start_date="01/01/2024",
        end_date="02/01/2024",
        location="Centro Comunitario",
        coordinator_id="coord123",
        max_participants=20
    )

def test_activity_creation():
    # Test successful creation
    activity = Activity(
        name="Test Activity",
        description="Test Description",
        start_date="01/01/2024",
        end_date="02/01/2024",
        location="Test Location",
        coordinator_id="coord123"
    )
    
    assert activity.name == "Test Activity"
    assert activity.status == ActivityStatus.PENDING
    assert activity.coordinator_id in activity.admins
    assert isinstance(activity.created_at, datetime)
    assert activity.created_at.tzinfo == timezone.utc

def test_activity_validation():
    # Test invalid dates
    with pytest.raises(ValueError):
        Activity(
            name="Test",
            description="Test",
            start_date="02/01/2024",
            end_date="01/01/2024",  # End before start
            location="Test",
            coordinator_id="coord123"
        )
    
    # Test missing required fields
    with pytest.raises(ValueError):
        Activity(
            name="",
            description="Test",
            start_date="01/01/2024",
            end_date="02/01/2024",
            location="Test",
            coordinator_id="coord123"
        )

def test_add_participant(valid_activity):
    # Test successful addition
    assert valid_activity.add_participant("user123", "coord123") is True
    assert "user123" in valid_activity.participants
    
    # Test duplicate addition
    assert valid_activity.add_participant("user123", "coord123") is False
    
    # Test non-admin addition
    assert valid_activity.add_participant("user456", "non_admin") is False
    
    # Test max participants limit
    activity = Activity(
        name="Limited Activity",
        description="Test",
        start_date="01/01/2024",
        end_date="02/01/2024",
        location="Test",
        coordinator_id="coord123",
        max_participants=1
    )
    activity.add_participant("user123", "coord123")
    assert activity.add_participant("user456", "coord123") is False

def test_remove_participant(valid_activity):
    # Setup
    valid_activity.add_participant("user123", "coord123")
    
    # Test successful removal
    assert valid_activity.remove_participant("user123", "coord123") is True
    assert "user123" not in valid_activity.participants
    
    # Test non-existent participant
    assert valid_activity.remove_participant("nonexistent", "coord123") is False
    
    # Test non-admin removal
    valid_activity.add_participant("user123", "coord123")
    assert valid_activity.remove_participant("user123", "non_admin") is False

def test_make_admin(valid_activity):
    # Setup
    valid_activity.add_participant("user123", "coord123")
    
    # Test successful promotion
    assert valid_activity.make_admin("user123", "coord123") is True
    assert "user123" in valid_activity.admins
    
    # Test non-participant promotion
    assert valid_activity.make_admin("nonexistent", "coord123") is False
    
    # Test non-admin promotion attempt
    assert valid_activity.make_admin("user456", "non_admin") is False

def test_update_status(valid_activity):
    # Test successful update
    assert valid_activity.update_status(ActivityStatus.IN_PROGRESS, "coord123") is True
    assert valid_activity.status == ActivityStatus.IN_PROGRESS
    
    # Test non-admin update
    assert valid_activity.update_status(ActivityStatus.COMPLETED, "non_admin") is False

def test_verify_participant_data(valid_activity):
    # Test complete data
    data = {
        "name": "Test User",
        "birth_date": "01/01/1990",
        "id": "user123"
    }
    assert valid_activity.verify_participant_data(data) is True
    
    # Test incomplete data
    incomplete_data = {
        "name": "Test User",
        "id": "user123"
    }
    assert valid_activity.verify_participant_data(incomplete_data) is False

def test_mark_surveys_ready(valid_activity):
    # Test successful marking
    assert valid_activity.mark_surveys_ready("coord123") is True
    assert valid_activity.surveys_ready is True
    
    # Test non-admin marking
    valid_activity.surveys_ready = False
    assert valid_activity.mark_surveys_ready("non_admin") is False

def test_to_dict(valid_activity):
    activity_dict = valid_activity.to_dict()
    
    assert isinstance(activity_dict, dict)
    assert activity_dict["name"] == "Taller de Agricultura"
    assert activity_dict["status"] == ActivityStatus.PENDING.value
    assert isinstance(activity_dict["created_at"], str)
    assert isinstance(activity_dict["updated_at"], str)
    assert isinstance(activity_dict["change_log"], list)

def test_change_log(valid_activity):
    # Test initial log entry
    assert len(valid_activity.change_log) == 1
    assert valid_activity.change_log[0]["action"] == "created"
    
    # Test log after actions
    valid_activity.add_participant("user123", "coord123")
    assert len(valid_activity.change_log) == 2
    assert "added_participant" in valid_activity.change_log[1]["action"]