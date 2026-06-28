from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.infrastructure.database.repositories import reference_crud_repository as repo


def get_all_countries(db: Session) -> list:
    return [
        {"country_id": c.country_id, "country_name": c.country_name}
        for c in repo.get_all_countries(db)
    ]

def create_country(db: Session, country_name: str) -> dict:
    obj = repo.create_country(db, country_name.strip())
    return {"country_id": obj.country_id, "country_name": obj.country_name}

def update_country(db: Session, country_id: int, country_name: str) -> dict:
    obj = repo.update_country(db, country_id, country_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Country not found")
    return {"country_id": obj.country_id, "country_name": obj.country_name}

def delete_country(db: Session, country_id: int) -> dict:
    if not repo.delete_country(db, country_id):
        raise HTTPException(status_code=404, detail="Country not found")
    return {"deleted": True}


def get_all_cities(db: Session) -> list:
    return [
        {
            "city_id":      c.city_id,
            "city_name":    c.city_name,
            "country_id":   c.country_id,
            "country_name": c.country.country_name if c.country else None,
        }
        for c in repo.get_all_cities(db)
    ]

def create_city(db: Session, city_name: str, country_id: int) -> dict:
    obj = repo.create_city(db, city_name.strip(), country_id)
    return {"city_id": obj.city_id, "city_name": obj.city_name, "country_id": obj.country_id}

def update_city(db: Session, city_id: int, city_name: str, country_id: int) -> dict:
    obj = repo.update_city(db, city_id, city_name.strip(), country_id)
    if not obj:
        raise HTTPException(status_code=404, detail="City not found")
    return {"city_id": obj.city_id, "city_name": obj.city_name, "country_id": obj.country_id}

def delete_city(db: Session, city_id: int) -> dict:
    if not repo.delete_city(db, city_id):
        raise HTTPException(status_code=404, detail="City not found")
    return {"deleted": True}


def get_all_classes(db: Session) -> list:
    return [
        {"class_id": c.class_id, "class_name": c.class_name}
        for c in repo.get_all_classes(db)
    ]

def create_class(db: Session, class_name: str) -> dict:
    obj = repo.create_class(db, class_name.strip())
    return {"class_id": obj.class_id, "class_name": obj.class_name}

def update_class(db: Session, class_id: int, class_name: str) -> dict:
    obj = repo.update_class(db, class_id, class_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"class_id": obj.class_id, "class_name": obj.class_name}

def delete_class(db: Session, class_id: int) -> dict:
    if not repo.delete_class(db, class_id):
        raise HTTPException(status_code=404, detail="Class not found")
    return {"deleted": True}


def get_all_baggage_types(db: Session) -> list:
    return [
        {"baggage_type_id": b.baggage_type_id, "baggage_type_name": b.baggage_type_name}
        for b in repo.get_all_baggage_types(db)
    ]

def create_baggage_type(db: Session, baggage_type_name: str) -> dict:
    obj = repo.create_baggage_type(db, baggage_type_name.strip())
    return {"baggage_type_id": obj.baggage_type_id, "baggage_type_name": obj.baggage_type_name}

def update_baggage_type(db: Session, baggage_type_id: int, baggage_type_name: str) -> dict:
    obj = repo.update_baggage_type(db, baggage_type_id, baggage_type_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Baggage type not found")
    return {"baggage_type_id": obj.baggage_type_id, "baggage_type_name": obj.baggage_type_name}

def delete_baggage_type(db: Session, baggage_type_id: int) -> dict:
    if not repo.delete_baggage_type(db, baggage_type_id):
        raise HTTPException(status_code=404, detail="Baggage type not found")
    return {"deleted": True}


def get_all_baggage_rules(db: Session) -> list:
    return [
        {
            "baggage_pricing_rule_id": r.baggage_pricing_rule_id,
            "baggage_type_id":         r.baggage_type_id,
            "baggage_type_name":       r.baggage_type.baggage_type_name if r.baggage_type else None,
            "baggage_dimension":       r.baggage_dimension,
            "baggage_max_weight":      float(r.baggage_max_weight) if r.baggage_max_weight else None,
            "overweight_fee_per_kg":   float(r.overweight_fee_per_kg) if r.overweight_fee_per_kg else None,
        }
        for r in repo.get_all_baggage_rules(db)
    ]

def create_baggage_rule(
    db: Session,
    baggage_type_id:       int,
    baggage_dimension:     str | None,
    baggage_max_weight:    float,
    overweight_fee_per_kg: float,
) -> dict:
    obj = repo.create_baggage_rule(
        db, baggage_type_id, baggage_dimension,
        baggage_max_weight, overweight_fee_per_kg,
    )
    return {"baggage_pricing_rule_id": obj.baggage_pricing_rule_id}

def update_baggage_rule(
    db: Session,
    rule_id:               int,
    baggage_type_id:       int,
    baggage_dimension:     str | None,
    baggage_max_weight:    float,
    overweight_fee_per_kg: float,
) -> dict:
    obj = repo.update_baggage_rule(
        db, rule_id, baggage_type_id, baggage_dimension,
        baggage_max_weight, overweight_fee_per_kg,
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Baggage rule not found")
    return {"baggage_pricing_rule_id": obj.baggage_pricing_rule_id}

def delete_baggage_rule(db: Session, rule_id: int) -> dict:
    if not repo.delete_baggage_rule(db, rule_id):
        raise HTTPException(status_code=404, detail="Baggage rule not found")
    return {"deleted": True}


def get_all_terminal_types(db: Session) -> list:
    return [
        {"terminal_type_id": t.terminal_type_id, "terminal_type_name": t.terminal_type_name}
        for t in repo.get_all_terminal_types(db)
    ]

def get_terminal_type(db: Session, terminal_type_id: int) -> dict:
    obj = repo.get_terminal_type(db, terminal_type_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Terminal type not found")
    return {"terminal_type_id": obj.terminal_type_id, "terminal_type_name": obj.terminal_type_name}

def create_terminal_type(db: Session, terminal_type_name: str) -> dict:
    obj = repo.create_terminal_type(db, terminal_type_name.strip())
    return {"terminal_type_id": obj.terminal_type_id, "terminal_type_name": obj.terminal_type_name}

def update_terminal_type(db: Session, terminal_type_id: int, terminal_type_name: str) -> dict:
    obj = repo.update_terminal_type(db, terminal_type_id, terminal_type_name.strip())
    if not obj:
        raise HTTPException(status_code=404, detail="Terminal type not found")
    return {"terminal_type_id": obj.terminal_type_id, "terminal_type_name": obj.terminal_type_name}

def delete_terminal_type(db: Session, terminal_type_id: int) -> dict:
    if not repo.delete_terminal_type(db, terminal_type_id):
        raise HTTPException(status_code=404, detail="Terminal type not found")
    return {"deleted": True}