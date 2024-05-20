import frappe

def on_submit(doc, event):
    frappe.msgprint("Hello There")