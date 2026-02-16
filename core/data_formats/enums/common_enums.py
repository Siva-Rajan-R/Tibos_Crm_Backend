from enum import Enum

class UserRoles(Enum):
    ADMIN="admin".upper()
    SUPER_ADMIN='super admin'.upper()
    USER="user".upper()

class EnvironmentEnum(Enum):
    DEVELOPMENT="DEVELOPMENT"
    PRODUCTION="PRODUCTION"

class IndianStatesEnum(Enum):
    ANDHRA_PRADESH = "Andhra Pradesh"
    ARUNACHAL_PRADESH = "Arunachal Pradesh"
    ASSAM = "Assam"
    BIHAR = "Bihar"
    CHHATTISGARH = "Chhattisgarh"
    GOA = "Goa"
    GUJARAT = "Gujarat"
    HARYANA = "Haryana"
    HIMACHAL_PRADESH = "Himachal Pradesh"
    JHARKHAND = "Jharkhand"
    KARNATAKA = "Karnataka"
    KERALA = "Kerala"
    MADHYA_PRADESH = "Madhya Pradesh"
    MAHARASHTRA = "Maharashtra"
    MANIPUR = "Manipur"
    MEGHALAYA = "Meghalaya"
    MIZORAM = "Mizoram"
    NAGALAND = "Nagaland"
    ODISHA = "Odisha"
    PUNJAB = "Punjab"
    RAJASTHAN = "Rajasthan"
    SIKKIM = "Sikkim"
    TAMIL_NADU = "Tamil Nadu"
    TELANGANA = "Telangana"
    TRIPURA = "Tripura"
    UTTAR_PRADESH = "Uttar Pradesh"
    UTTARAKHAND = "Uttarakhand"
    WEST_BENGAL = "West Bengal"

    # Union Territories
    ANDAMAN_NICOBAR = "Andaman and Nicobar Islands"
    CHANDIGARH = "Chandigarh"
    DADRA_NAGAR_HAVELI_DAMAN_DIU = "Dadra and Nagar Haveli and Daman and Diu"
    DELHI = "Delhi"
    JAMMU_KASHMIR = "Jammu and Kashmir"
    LADAKH = "Ladakh"
    LAKSHADWEEP = "Lakshadweep"
    PUDUCHERRY = "Puducherry"


class OwnersEnum(Enum):
    RAMESH_S="RAMESH S"
    MOHAMMED_FAROOK="MOHAMMED FAROOK"
    JAISATHISH_R="JAISATHISH R"
    PRASANNA_CHANDRAN_R="PRASANNA CHANDRAN R"
    NAGARAJ_D="NAGARAJ D"
    DANIEL_VENKAT="DANIEL VENKAT"
    SANJAYJAS_KUMAR="SANJAYJAS KUMAR"

class ImportExportTypeEnum(Enum):
    EXCEL="EXCEL"
    # CSV="CSV"

class SettingsEnum(Enum):
    EMAIL="EMAIL"