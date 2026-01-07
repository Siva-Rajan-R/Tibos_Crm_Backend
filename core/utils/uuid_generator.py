import uuid
from icecream import ic
from fastapi.exceptions import HTTPException

def generate_uuid(data:str=uuid.uuid4().__str__())->str:
    """It will get a string data and generate a random uuid5 based id"""
    try:
        return uuid.uuid5(uuid.uuid4(),name=data).__str__()
    
    except Exception as e:
        ic(f"something went wrong while generating uuid {e}")
        raise HTTPException(
            status_code=500,
            detail=f"something went wrong while generating uuid {e}"
        )