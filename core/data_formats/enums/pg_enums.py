from enum import Enum

class ProductTypes(Enum):
    APPLE="apple".upper()
    ORANGE="orange".upper()

class PaymentStatus(Enum):
    PAID ='paid'.upper()
    NOT_PAID = "not paid".upper()


class InvoiceStatus(Enum):
    COMPLETED='completed'.upper()
    INCOMPLETED='incompleted'.upper()


class CustomerIndustries(Enum):
    IT="It".upper()
    AGRICULTURE="agriculture".upper()
    MANUFACTURING="manufacturing".upper()

class CustomerSectors(Enum):
    PRIVATE="private".upper()
    PUBLIC='public'.upper()

class ShippingMethods(Enum):
    MAIL='mail'.upper()
    FAX='fax'.upper()

class LeadStatus(Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    LOST = "LOST"


class BillingType(Enum):
    SUBSCRIPTION = "SUBSCRIPTION"
    ONE_TIME = "ONE_TIME"


class OpportunityStatus(Enum):
    WON = "WON"
    LOST = "LOST"


class LeadSource(Enum):
    WEBSITE = "WEBSITE"
    WHATSAPP = "WHATSAPP"
    INSTAGRAM = "INSTAGRAM"
    REFERRAL = "REFERRAL"

