import os
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from app.config import settings


class TicketPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", 'B', 24)
        self.set_text_color(100, 50, 200)
        self.cell(0, 15, "AirShero", ln=True, align='L')
        self.set_draw_color(100, 50, 200)
        self.set_line_width(0.8)
        self.line(10, 25, 60, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"AirShero Official Ticket | Page {self.page_no()}", align='C')


def _draw_flight_card(pdf: FPDF, title: str, data: dict) -> None:
    pdf.set_font("Helvetica", 'B', 10)
    pdf.set_text_color(100, 50, 200)
    pdf.cell(0, 8, f"  {title}", ln=True)
    pdf.set_draw_color(230, 230, 230)
    pdf.rect(10, pdf.get_y(), 190, 42)
    curr_y = pdf.get_y() + 5

    pdf.set_xy(15, curr_y)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 8, data['dep_time'], ln=True)
    pdf.set_x(15)
    pdf.set_font("Helvetica", '', 9)
    pdf.cell(50, 5, f"{data['dep_city']} ({data['dep_code']})", ln=True)
    pdf.set_x(15)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(50, 5, data['dep_date'], ln=True)

    pdf.set_xy(80, curr_y + 5)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 5, "----->", align='C')

    pdf.set_xy(145, curr_y)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(50, 8, data['arr_time'], align='R', ln=True)
    pdf.set_x(145)
    pdf.set_font("Helvetica", '', 9)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(50, 5, f"{data['arr_city']} ({data['arr_code']})", align='R', ln=True)
    pdf.set_x(145)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(50, 5, data['arr_date'], align='R', ln=True)

    pdf.set_y(curr_y + 37)


def generate_ticket_pdf_for_passenger(
    booking_id: int,
    passenger: dict,
    booking_details: dict,
    flight_info: dict,
    booking_id_2: int | None = None,
    flight_info_2: dict | None = None,
    booking_details_2: dict | None = None,
) -> str:
    os.makedirs("tickets", exist_ok=True)
    pdf = TicketPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    is_multi_segment = flight_info_2 is not None

    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(100, 10, "E-TICKET CONFIRMATION", ln=False)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_fill_color(245, 240, 255)
    pdf.set_text_color(100, 50, 200)

    if is_multi_segment:
        booking_ref = f"{booking_details['number']} + {booking_details_2['number']}"
    else:
        booking_ref = booking_details['number']

    pdf.cell(0, 10, f"  Booking ref: {booking_ref}  ", ln=True, align='R', fill=True)
    pdf.ln(5)

    # Рейси
    if is_multi_segment:
        # Перший рейс
        if flight_info.get('outbound'):
            _draw_flight_card(pdf, "FLIGHT 1 (LEG 1)", flight_info['outbound'])
        pdf.ln(5)
        # Другий рейс
        if flight_info_2 and flight_info_2.get('outbound'):
            _draw_flight_card(pdf, "FLIGHT 2 (LEG 2)", flight_info_2['outbound'])
    else:
        if flight_info.get('outbound'):
            _draw_flight_card(pdf, "OUTBOUND FLIGHT", flight_info['outbound'])
        if flight_info.get('return'):
            pdf.ln(5)
            _draw_flight_card(pdf, "RETURN FLIGHT", flight_info['return'])

    # Пасажир
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, "Passenger", ln=True)
    pdf.set_draw_color(220, 220, 220)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, passenger['name'], ln=True)

    pdf.set_font("Helvetica", '', 10)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, f"  Class: {passenger.get('class_name', 'Economy')}", ln=True)

    ticket_prices = passenger.get('ticket_prices', [])

    if is_multi_segment:
        # Для multi-segment показуємо leg1 і leg2 окремо
        labels = ['Leg 1', 'Leg 2']
        for i, price in enumerate(ticket_prices):
            label = labels[i] if i < len(labels) else f'Flight {i + 1}'
            pdf.set_font("Helvetica", '', 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(130, 6, f"  {label} ticket", ln=False)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(0, 6, f"USD {price:.2f}", ln=True, align='R')
    else:
        directions = ['Outbound', 'Return']
        for i, price in enumerate(ticket_prices):
            label = directions[i] if i < len(directions) else f'Flight {i + 1}'
            pdf.set_font("Helvetica", '', 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(130, 6, f"  {label} ticket", ln=False)
            pdf.set_font("Helvetica", 'B', 10)
            pdf.cell(0, 6, f"USD {price:.2f}", ln=True, align='R')

    if passenger.get('baggage_items'):
        for bag in passenger['baggage_items']:
            pdf.set_font("Helvetica", '', 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(130, 6, f"  + {bag['label']} x{bag['count']}", ln=False)
            pdf.cell(0, 6, f"USD {bag['price']:.2f}", ln=True, align='R')

    passenger_total = sum(ticket_prices) + sum(
        bag['price'] for bag in passenger.get('baggage_items', [])
    )
    pdf.ln(3)
    pdf.set_draw_color(100, 50, 200)
    pdf.line(130, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(100, 50, 200)
    pdf.cell(0, 12, f"Total: USD {passenger_total:.2f}", ln=True, align='R')

    safe_name = passenger['name'].replace(' ', '_')
    file_path = f"tickets/ticket_{booking_id}_{safe_name}.pdf"
    pdf.output(file_path)
    return file_path


def send_booking_confirmation_email(
    to_email: str,
    booking_id: int,
    booking_details: dict,
    flight_info: dict,
    booking_id_2: int | None = None,
    flight_info_2: dict | None = None,
    booking_details_2: dict | None = None,
) -> None:
    is_multi_segment = flight_info_2 is not None

    passengers = flight_info.get('passengers', [])
    count = len(passengers)

    msg = EmailMessage()

    if is_multi_segment:
        subject = f"AirShero Tickets - {booking_details['number']} + {booking_details_2['number']}"
        body_text = (
            f"Dear passenger,\n\n"
            f"Your payment for bookings "
            f"{booking_details['number']} and {booking_details_2['number']} was successful.\n"
            f"Please find attached {count * 2} ticket{'s' if count > 1 else ''} "
            f"— separate tickets for each flight leg.\n\n"
            f"Thank you for choosing AirShero!"
        )
    else:
        subject = f"AirShero Ticket - {booking_details['number']}"
        body_text = (
            f"Dear passenger,\n\n"
            f"Your payment for booking {booking_details['number']} was successful.\n"
            f"Please find attached {count} ticket{'s' if count > 1 else ''} "
            f"for all passengers.\n\n"
            f"Thank you for choosing AirShero!"
        )

    msg['Subject'] = subject
    msg['From'] = settings.smtp_email
    msg['To'] = to_email
    msg.set_content(body_text)

    if is_multi_segment:
        # PDF для leg-1 (окремий для кожного пасажира)
        for passenger in passengers:
            pdf_path = generate_ticket_pdf_for_passenger(
                booking_id=booking_id,
                passenger=passenger,
                booking_details=booking_details,
                flight_info=flight_info,
            )
            with open(pdf_path, 'rb') as f:
                safe_name = passenger['name'].replace(' ', '_')
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='pdf',
                    filename=f"Ticket_{booking_details['number']}_{safe_name}_Leg1.pdf",
                )

        passengers_2 = flight_info_2.get('passengers', [])
        for passenger in passengers_2:
            pdf_path = generate_ticket_pdf_for_passenger(
                booking_id=booking_id_2,
                passenger=passenger,
                booking_details=booking_details_2,
                flight_info=flight_info_2,
            )
            with open(pdf_path, 'rb') as f:
                safe_name = passenger['name'].replace(' ', '_')
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='pdf',
                    filename=f"Ticket_{booking_details_2['number']}_{safe_name}_Leg2.pdf",
                )
    else:
        for passenger in passengers:
            pdf_path = generate_ticket_pdf_for_passenger(
                booking_id=booking_id,
                passenger=passenger,
                booking_details=booking_details,
                flight_info=flight_info,
            )
            with open(pdf_path, 'rb') as f:
                safe_name = passenger['name'].replace(' ', '_')
                msg.add_attachment(
                    f.read(),
                    maintype='application',
                    subtype='pdf',
                    filename=f"Ticket_{booking_details['number']}_{safe_name}.pdf",
                )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(settings.smtp_email, settings.smtp_password)
            smtp.send_message(msg)
            print(f"[email] Tickets sent to {to_email}")
    except Exception as e:
        print(f"[email] SMTP Error: {e}")
