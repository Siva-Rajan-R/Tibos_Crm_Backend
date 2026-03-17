from infras.search_engine.models import customer
from sqlalchemy import select
from infras.primary_db.models.customer import Customers
from infras.primary_db.models import contact,product,order,leads,opportunity,distributor,user
from infras.primary_db.models.product import Products
from infras.primary_db.models.distributor import Distributors
from infras.primary_db.models.contact import Contacts
from infras.primary_db.main import AsyncLocalSession
from infras.search_engine.models.customer import CustomerSearch,ES
from infras.search_engine.models.distributor import DistributorSearch
from infras.search_engine.models.product import ProductSearch
from infras.search_engine.models.contact import ContactSearch
from infras.primary_db.models.order import Orders
import asyncio,json

from customersSearchFields import customer_data
from distributorsSearchFields import distri_data
from productsSearchFields import product_data
from contactsSearchFields import contact_data


# async def get_customer():
#     async with AsyncLocalSession() as session:
#         res = (await session.execute(
#             select(
#                 Customers.id,
#                 Customers.ui_id,
#                 Customers.name,
#                 Customers.email,
#                 Customers.mobile_number,
#                 Customers.tenant_id,
#                 Customers.secondary_domain,
#                 Customers.sector,
#                 Customers.industry
#             )
#         )).mappings().all()

#         res = [dict(row) for row in res]   # convert RowMapping -> dict

#         with open('customersSearchFields.py', 'w', encoding="utf-8") as file:
#             json.dump(res, file, indent=2)

# asyncio.run(get_customer())

# async def get_product():
#     async with AsyncLocalSession() as session:
#         res = (await session.execute(
#             select(
#                 Products.id,
#                 Products.ui_id,
#                 Products.name,
#                 Products.description,
#                 Products.price,
#                 Products.product_type,
#                 Products.part_number
#             )
#         )).mappings().all()

#         res = [dict(row) for row in res]   # convert RowMapping -> dict

#         with open('productsSearchFields.py', 'w', encoding="utf-8") as file:
#             json.dump(res, file, indent=2)

# asyncio.run(get_product())


# async def get_distributor():
#     async with AsyncLocalSession() as session:
#         res = (await session.execute(
#             select(
#                 Distributors.id,
#                 Distributors.ui_id,
#                 Distributors.name
#             )
#         )).mappings().all()

#         res = [dict(row) for row in res]   # convert RowMapping -> dict

#         with open('distributorsSearchFields.py', 'w', encoding="utf-8") as file:
#             json.dump(res, file, indent=2)

# asyncio.run(get_distributor())

# async def get_contact():
#     async with AsyncLocalSession() as session:
#         res = (await session.execute(
#             select(
#                 Contacts.id,
#                 Contacts.ui_id,
#                 Contacts.name,
#                 Contacts.customer_id,
#                 Contacts.email,
#                 Contacts.mobile_number,
#                 Customers.name.label("customer_name"),
#                 Customers.email.label("customer_email")
#             ).join(Customers,Customers.id==Contacts.customer_id)
#         )).mappings().all()

#         res = [dict(row) for row in res]   # convert RowMapping -> dict

#         with open('contactsSearchFields.py', 'w', encoding="utf-8") as file:
#             json.dump(res, file, indent=2)

# asyncio.run(get_contact())

# async def get_order():
#     async with AsyncLocalSession() as session:
#         res = (await session.execute(
#             select(
#                 Orders.id,
#                 Orders.ui_id,
#                 Orders.customer_id,
#                 Orders.product_id,
#                 Orders.distributor_id,
#                 Orders.discount_id,
#                 Customers.ui_id.label("customer_ui_id"),
#                 Customers.name.label("customer_name"),
#                 Customers.email.label("customer_email"),
#                 Products.ui_id.label("product_ui_id"),
#                 Products.name.label("product_name"),
#                 Products.product_type.label("product_type"),
#                 Distributors.ui_id.label("distributor_ui_id"),
#                 Distributors.name.label("distributor_name")
                
#             )
#             .select_from(Orders)
#             .join(Customers,Customers.id==Orders.customer_id,isouter=True)
#             .join(Products,Products.id==Orders.product_id,isouter=True)
#             .join(Distributors,Distributors.id==Orders.distributor_id,isouter=True)

#         )).mappings().all()

#         res = [dict(row) for row in res]   # convert RowMapping -> dict

#         with open('ordersSearchFields.py', 'w', encoding="utf-8") as file:
#             json.dump(res, file, indent=2)

# asyncio.run(get_order())


# async def insert_bulk():
#     obj=ContactSearch()
#     await obj.create_index()

#     res=await obj.create_bulk_doc(
#         datas=contact_data
#     )

#     print(res)
# asyncio.run(insert_bulk())


# async def delete_all():
#     indices = await ES.cat.indices(format="json")

#     for idx in indices:
#         await ES.indices.delete(index=idx["index"])

#     await ES.close()

# asyncio.run(delete_all())

# async def search():
#     cs_obj=ProductSearch()
#     res=await cs_obj.search_document(query="basic",limit=30,page=1)
#     print(res)

# asyncio.run(search())

# async def get_all():
#     cs_obj=Customers()
#     res=await ES.search(index="customers",query={"multi_match":{"query":"380","fields":['ui_id']}})
#     print(res)
#     return res

# asyncio.run(get_all())

a=10
b=10.4

print(a*b)