from sqlalchemy.orm import Session
from app.infrastructure.database.models.airport_model import City, Country
from app.infrastructure.database.models.seat_model import Class
from app.infrastructure.database.models.airport_model import TerminalType
from app.infrastructure.database.models.baggage_model import BaggageType, BaggagePricingRule



def get_all_countries(db: Session) -> list:
    return db.query(Country).order_by(Country.country_name).all()

def get_country(db: Session, country_id: int) -> Country | None:
    return db.query(Country).filter(Country.country_id == country_id).first()

def create_country(db: Session, country_name: str) -> Country:
    obj = Country(country_name=country_name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_country(db: Session, country_id: int, country_name: str) -> Country | None:
    obj = get_country(db, country_id)
    if not obj:
        return None
    obj.country_name = country_name
    db.commit()
    db.refresh(obj)
    return obj

def delete_country(db: Session, country_id: int) -> bool:
    obj = get_country(db, country_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_cities(db: Session) -> list:
    return db.query(City).join(Country).order_by(City.city_name).all()

def get_city(db: Session, city_id: int) -> City | None:
    return db.query(City).filter(City.city_id == city_id).first()

def create_city(db: Session, city_name: str, country_id: int) -> City:
    obj = City(city_name=city_name, country_id=country_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_city(db: Session, city_id: int, city_name: str, country_id: int) -> City | None:
    obj = get_city(db, city_id)
    if not obj:
        return None
    obj.city_name = city_name
    obj.country_id = country_id
    db.commit()
    db.refresh(obj)
    return obj

def delete_city(db: Session, city_id: int) -> bool:
    obj = get_city(db, city_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_classes(db: Session) -> list:
    return db.query(Class).order_by(Class.class_name).all()

def get_class(db: Session, class_id: int) -> Class | None:
    return db.query(Class).filter(Class.class_id == class_id).first()

def create_class(db: Session, class_name: str) -> Class:
    obj = Class(class_name=class_name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_class(db: Session, class_id: int, class_name: str) -> Class | None:
    obj = get_class(db, class_id)
    if not obj:
        return None
    obj.class_name = class_name
    db.commit()
    db.refresh(obj)
    return obj

def delete_class(db: Session, class_id: int) -> bool:
    obj = get_class(db, class_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_baggage_types(db: Session) -> list:
    return db.query(BaggageType).order_by(BaggageType.baggage_type_name).all()

def get_baggage_type(db: Session, baggage_type_id: int) -> BaggageType | None:
    return db.query(BaggageType).filter(
        BaggageType.baggage_type_id == baggage_type_id).first()

def create_baggage_type(db: Session, baggage_type_name: str) -> BaggageType:
    obj = BaggageType(baggage_type_name=baggage_type_name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_baggage_type(db: Session, baggage_type_id: int,
                        baggage_type_name: str) -> BaggageType | None:
    obj = get_baggage_type(db, baggage_type_id)
    if not obj:
        return None
    obj.baggage_type_name = baggage_type_name
    db.commit()
    db.refresh(obj)
    return obj

def delete_baggage_type(db: Session, baggage_type_id: int) -> bool:
    obj = get_baggage_type(db, baggage_type_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_baggage_rules(db: Session) -> list:
    return db.query(BaggagePricingRule).join(BaggageType).order_by(
        BaggageType.baggage_type_name, BaggagePricingRule.baggage_max_weight).all()

def get_baggage_rule(db: Session, rule_id: int) -> BaggagePricingRule | None:
    return db.query(BaggagePricingRule).filter(
        BaggagePricingRule.baggage_pricing_rule_id == rule_id).first()

def create_baggage_rule(
    db: Session,
    baggage_type_id: int,
    baggage_dimension: str | None,
    baggage_max_weight: float,
) -> BaggagePricingRule:
    obj = BaggagePricingRule(
        baggage_type_id=baggage_type_id,
        baggage_dimension=baggage_dimension,
        baggage_max_weight=baggage_max_weight,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_baggage_rule(
    db: Session,
    rule_id: int,
    baggage_type_id: int,
    baggage_dimension: str | None,
    baggage_max_weight: float,
    overweight_fee_per_kg: float,
) -> BaggagePricingRule | None:
    obj = get_baggage_rule(db, rule_id)
    if not obj:
        return None
    obj.baggage_type_id = baggage_type_id
    obj.baggage_dimension = baggage_dimension
    obj.baggage_max_weight = baggage_max_weight
    obj.overweight_fee_per_kg = overweight_fee_per_kg
    db.commit()
    db.refresh(obj)
    return obj

def delete_baggage_rule(db: Session, rule_id: int) -> bool:
    obj = get_baggage_rule(db, rule_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def get_all_terminal_types(db: Session) -> list:
    return db.query(TerminalType).order_by(TerminalType.terminal_type_name).all()

def get_terminal_type(db: Session, terminal_type_id: int) -> TerminalType | None:
    return db.query(TerminalType).filter(
        TerminalType.terminal_type_id == terminal_type_id).first()

def create_terminal_type(db: Session, terminal_type_name: str) -> TerminalType:
    obj = TerminalType(terminal_type_name=terminal_type_name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_terminal_type(db: Session, terminal_type_id: int,
                         terminal_type_name: str) -> TerminalType | None:
    obj = get_terminal_type(db, terminal_type_id)
    if not obj:
        return None
    obj.terminal_type_name = terminal_type_name
    db.commit()
    db.refresh(obj)
    return obj

def delete_terminal_type(db: Session, terminal_type_id: int) -> bool:
    obj = get_terminal_type(db, terminal_type_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True



