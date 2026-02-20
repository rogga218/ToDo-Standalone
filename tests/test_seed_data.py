from unittest.mock import patch, MagicMock
from sqlmodel import Session
from src.seed_data import create_seed_data


def test_create_seed_data_no_persons():
    # Patch the global engine so seed_data connects to our mocked environment
    with patch("src.seed_data.create_db_and_tables"):
        with patch("src.seed_data.Session") as mock_session_cls:
            mock_session = MagicMock(spec=Session)
            mock_session_cls.return_value.__enter__.return_value = mock_session

            # Simulate returning NO persons
            mock_session.exec.return_value.all.return_value = []

            create_seed_data()

            # Assert that session.commit was never called because it aborted
            mock_session.commit.assert_not_called()


def test_create_seed_data_success():
    with patch("src.seed_data.create_db_and_tables"):
        with patch("src.seed_data.Session") as mock_session_cls:
            mock_session = MagicMock(spec=Session)
            mock_session_cls.return_value.__enter__.return_value = mock_session

            # Simulate returning 2 persons
            mock_person = MagicMock()
            mock_person.id = "fake-uuid"
            mock_person.name = "Seed Man"
            mock_session.exec.return_value.all.return_value = [mock_person, mock_person]

            create_seed_data()

            # Assert that 42 todos were generated
            assert mock_session.add.call_count == 42
            mock_session.commit.assert_called_once()
