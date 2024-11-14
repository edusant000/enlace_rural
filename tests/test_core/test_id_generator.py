import pytest
from src.core.id_generator import ParticipantIDGenerator

@pytest.fixture
def id_generator():
    return ParticipantIDGenerator()

def test_clean_name():
    generator = ParticipantIDGenerator()
    
    # Test basic cleaning
    assert generator.clean_name("JUAN PÉREZ") == "juan perez"
    
    # Test multiple spaces
    assert generator.clean_name("Juan   Pérez   García") == "juan perez garcia"
    
    # Test special characters
    assert generator.clean_name("María!@#$%^&*()_+ Ñ") == "maria n"
    
    # Test empty string
    assert generator.clean_name("") == ""
    
    # Test only special characters
    assert generator.clean_name("!@#$%^&*()") == ""

def test_validate_date():
    generator = ParticipantIDGenerator()
    
    # Test valid dates
    assert generator.validate_date("01/01/2000") is True
    assert generator.validate_date("31/12/1999") is True
    
    # Test invalid dates
    assert generator.validate_date("32/01/2000") is False  # Invalid day
    assert generator.validate_date("01/13/2000") is False  # Invalid month
    assert generator.validate_date("00/00/0000") is False  # All zeros
    
    # Test invalid formats
    assert generator.validate_date("2000-01-01") is False  # Wrong format
    assert generator.validate_date("01-01-2000") is False  # Wrong separators
    assert generator.validate_date("1/1/2000") is False    # Missing leading zeros

def test_generate_id():
    generator = ParticipantIDGenerator()
    
    # Test consistent ID generation
    id1 = generator.generate_id("Juan Pérez", "01/01/1990")
    id2 = generator.generate_id("Juan Pérez", "01/01/1990")
    assert id1 == id2
    assert len(id1) == 8
    
    # Test different inputs produce different IDs
    id3 = generator.generate_id("Juan Pérez", "02/01/1990")
    assert id1 != id3
    
    # Test case insensitivity
    id4 = generator.generate_id("JUAN PÉREZ", "01/01/1990")
    assert id1 == id4
    
    # Test error cases
    with pytest.raises(ValueError):
        generator.generate_id("", "01/01/1990")
    
    with pytest.raises(ValueError):
        generator.generate_id("Juan Pérez", "")
    
    with pytest.raises(ValueError):
        generator.generate_id("Juan Pérez", "2000-01-01")

def test_id_uniqueness():
    generator = ParticipantIDGenerator()
    
    # Generate multiple IDs and check for uniqueness
    ids = set()
    test_cases = [
        ("Juan Pérez", "01/01/1990"),
        ("Juan Perez", "01/01/1990"),  # Similar name
        ("Juan Pérez", "02/01/1990"),  # Different date
        ("María García", "01/01/1990"), # Different name
    ]
    
    for name, date in test_cases:
        id_ = generator.generate_id(name, date)
        ids.add(id_)
    
    # Check that similar but different inputs produce different IDs
    assert len(ids) == len(test_cases) - 1  # -1 because first two should produce same ID