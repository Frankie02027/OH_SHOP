"""Compatibility aggregator for storage-backed Garage tests.

The substantive storage-backed tests now live in smaller concern-based
modules so this file is no longer the physical catch-all.
"""

from ops.test_garage_storage_flow import GarageStorageFlowTests
from ops.test_garage_storage_persistence import GarageStoragePersistenceTests
from ops.test_garage_storage_posture import GarageStoragePostureTests

__all__ = [
    "GarageStorageFlowTests",
    "GarageStoragePersistenceTests",
    "GarageStoragePostureTests",
]
