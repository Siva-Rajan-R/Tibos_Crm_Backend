from enum import Enum


class LeadStatus(Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    LOST = "LOST"

class OpportunityStatus(Enum):
    WON = "WON"
    LOST = "LOST"

class LeadSource(Enum):
    WEBSITE = "WEBSITE"
    WHATSAPP = "WHATSAPP"
    INSTAGRAM = "INSTAGRAM"
    REFERRAL = "REFERRAL"