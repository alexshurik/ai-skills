# Public repository contracts: InventoryRepository.decrement_available/restore;
# ReservationRepository.get/create/cancel. UnitOfWork owns the shared transaction.
# Missing evidence: concurrent cancellation lock/version strategy.
