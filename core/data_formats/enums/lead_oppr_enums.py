from enum import Enum


class LeadStatus(Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    CONVERTED = "CONVERTED"
    LOST = "LOST"

class OpportunityStatus(Enum):
    OPEN = "OPEN"
    WON = "WON"
    LOST = "LOST"

class LeadSource(Enum):
    WEBSITE = "WEBSITE"
    WHATSAPP = "WHATSAPP"
    INSTAGRAM = "INSTAGRAM"
    REFERRAL = "REFERRAL"