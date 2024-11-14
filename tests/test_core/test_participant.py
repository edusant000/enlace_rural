import pytest
from datetime import datetime, timezone
from src.core.participant import Participant, ParticipantError

@pytest.fixture
def valid_participant():
    return Participant(
        name="Juan Pérez",
        birth_date="01/01/1990",
        community="San Miguel",
        education_level="Secundaria",
        gender="M",
        income_level="Medio",
        dependents=2
    )

def test_participant_creation():
    participant = Participant(
        name="Juan Pérez",
        birth_date="01/01/1990",
        community="San Miguel"
    )
    assert participant.name == "Juan Pérez"
    assert participant.birth_date == "01/01/1990"
    assert participant.community == "San Miguel"
    assert isinstance(participant.created_at, datetime)
    assert participant.created_at.tzinfo == timezone.utc

def test_participant_creation_with_invalid_data():
    # Test missing required fields
    with pytest.raises(ParticipantError):
        Participant(name="", birth_date="01/01/1990", community="San Miguel")
    
    with pytest.raises(ParticipantError):
        Participant(name="Juan Pérez", birth_date="", community="San Miguel")
    
    # Test invalid date format
    with pytest.raises(ParticipantError):
        Participant(name="Juan Pérez", birth_date="2990-01-01", community="San Miguel")

def test_update_info(valid_participant):
    # Test valid updates
    valid_participant.update_info(
        education_level="Universidad",
        income_level="Alto"
    )
    assert valid_participant.education_level == "Universidad"
    assert valid_participant.income_level == "Alto"

    # Test invalid field update
    with pytest.raises(ParticipantError):
        valid_participant.update_info(invalid_field="Value")

def test_join_activity(valid_participant):
    # Test joining activity
    valid_participant.join_activity("activity123")
    assert "activity123" in valid_participant.activities

    # Test joining with empty activity_id
    with pytest.raises(ParticipantError):
        valid_participant.join_activity("")

def test_leave_activity(valid_participant):
    # Setup
    valid_participant.join_activity("activity123")
    
    # Test successful leave
    assert valid_participant.leave_activity("activity123") is True
    assert "activity123" not in valid_participant.activities

    # Test leaving non-existent activity
    assert valid_participant.leave_activity("nonexistent") is False

def test_add_survey_response(valid_participant):
    # Test valid survey response
    survey_data = {
        "activity_id": "activity123",
        "date": "02/01/2024",
        "responses": {"q1": "answer1", "q2": "answer2"}
    }
    valid_participant.add_survey_response(survey_data)
    assert len(valid_participant.survey_responses) == 1
    assert valid_participant.survey_responses[0]["responses"] == {"q1": "answer1", "q2": "answer2"}

    # Test invalid survey data
    with pytest.raises(ParticipantError):
        valid_participant.add_survey_response({"incomplete": "data"})

def test_verify_data(valid_participant):
    # Test complete data
    verification = valid_participant.verify_data()
    assert all(verification.values())

    # Test incomplete data
    # En lugar de crear un participante inválido, modificamos uno válido
    participant = Participant(
        name="Juan Pérez",
        birth_date="01/01/1990",
        community="Test"
    )
    # Simulamos datos incompletos modificando directamente los atributos
    participant.community = ""  # Modificamos después de la creación
    verification = participant.verify_data()
    assert not verification["community"]

def test_to_dict(valid_participant):
    participant_dict = valid_participant.to_dict()
    
    assert isinstance(participant_dict, dict)
    assert participant_dict["name"] == "Juan Pérez"
    assert participant_dict["birth_date"] == "01/01/1990"
    assert participant_dict["community"] == "San Miguel"
    assert isinstance(participant_dict["created_at"], str)
    assert isinstance(participant_dict["updated_at"], str)