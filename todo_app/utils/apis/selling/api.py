import frappe
import json
from frappe import _

@frappe.whitelist(allow_guest=False)  # Requires authentication
def create_material_receipt():
    try:
        # Get request data
        data = frappe.request.get_data(as_text=True)
        data = json.loads(data)

        # Validate required fields
        required_fields = ["item_code", "qty", "t_warehouse"]
        for field in required_fields:
            if field not in data or not data[field]:
                return {"status": "error", "message": _(f"Missing required field: {field}")}

        # Ensure stock entry type is Material Receipt
        doc = frappe.get_doc({
            "doctype": "Stock Entry",
            "stock_entry_type": "Material Receipt",
            "items": [
                {
                    "item_code": data["item_code"],
                    "qty": data["qty"],
                    "t_warehouse": data["t_warehouse"]
                }
            ]
        })

        # Insert and submit the document
        doc.insert()
        doc.submit()

        return {"status": "success", "message": "Material Receipt Created", "stock_entry": doc.name}

    except Exception as e:
        frappe.log_error(f"Material Receipt Error: {str(e)}", "Material Receipt API")
        return {"status": "error", "message": str(e)}
