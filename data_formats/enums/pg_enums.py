from enum import Enum

class ProductTypes(Enum):
    APPLE="apple"
    ORANGE="orange"

class CustomerIndustries(Enum):
    IT="It"
    AGRICULTURE="agriculture"
    MANUFACTURING="manufacturing"

class CustomerSectors(Enum):
    PRIVATE="private"
    PUBLIC='public'

class ShippingMethods(Enum):
    MAIL='mail'
    FAX='fax'
