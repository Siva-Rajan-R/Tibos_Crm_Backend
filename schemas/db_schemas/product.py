from pydantic import BaseModel,EmailStr
from core.data_formats.enums.product_enums import ProductTypes
from typing import Optional,Union

class AddProductDbSchema(BaseModel):
    lui_id:Optional[str]=None
    id:str
    ui_id:str
    name:str
    description:str
    price:float
    available_qty:int
    part_number:str
    product_type:str
    
class UpdateProductDbSchema(BaseModel):
    product_id:str
    name:Optional[str]=None
    description:Optional[str]=None
    price:Optional[float]=None
    available_qty:Optional[int]=None
    product_type:Optional[str]=None
    part_number:Optional[str]=None