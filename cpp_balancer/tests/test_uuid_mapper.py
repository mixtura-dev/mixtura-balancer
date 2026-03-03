"""
Tests for UUIDMapper class.

Tests UUID to int mapping and back conversion.
"""

import uuid
import pytest
from balance_engine.wrapper import UUIDMapper


class TestUUIDMapper:
    """Test suite for UUIDMapper bidirectional conversion."""

    def test_mapper_initialization(self):
        """Test that mapper initializes correctly."""
        mapper = UUIDMapper()
        assert mapper is not None

    def test_register_single_uuid(self):
        """Test registering a single UUID."""
        mapper = UUIDMapper()
        test_uuid = uuid.uuid4()

        int_id = mapper.register(test_uuid)

        assert isinstance(int_id, int)
        assert int_id == 0  # First registered ID should be 0

    def test_register_multiple_uuids(self):
        """Test registering multiple UUIDs increments correctly."""
        mapper = UUIDMapper()
        uuid1 = uuid.uuid4()
        uuid2 = uuid.uuid4()
        uuid3 = uuid.uuid4()

        id1 = mapper.register(uuid1)
        id2 = mapper.register(uuid2)
        id3 = mapper.register(uuid3)

        assert id1 == 0
        assert id2 == 1
        assert id3 == 2

    def test_register_idempotent(self):
        """Test that registering the same UUID twice returns same ID."""
        mapper = UUIDMapper()
        test_uuid = uuid.uuid4()

        id1 = mapper.register(test_uuid)
        id2 = mapper.register(test_uuid)

        assert id1 == id2

    def test_to_int_conversion(self):
        """Test converting registered UUID to int."""
        mapper = UUIDMapper()
        test_uuid = uuid.uuid4()
        registered_id = mapper.register(test_uuid)

        retrieved_id = mapper.to_int(test_uuid)

        assert retrieved_id == registered_id

    def test_to_uuid_conversion(self):
        """Test converting int back to UUID."""
        mapper = UUIDMapper()
        test_uuid = uuid.uuid4()
        registered_id = mapper.register(test_uuid)

        retrieved_uuid = mapper.to_uuid(registered_id)

        assert retrieved_uuid == test_uuid

    def test_bidirectional_conversion(self):
        """Test that conversion is bidirectional without loss."""
        mapper = UUIDMapper()
        test_uuids = [uuid.uuid4() for _ in range(5)]

        # Register all
        int_ids = [mapper.register(u) for u in test_uuids]

        # Convert back and verify
        retrieved_uuids = [mapper.to_uuid(int_id) for int_id in int_ids]

        assert test_uuids == retrieved_uuids

    def test_register_all(self):
        """Test registering multiple UUIDs at once."""
        mapper = UUIDMapper()
        test_uuids = [uuid.uuid4() for _ in range(5)]

        int_ids = mapper.register_all(test_uuids)

        assert len(int_ids) == 5
        assert int_ids == [0, 1, 2, 3, 4]

    def test_register_all_with_conversion(self):
        """Test that register_all works with conversion."""
        mapper = UUIDMapper()
        test_uuids = [uuid.uuid4() for _ in range(5)]

        mapper.register_all(test_uuids)

        # Verify each UUID converts correctly
        for idx, test_uuid in enumerate(test_uuids):
            assert mapper.to_int(test_uuid) == idx
            assert mapper.to_uuid(idx) == test_uuid

    def test_to_int_unregistered_uuid_raises(self):
        """Test that converting an unregistered UUID raises KeyError."""
        mapper = UUIDMapper()
        unregistered_uuid = uuid.uuid4()

        with pytest.raises(KeyError):
            mapper.to_int(unregistered_uuid)

    def test_to_uuid_invalid_int_raises(self):
        """Test that converting invalid int ID raises KeyError."""
        mapper = UUIDMapper()

        with pytest.raises(KeyError):
            mapper.to_uuid(999)

    def test_clear(self):
        """Test clearing all mappings."""
        mapper = UUIDMapper()
        test_uuid = uuid.uuid4()
        mapper.register(test_uuid)

        mapper.clear()

        with pytest.raises(KeyError):
            mapper.to_int(test_uuid)

    def test_clear_resets_next_id(self):
        """Test that clear resets the next_id counter."""
        mapper = UUIDMapper()
        uuid1 = uuid.uuid4()
        uuid2 = uuid.uuid4()

        id1 = mapper.register(uuid1)
        assert id1 == 0

        mapper.clear()

        id2 = mapper.register(uuid2)
        assert id2 == 0  # Should start from 0 again

    def test_mapper_with_predefined_uuids(self):
        """Test mapper with predefined UUIDs."""
        mapper = UUIDMapper()
        carry_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
        mid_uuid = uuid.UUID("87654321-4321-8765-4321-876543218765")

        carry_id = mapper.register(carry_uuid)
        mid_id = mapper.register(mid_uuid)

        assert carry_id == 0
        assert mid_id == 1
        assert mapper.to_uuid(0) == carry_uuid
        assert mapper.to_uuid(1) == mid_uuid

    def test_mapper_handles_many_uuids(self):
        """Test mapper with large number of UUIDs."""
        mapper = UUIDMapper()
        test_uuids = [uuid.uuid4() for _ in range(100)]

        int_ids = mapper.register_all(test_uuids)

        assert len(int_ids) == 100
        # Verify random sampling
        for idx in [0, 25, 50, 75, 99]:
            assert mapper.to_uuid(idx) == test_uuids[idx]

    def test_mapper_preserves_uuid_uniqueness(self):
        """Test that mapper preserves UUID uniqueness."""
        mapper = UUIDMapper()
        uuid1 = uuid.uuid4()
        uuid2 = uuid.uuid4()

        id1 = mapper.register(uuid1)
        id2 = mapper.register(uuid2)

        assert id1 != id2
        assert mapper.to_uuid(id1) != mapper.to_uuid(id2)
