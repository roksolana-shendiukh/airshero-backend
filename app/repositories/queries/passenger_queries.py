from sqlalchemy import text

GET_ALL_PASSENGERS = text("""
    SELECT * FROM (
        SELECT
            ROW_NUMBER() OVER (ORDER BY p.passenger_last_name, p.passenger_first_name) AS rn,
            p.passenger_id,
            p.passenger_first_name,
            p.passenger_last_name,
            p.passenger_sex,
            p.passenger_email,
            p.passenger_date_of_birth,
            pd.passenger_document_id,
            pd.citizenship_id,
            ci.citizenship_name,
            pd.document_type_id,
            dt.document_type_name,
            pd.document_number,
            pd.document_date_of_issue,
            pd.document_date_of_expire
        FROM Passenger p
        LEFT JOIN PassengerDocument pd ON p.passenger_id = pd.passenger_id
        LEFT JOIN DocumentType dt ON pd.document_type_id = dt.document_type_id
        LEFT JOIN Citizenship ci ON pd.citizenship_id = ci.citizenship_id
    ) t
    WHERE rn > :skip AND rn <= :skip + :limit
""")

GET_PASSENGER_BY_ID = text("""
    SELECT
        p.passenger_id,
        p.passenger_first_name,
        p.passenger_last_name,
        p.passenger_sex,
        p.passenger_email,
        p.passenger_date_of_birth,
        pd.passenger_document_id,
        pd.citizenship_id,
        ci.citizenship_name,
        pd.document_type_id,
        dt.document_type_name,
        pd.document_number,
        pd.document_date_of_issue,
        pd.document_date_of_expire
    FROM Passenger p
    LEFT JOIN PassengerDocument pd ON p.passenger_id = pd.passenger_id 
    LEFT JOIN DocumentType dt ON pd.document_type_id = dt.document_type_id
    LEFT JOIN Citizenship ci ON pd.citizenship_id = ci.citizenship_id
    WHERE p.passenger_id = :passenger_id
""")

CREATE_PASSENGER = text("""
    INSERT INTO Passenger (
        passenger_first_name,
        passenger_last_name,
        passenger_sex,
        passenger_email,
        passenger_date_of_birth
    )
    OUTPUT INSERTED.passenger_id
    VALUES (
        :first_name,
        :last_name,
        :sex,
        :email,
        :date_of_birth
    )
""")

CREATE_DOCUMENT = text("""
    INSERT INTO PassengerDocument (
        passenger_id,
        citizenship_id,
        document_type_id,
        document_number,
        document_date_of_issue,
        document_date_of_expire
    )
    VALUES (
        :passenger_id,
        :citizenship_id,
        :document_type_id,
        :document_number,
        :document_date_of_issue,
        :document_date_of_expire
    )
""")

UPDATE_PASSENGER = text("""
    UPDATE Passenger SET
        passenger_first_name    = COALESCE(:first_name,    passenger_first_name),
        passenger_last_name     = COALESCE(:last_name,     passenger_last_name),
        passenger_sex           = COALESCE(:sex,           passenger_sex),
        passenger_email         = COALESCE(:email,         passenger_email),
        passenger_date_of_birth = COALESCE(:date_of_birth, passenger_date_of_birth)
    WHERE passenger_id = :passenger_id
""")

UPDATE_DOCUMENT = text("""
    UPDATE PassengerDocument SET
        citizenship_id          = COALESCE(:citizenship_id,   citizenship_id),
        document_type_id        = COALESCE(:document_type_id, document_type_id),
        document_number         = COALESCE(:document_number,  document_number),
        document_date_of_issue  = COALESCE(:date_of_issue,    document_date_of_issue),
        document_date_of_expire = COALESCE(:date_of_expire,   document_date_of_expire)
    WHERE passenger_id = :passenger_id
""")

CHECK_DOCUMENT_EXISTS = text("""
    SELECT passenger_document_id FROM PassengerDocument
    WHERE passenger_id = :passenger_id
""")

DELETE_PASSENGER = text("""
    DELETE FROM Passenger
    WHERE passenger_id = :passenger_id
""")

DELETE_PASSENGER_DOCUMENT = text("""
    DELETE FROM PassengerDocument
    WHERE passenger_id = :passenger_id
""")

CHECK_PASSENGER_EXISTS = text("""
    SELECT passenger_id FROM Passenger
    WHERE passenger_id = :passenger_id
""")

SEARCH_PASSENGER_BY_DOCUMENT = text("""
    SELECT
        p.passenger_id,
        p.passenger_first_name,
        p.passenger_last_name,
        p.passenger_sex,
        p.passenger_email,
        p.passenger_date_of_birth,
        pd.passenger_document_id,
        pd.citizenship_id,
        ci.citizenship_name,
        pd.document_type_id,
        dt.document_type_name,
        pd.document_number,
        pd.document_date_of_issue,
        pd.document_date_of_expire
    FROM Passenger p
    LEFT JOIN PassengerDocument pd ON p.passenger_id = pd.passenger_id
    LEFT JOIN Citizenship ci ON pd.citizenship_id = ci.citizenship_id
    LEFT JOIN DocumentType dt ON pd.document_type_id = dt.document_type_id
    WHERE pd.document_number = :document_number
""")

SEARCH_PASSENGERS_BY_DOCUMENT_PARTIAL = text("""
    SELECT TOP 10
        p.passenger_id,
        p.passenger_first_name,
        p.passenger_last_name,
        pd.document_number
    FROM Passenger p
    JOIN PassengerDocument pd ON p.passenger_id = pd.passenger_id
    WHERE pd.document_number LIKE :query
    ORDER BY pd.document_number
""")

GET_DOCUMENT_TYPE_CODE = text("""
    SELECT document_type_code
    FROM DocumentType
    WHERE document_type_id = :document_type_id
""")

