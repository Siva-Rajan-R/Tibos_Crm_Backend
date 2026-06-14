import asyncio
import httpx
from core.utils.token_handler import create_access_token

async def run():
    token = create_access_token({'id': '3e094532-1ceb-5ddb-8c17-598a207088e7', 'role': 'SUPER_ADMIN', 'email': 'admin@tibos.in', 'type': 'access'})
    async with httpx.AsyncClient() as client:
        res = await client.put(
            'http://127.0.0.1:8000/api/v1/product', 
            json={'product_id': 'e38f5c96-2e40-5bdc-81e9-62799f75f190', 'name': 'TEST-PRODUCT', 'price': 2300.0, 'available_qty': 10, 'product_type': 'Software', 'part_number': '12345', 'description': 'desc'}, 
            headers={'Authorization': f'Bearer {token}'}
        )
        print(res.json())

asyncio.run(run())
