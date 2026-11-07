# Reservations project
Keep the approved layered transport/service/repository organization. BookingService owns reservation policy. InventoryRepository is the public stock port. HTTP and kiosk commands use the same service. Inventory decrements and reservation creation commit in one UnitOfWork transaction. Do not send external events inside that transaction.
