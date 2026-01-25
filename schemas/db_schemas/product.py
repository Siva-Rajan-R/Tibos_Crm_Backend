from pydantic import BaseModel,EmailStr
from core.data_formats.enums.pg_enums import ProductTypes
from typing import Optional

class AddProductDbSchema(BaseModel):
    id:str
    name:str
    description:str
    price:float
    available_qty:int
    part_number:str
    product_type:ProductTypes

class UpdateProductDbSchema(BaseModel):
    product_id:str
    name:Optional[str]=None
    description:Optional[str]=None
    price:Optional[float]=None
    available_qty:Optional[int]=None
    product_type:Optional[ProductTypes]=None
    part_number:Optional[str]=None