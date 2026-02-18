# import pandas as pd
# from infras.primary_db.main import AsyncLocalSession
# from infras.primary_db.models.order import Orders
# from sqlalchemy import text,select,update
# import asyncio
# from core.data_formats.typed_dicts.order_typdict import StatusInfo,LogisticsInfo
# from infras.primary_db.models import customer,product,user,contact,settings,distributor,leads,dropdown,opportunity



# # results=[]

# # async def scripts():

# #     stmt = text(
# #         """
# #         SELECT 
# #             id,
# #             purchase_type,
# #             payment_status,
# #             invoice_status,
# #             invoice_number,
# #             invoice_date,
# #             renewal_type,
# #             bill_to,
# #             distributor_type,
# #             discount
        
# #         FROM orders
# #         """
# #     )

# #     async with AsyncLocalSession() as session:
# #         result = await session.execute(stmt)
# #         rows = result.mappings().all()
# #     print()
# #     for row in rows:
# #         status_info=StatusInfo(
# #             payment_status=row['payment_status'],
# #             invoice_status=row['invoice_status'],
# #             invoice_date=row['invoice_date'],
# #             invoice_number=row['invoice_number']
# #         )
# #         logistic_info=LogisticsInfo(
# #             purchase_type=row['purchase_type'],
# #             renewal_type=row['renewal_type'],
# #             bill_to=row['bill_to'],
# #             distributor_type=row['distributor_type']
# #         )

# #         additional_discount=row['discount']

# #         data={'id':row['id'],'status_info':status_info,'logistic_info':logistic_info,'additional_discount':additional_discount}
# #         print(data)
# #         results.append(data)


# # asyncio.run(scripts())
# # print(results)
# # print(len(results))

# # df=pd.DataFrame(results)
# # df.to_excel('results.xlsx',index=False)


# async def reupload():
#     ex=pd.read_excel('results.xlsx')
#     df=pd.DataFrame(ex)
#     converted_data=df.to_dict('records')
#     completed_count=0
#     async with AsyncLocalSession() as session:
#         for i in converted_data:
#             print(i)
#             i['additional_discount']=str(i['additional_discount'])
#             data_toupdate=update(Orders).where(Orders.id==i['id']).values(logistic_info=eval(i['logistic_info']),status_info=eval(i['status_info']),additional_discount=i['additional_discount']).returning(Orders.id)
#             is_updated=(await session.execute(data_toupdate)).scalar_one_or_none()
#             completed_count+=1
#             print(is_updated)
#         print(completed_count)

#         await session.commit()

# asyncio.run(reupload())

