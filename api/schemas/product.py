from pydantic import BaseModel,EmailStr
from data_formats.enums.pg_enums import ProductTypes

class AddProductSchema(BaseModel):
    name:str
    description:str
    price:float
    available_qty:int
    product_type:ProductTypes

class UpdateProductSchema(BaseModel):
    product_id:str
    name:str
    description:str
    price:float
    available_qty:int
    product_type:ProductTypes