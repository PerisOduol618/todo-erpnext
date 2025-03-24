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
 

def convert_quotation_to_sales_order(doc, event=None): 
    """
    Converts a submitted Quotation into a Sales Order
    """
    frappe.logger().info(f"🚀 Hook Triggered for Quotation: {doc.name}")  # Log to `logs/`
    frappe.msgprint(f"Hook Triggered for Quotation: {doc.name}")  # UI popup

    if doc.docstatus != 1:
        frappe.throw("Only submitted quotations can be converted")

    delivery_date = add_days(today(), 7)
    
    sales_order = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": doc.party_name,
        "delivery_date": delivery_date,
        "items": [{
            "item_code": item.item_code,
            "qty": item.qty,
            "rate": item.rate,
            "delivery_date": delivery_date
        } for item in doc.items]
    })
    
    sales_order.insert(ignore_permissions=True)
    sales_order.submit()
    frappe.db.commit()

    frappe.logger().info(f"✅ Sales Order Created: {sales_order.name}")
    frappe.msgprint(f"✅ Sales Order Created: {sales_order.name}")


def create_sales_invoice(sales_order_name, event=None):
    """
    Creates a Sales Invoice from a Sales Order, ensuring that the Sales Order is ready for billing.
    """
    sales_order = frappe.get_doc("Sales Order", sales_order_name)

    # ✅ Ensure the Sales Order is ready for billing
    if sales_order.status not in ["To Bill", "Completed"]:
        sales_order.db_set("status", "To Bill")  # ✅ Update Status
        sales_order.save()


    sales_invoice = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": sales_order.customer,
        "items": [
            {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate
            } for item in sales_order.items
        ],
        "due_date": frappe.utils.today()
    })
    sales_invoice.insert()
    sales_invoice.submit()
    frappe.db.commit()
    
    print(f"✅ Sales Invoice Created: {sales_invoice.name}")
    return sales_invoice.name

