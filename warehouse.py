class Reservation:
    def __init__(self, id, sku, qty):
        self.id = id
        self.sku = sku
        self.qty = qty
        self.active = True

class Stock:
    def __init__(self, sku):
        self.sku = sku
        self.total = 0
        self.reserved = 0

class Warehouse:
    def __init__(self):
        self.stocks = {}
        self.reservations = {}
        self.reservation_id = 1

    def receive(self, sku, qty):
        if sku not in self.stocks:
            self.stocks[sku] = Stock(sku)
        self.stocks[sku].total += qty

    def reserve(self, sku, qty):
        if sku not in self.stocks or self.available(sku) < qty:
            raise Exception("Not enough stock")
        r = Reservation(self.reservation_id, sku, qty)
        self.reservations[self.reservation_id] = r
        self.stocks[sku].reserved += qty
        self.reservation_id += 1
        return r

    def release(self, reservation_id, qty):
        r = self.reservations.get(reservation_id)
        if not r or not r.active:
            raise Exception("Invalid reservation")
        # Only allow releasing up to the reserved amount for this reservation
        release_qty = min(qty, r.qty)
        self.stocks[r.sku].reserved -= release_qty
        r.qty -= release_qty
        if r.qty == 0:
            r.active = False

    def stock(self, sku):
        return self.stocks[sku]

    def available(self, sku):
        s = self.stocks[sku]
        return s.total - s.reserved

# Repro steps from code_context
wh = Warehouse()
wh.receive("WID-100", 100)
r = wh.reserve("WID-100", 10)
wh.release(r.id, 25)          # only 10 were ever held
print(wh.stock("WID-100").reserved)  # should not go negative
print(wh.available("WID-100"))       # should not exceed 100
