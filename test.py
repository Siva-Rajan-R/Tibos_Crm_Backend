import asyncpg
import asyncio

async def main():
    conn = await asyncpg.connect(
        host="tibos-crm-database.rs-08d5d6fa71eb.postgres.database.azure.com",
        port=5432,
        user="TibosCrmDatabase",
        password="AzureCRMDatabase#437734#1234#",
        database="postgres",
        ssl="require"
    )
    print("CONNECTED SUCCESSFULLY")


asyncio.run(main())