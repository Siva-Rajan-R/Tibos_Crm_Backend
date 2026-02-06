from datetime import date
from icecream import ic
from core.constants import UI_ID_STARTING_DIGIT

# UI_ID_STARTING_DIGIT="100000"
def generate_ui_id(prefix:str,last_id:str|None=None):
    cur_year=date.today().year.__str__()
    if not last_id:
        cur_id=f"{prefix}-T-{cur_year}-{UI_ID_STARTING_DIGIT}"
    else:
        extracted_last_id=last_id.split('-')
        ic(extracted_last_id)
        ic(cur_year)
        if len(extracted_last_id)>4:
            return False
        
        if prefix!=extracted_last_id[0]:
            return False
        
        if extracted_last_id[2]==cur_year:
            cur_id=f"{prefix}-T-{cur_year}-{int(extracted_last_id[-1])+1}"
        else:
            cur_id=f"{prefix}-T-{cur_year}-{UI_ID_STARTING_DIGIT}"
     

    return cur_id


if __name__ == "__main__":
    ic(generate_ui_id("ORD",'ORD-T-2026-999999'))



    