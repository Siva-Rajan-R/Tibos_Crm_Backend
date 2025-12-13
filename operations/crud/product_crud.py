from globals.fastapi_globals import HTTPException
from database.models.pg_models.product import Products,ProductTypes
from utils.uuid_generator import generate_uuid
from sqlalchemy import select,delete,update,or_,cast,String,func,Float
from sqlalchemy.ext.asyncio import AsyncSession
from icecream import ic
from data_formats.enums.common_enums import UserRoles
from operations.abstract_models.crud_model import BaseCrud
from math import ceil



class ProductsCrud(BaseCrud):
    def __init__(self,session:AsyncSession,user_role:UserRoles):
        self.session=session
        self.user_role=user_role
        self.low_qty_thershold=5

        if self.user_role==UserRoles.USER.value:
            raise HTTPException(
                status_code=401,
                detail="Not a valid user"
            )

    async def add(self,name:str,description:str,price:float,ava_qty:int,product_type:ProductTypes):
        try:
            async with self.session.begin():
                product_id=generate_uuid(data=name)
                prod_toadd=Products(
                    id=product_id,
                    name=name,
                    description=description,
                    available_qty=ava_qty,
                    price=price,
                    product_type=product_type.value
                )

                self.session.add(prod_toadd)

                return "Successfully Product Added"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while adding products {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while adding products {e}"
            )
        
    async def update(self,product_id:str,name:str,description:str,price:float,ava_qty:int,product_type:ProductTypes):
        try:
            async with self.session.begin():
                prod_toupdate=update(Products).where(Products.id==product_id).values(
                    name=name,
                    description=description,
                    price=price,
                    available_qty=ava_qty,
                    product_type=product_type.value
                ).returning(Products.id)

                product_id=(await self.session.execute(prod_toupdate)).scalar_one_or_none()

                if not product_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Product Id"
                    )
                
                return "Product Update Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while updating product {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while updating product {e}"
            )
        
    async def delete(self,product_id:str):
        try:
            async with self.session.begin():
                prod_todelete=delete(Products).where(Products.id==product_id).returning(Products.id)

                product_id=(await self.session.execute(prod_todelete)).scalar_one_or_none()

                if not product_id:
                    raise HTTPException(
                        status_code=404,
                        detail="Invalid Product Id"
                    )
                
                return "Product Deleted Successfully"
        
        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while Deleting product {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while Deleting product {e}"
            )
        
    async def get(self,offset:int=1,limit:int=10,query:str=''):
        try:
            search_term=f"%{query.lower()}%"
            cursor=(offset-1)*limit
            queried_products=(await self.session.execute(
                select(
                    Products.id,
                    Products.name,
                    Products.description,
                    Products.available_qty.label('quantity'),
                    Products.price,
                    Products.product_type
                )
                .limit(limit)
                .order_by(Products.name)
                .where(
                    or_(
                        Products.id.ilike(search_term),
                        Products.name.ilike(search_term),
                        Products.description.ilike(search_term),
                        Products.product_type.ilike(search_term)
                    ),
                    Products.sequence_id>cursor

                )
            )).mappings().all()

            total_products:int=0
            low_qty:int=0
            if offset == 1:
                total_products=(await self.session.execute(
                    select(func.count(Products.id))
                )).scalar_one_or_none()

                low_qty=(await self.session.execute(
                    select(func.count()).select_from(Products).where(Products.available_qty<=self.low_qty_thershold)
                )).scalar()

            return {
                'products':queried_products,
                'total_products':total_products,
                'total_pages':ceil(total_products/limit),
                'low_quantites':low_qty
            }
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching all product {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching all product {e}"
            )
    
    async def search(self, query: str):
        try:
            search_term = f"%{query.lower()}%"

            result = await self.session.execute(
                select(
                    Products.id,
                    Products.name,
                    Products.price.label("price")
                )
                .where(
                    or_(
                        Products.name.ilike(search_term),
                        Products.description.ilike(search_term),
                        cast(Products.product_type, String).ilike(search_term),
                    )
                )
                .order_by(Products.name)
                .limit(5)
            )

            products = result.mappings().all()
            ic(products)
            return {"products": products}

        except HTTPException:
            raise

        except Exception as e:
            ic(f"Something went wrong while searching product: {e}")
            raise HTTPException(
                status_code=500,
                detail="Something went wrong while searching product",
            )
        
    async def get_by_id(self,product_id:str):
        try:
            ic("pro6t6t6")
            queried_products=(await self.session.execute(
                select(
                    Products.id,
                    Products.name,
                    Products.description,
                    Products.available_qty.label('quantity'),
                    Products.price,
                    Products.product_type
                )
                .where(Products.id==product_id)
                .order_by(Products.name)
            )).mappings().one_or_none()

            return {'product':queried_products}
        
        except HTTPException:
            raise
        
        except Exception as e:
            ic(f"Something went wrong while fetching single product {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Something went wrong while fetching single product {e}"
            )



