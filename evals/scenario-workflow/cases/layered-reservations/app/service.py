class BookingService:
    def __init__(self, uow):
        self.uow = uow

    def reserve(self, command):
        with self.uow.transaction():
            self.uow.inventory.decrement_available(command.seat_id)
            return self.uow.reservations.create(command)

    def cancel(self, command):
        with self.uow.transaction():
            reservation = self.uow.reservations.get(command.reservation_id)
            if reservation.status != "cancelled":
                self.uow.reservations.cancel(reservation)
                self.uow.inventory.restore(reservation.seat_id)
            return reservation
