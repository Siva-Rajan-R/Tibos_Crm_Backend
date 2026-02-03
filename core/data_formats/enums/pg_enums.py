from enum import Enum

class ProductTypes(Enum):
    GOOGLE = "Google".upper()
    AMAZON = "Amazon".upper()
    HARDWARE = "Hardware".upper()
    MICROSOFT = "Microsoft".upper()
    OTHERS = "Others".upper()
    ZOHO = "Zoho".upper()

class PaymentStatus(Enum):
    PAID ='paid'.upper()
    NOT_PAID = "not paid".upper()
    TDS_PENDING="TDS PENDING"
    FULL_PAYMENT_RECEIVED="FULL PAYMENT RECEIVED"
    HALF_PAYMENT_RECEIVED="HALF PAYMENT RECEIVED"
    SHORT_PAYMENT_RECEIVED="SHORT PAYMENT RECEIVED"
    GST_PENDING="GST PENDING"



class InvoiceStatus(Enum):
    COMPLETED='completed'.upper()
    INCOMPLETED='incompleted'.upper()


class CustomerIndustries(Enum):
    AGRICULTURE = "Agriculture"
    AUTOMOTIVE = "Automotive"
    AVIATION = "Aviation & Aerospace"
    BANKING = "Banking"
    BIOTECHNOLOGY = "Biotechnology"
    CHEMICALS = "Chemicals"
    CONSTRUCTION = "Construction"
    CONSUMER_GOODS = "Consumer Goods"
    DEFENSE = "Defense"
    EDUCATION = "Education"
    ENERGY = "Energy"
    ENGINEERING = "Engineering"
    ENTERTAINMENT = "Entertainment & Media"
    ENVIRONMENTAL = "Environmental Services"
    FINANCIAL_SERVICES = "Financial Services"
    FOOD_BEVERAGE = "Food & Beverage"
    GOVERNMENT = "Government"
    HEALTHCARE = "Healthcare"
    HOSPITALITY = "Hospitality"
    INSURANCE = "Insurance"
    IT_SERVICES = "IT Services"
    LEGAL = "Legal Services"
    LOGISTICS = "Logistics & Supply Chain"
    MANUFACTURING = "Manufacturing"
    MARKETING = "Marketing & Advertising"
    MINING = "Mining"
    NON_PROFIT = "Non-Profit"
    PHARMACEUTICALS = "Pharmaceuticals"
    PROFESSIONAL_SERVICES = "Professional Services"
    REAL_ESTATE = "Real Estate"
    RETAIL = "Retail"
    TELECOMMUNICATIONS = "Telecommunications"
    TEXTILES = "Textiles & Apparel"
    TOURISM = "Tourism & Travel"
    TRANSPORTATION = "Transportation"
    UTILITIES = "Utilities"
    WHOLESALE = "Wholesale"
    SOFTWARE = "Software & SaaS"
    ECOMMERCE = "E-Commerce"
    CYBERSECURITY = "Cybersecurity"
    DATA_ANALYTICS = "Data & Analytics"
    ARTIFICIAL_INTELLIGENCE = "Artificial Intelligence"
    BLOCKCHAIN = "Blockchain & Web3"
    IOT = "Internet of Things (IoT)"
    GAMING = "Gaming"
    SPORTS = "Sports"
    FASHION = "Fashion"
    MARITIME = "Maritime"
    SPACE = "Space Technology"
    OTHER = "Other"

class CustomerSectors(Enum):
    PRIVATE="private".upper()
    PUBLIC='public'.upper()

class ShippingMethods(Enum):
    ONLINE ='online'.upper()
    OFFLINE ='offline'.upper()

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

class RenewalTypes(Enum):
    YEARLY_BILL="YEARLY-BILL"
    MONTHLY_BILL="MONTHLY-BILL"
    HALFLY_BILL='HALFLY-BILL'

class PurchaseTypes(Enum):
    NEW_LOGO_RENEWAL="NEW-LOGO-RENEWAL"
    NET_NEW_CUSTOMER="NET-NEW-CUSTOMER"
    EXISTING_RENEWAL="EXISTING-RENEWAL"
    EXISTING_ADD_ON="EXISTING-ADD-ON"

