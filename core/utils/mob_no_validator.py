def mobile_number_validator(mob_no:str):
    if len(mob_no)!=10:
        return False

    try:
        int(mob_no)
        return True
    except:
        return False