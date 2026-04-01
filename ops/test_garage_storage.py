"""Compatibility aggregator for the remaining factual storage-backed Garage tests."""

from ops.test_garage_storage_persistence import GarageStoragePersistenceTests
from ops.test_garage_storage_posture import GarageStoragePostureTests

__all__ = ["GarageStoragePersistenceTests", "GarageStoragePostureTests"]
