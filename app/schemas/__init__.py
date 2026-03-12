from .city_schema import CityDTO

from .airline_schema import AirlineDTO
from .airport_schema import AirportDTO

from .flight_schema import FlightDTO, FlightResultDTO, FlightSearchResponseDTO

from .document_schema import PassengerDocumentDTO
from .passenger_schema import PassengerDTO, PassengerCreateDTO, PassengerUpdateDTO

from .payment_schema import PaymentDTO
from .booking_schema import BaggageItemDTO, BookingPassengerDTO, CreateBookingDTO, BookingResponseDTO

from .baggage_schema import BaggageUnitInputDTO, BaggageSurchargeDTO, BaggageCheckDTO
from .seat_schema import SeatDTO, SeatMapDTO

from .checkin_schema import DocumentInfoDTO, BookingItemDTO, BookingDetailsDTO, CheckinPaymentInputDTO, IssueBoardingPassDTO
from .boarding_pass_schema import BoardingPassDTO