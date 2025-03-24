import frappe
from frappe.utils import add_days, today



def create_quotation(customer, items):
    print("🚀 Creating Quotation...")  # ✅ Print Start
    
    try:
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",  # ✅ Mandatory field
            "party_name": customer,
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "rate": item.get("rate", 0)  # ✅ Add rate fallback
                } for item in items
            ]
        })
        
        print(f"📌 Quotation Draft Created: {quotation.as_dict()}")  # ✅ Print Draft
        
        quotation.insert()
        print(f"✅ Quotation Inserted: {quotation.name}")  # ✅ After Insert
        
        quotation.submit()  # ✅ Submit immediately to trigger hooks
        print(f"✅ Quotation Submitted: {quotation.name}")  # ✅ After Submit
        
        frappe.db.commit()
        print(f"✅ Quotation Committed to DB: {quotation.name}")  # ✅ After Commit

        return quotation.name

    except Exception as e:
        print(f"❌ Error: {e}")  # ✅ Print Errors
        frappe.log_error(f"Error Creating Quotation: {str(e)}")
        return None
 

