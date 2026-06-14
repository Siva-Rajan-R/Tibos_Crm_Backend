import asyncio
import json
import httpx

async def run():
    # Attempt an update on the product
    # The API is PATCH /product/{id} or PUT /product
    payload = {
        "product_id": "e38f5c96-2e40-5bdc-81e9-62799f75f190",
        "price": 1200.0
    }
    async with httpx.AsyncClient() as client:
        res = await client.put("http://127.0.0.1:8000/product", json=payload)
        print("Update response:", res.status_code, res.text)
        
        # Now fetch history
        res2 = await client.get("http://127.0.0.1:8000/product/e38f5c96-2e40-5bdc-81e9-62799f75f190/pricing-history")
        print("History response:", res2.status_code, res2.text)

asyncio.run(run())
