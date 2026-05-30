from datetime import date
from icecream import ic
from core.constants import UI_ID_STARTING_DIGIT

# UI_ID_STARTING_DIGIT="100000"
def generate_ui_id(prefix:str,last_id:str|None=None):
    cur_year=date.today().year.__str__()
    if not last_id:
        return f"{prefix}-T-{cur_year}-{UI_ID_STARTING_DIGIT}"
    
    try:
        extracted_last_id=last_id.split('-')
        ic(extracted_last_id)
        ic(cur_year)
        
        # If it's malformed, fall back to new sequence starting digit
        if len(extracted_last_id) != 4:
            return f"{prefix}-T-{cur_year}-{UI_ID_STARTING_DIGIT}"
            
        # Continue sequence even if prefix changed (e.g. CARTORD to ORD transition)
        last_seq_str = extracted_last_id[-1]
        last_year_str = extracted_last_id[2]
        
        if last_year_str == cur_year:
            cur_id = f"{prefix}-T-{cur_year}-{int(last_seq_str)+1}"
        else:
            cur_id = f"{prefix}-T-{cur_year}-{UI_ID_STARTING_DIGIT}"
            
        return cur_id
    except Exception as e:
        ic(e)
        return f"{prefix}-T-{cur_year}-{UI_ID_STARTING_DIGIT}"


if __name__ == "__main__":
    ic(generate_ui_id("ORD",'ORD-T-2026-999999'))



    