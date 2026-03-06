from sqlalchemy import text

GET_BOOKING_STATUS_ID = text("""
    SELECT booking_status_id
    FROM BookingStatus
    WHERE booking_status_name = :name
""")

GET_PAYMENT_STATUS_ID = text("""
    SELECT payment_status_id
    FROM PaymentStatus
    WHERE payment_status_name = :name
""")

INSERT_BOOKING = text("""
    INSERT INTO Booking (booking_status_id, booking_date_time, booking_total_amount, booking_number)
    OUTPUT INSERTED.booking_id
    VALUES (
        :booking_status_id,
        GETDATE(),
        :total_amount,
        :booking_number
    )
""")

INSERT_BOOKING_ITEM = text("""
    INSERT INTO BookingItem (passenger_document_id, booking_id, flight_price_id)
    VALUES (:passenger_document_id, :booking_id, :flight_price_id)
""")

INSERT_BAGGAGE_OPTION = text("""
    INSERT INTO BaggageOptionInFlight (baggage_pricing_in_flight_id, booking_item_id, baggage_quantity)
    VALUES (:baggage_pricing_in_flight_id, :booking_item_id, :baggage_quantity)
""")

INSERT_PAYMENT = text("""
    INSERT INTO Payment (booking_id, payment_status_id, payment_method_id, payment_date_time, payment_amount)
    VALUES (:booking_id, :payment_status_id, :payment_method_id, GETDATE(), :payment_amount)
""")

UPDATE_BOOKING_STATUS = text("""
    UPDATE Booking
    SET booking_status_id = :booking_status_id
    WHERE booking_id = :booking_id
""")

GET_PAYMENT_METHODS = text("""
    SELECT payment_method_id, payment_method_name
    FROM PaymentMethod
    ORDER BY payment_method_id
""")

