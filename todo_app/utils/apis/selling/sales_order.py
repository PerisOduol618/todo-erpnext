import frappe
from frappe.utils import add_days, today



def create_quotation(customer, items):
    print("Creating Quotation...") 
    
    try:
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",  
            "party_name": customer,
            "items": [
                {
                    "item_code": item["item_code"],
                    "qty": item["qty"],
                    "rate": item.get("rate", 0)  
                } for item in items
            ]
        })
        
        print(f"Quotation Draft Created: {quotation.as_dict()}")  
        
        quotation.insert()
        
        quotation.submit()  #  Submit immediately to trigger hooks
        print(f"Quotation Submitted: {quotation.name}") 
        
        frappe.db.commit()

        return quotation.name

    except Exception as e:
        print(f"❌ Error: {e}") 
        frappe.log_error(f"Error Creating Quotation: {str(e)}")
        return None
 

def convert_quotation_to_sales_order(doc, event=None): 
    """
    Converts a submitted Quotation into a Sales Order
    """
    frappe.logger().info(f"🚀 Hook Triggered for Quotation: {doc.name}")  
    frappe.msgprint(f"Hook Triggered for Quotation: {doc.name}")  

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

    frappe.logger().info(f"Sales Order Created: {sales_order.name}")
    frappe.msgprint(f"Sales Order Created: {sales_order.name}")


def create_sales_invoice(sales_order_name, event=None):
    """
    Creates a Sales Invoice from a Sales Order, ensuring that the Sales Order is ready for billing.
    """

     # Step 1: Fetch the Sales Order
    sales_order = frappe.get_doc("Sales Order", sales_order_name)

    # Ensure the Sales Order is ready for billing
    if sales_order.status not in ["To Bill", "Completed"]:
        sales_order.db_set("status", "To Bill")  
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
    
    print(f"Sales Invoice Created: {sales_invoice.name}")
    return sales_invoice.name


def create_delivery_note(sales_order_name,event=None):
    """
    Creates a Delivery Note from a Sales Order.

   
    """
    # Step 1: Fetch the Sales Order
    sales_order = frappe.get_doc("Sales Order", sales_order_name)

    # Step 2: Create the Delivery Note with Sales Order details
    delivery_note = frappe.get_doc({
        "doctype": "Delivery Note",
        "customer": sales_order.customer,
        "posting_date": today(),
        "items": [
            {
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": item.rate
            } for item in sales_order.items
        ]
    })

    # Step 3: Insert and submit the Delivery Note
    delivery_note.insert()
    delivery_note.submit()
    frappe.db.commit()
    
    print(f"Delivery Note Created: {delivery_note.name}")
    return delivery_note.name

    
def record_payment_entry(doc, event=None):
    """
    Automatically creates a Payment Entry when a Sales Invoice is submitted.
    """
    try:
        print(f"Auto Payment Entry Triggered for Invoice: {doc.name}")

        company = frappe.get_value("Sales Invoice", doc.name, "company")  # Get the company
        paid_from = frappe.get_value("Account", {"account_type": "Receivable", "company": company}, "name") or "Debtors - T"
        paid_to = frappe.get_value("Account", {"account_type": "Cash", "company": company}, "name") or "Cash - T"

        payment_entry = frappe.get_doc({
            "doctype": "Payment Entry",
            "payment_type": "Receive",
            "party_type": "Customer",
            "party": doc.customer,
            "paid_amount": doc.outstanding_amount,  
            "received_amount": doc.outstanding_amount,
            "reference_no": doc.name,
            "reference_date": today(),
            "mode_of_payment": "Cash",  
            "paid_from": paid_from,  
            "paid_to": paid_to 
        })

        payment_entry.insert()
        payment_entry.submit()
        frappe.db.commit()

        print(f"✅ Auto Payment Entry Created: {payment_entry.name}")
    
    except Exception as e:
        frappe.log_error(f"❌ Error in Auto Payment Entry: {str(e)}")
        print(f"❌ Error: {e}")
