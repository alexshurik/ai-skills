# Approved reservation change
Scope Delta: None.
AC-1: A signed-in customer can reserve an available seat and see a confirmation; insufficient stock returns unavailable without a reservation.
AC-2: A signed-in customer can cancel their own reservation and see it cancelled; stock returns once, and repeated cancellation is harmless.
Preserve HTTP and kiosk entry contracts. Add customer ownership validation and propagate the reservation version through both entries, request models, service, repository contract, SQL mapping, and tests. This is one cohesive compatibility change across those owners. No new booking channels or events.
