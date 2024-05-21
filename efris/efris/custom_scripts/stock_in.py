import base64
from datetime import datetime, timezone, timedelta
import frappe
import requests
import json

# Specify the East Africa Time (EAT) timezone
eat_timezone = timezone(timedelta(hours=3))  # UTC+3

def on_stock(doc, event):
    # Check if checkbox is checked
    if not doc.custom_efris_pi:
        return

    date_str = doc.posting_date  # Assuming doc.posting_date holds the date string
    time_str = doc.posting_time  # Assuming doc.posting_time holds the time string

    # Concatenate the date and time strings to form one string
    datetime_combined = date_str + " " + time_str

    items_data = []
    goods_stock_in_items = []

    uom_mapping = {
        "Box": 110,
        "Pair": 111,
        "Yard": 112,
        "stick": 101,
        "Kg": 103,
        "Minute": 105,
        "Litre": 102,
        "User per day access": 104,
        "Cost": 208,
        "-": 108,
        "Per week": 114,
        "Per annum": 116,
        "Per month": 115,
        "PP-Piece": 117,
        "Hours": 207,
        "Tot": 211,
        "Percentage": 210,
        "Billing": 213,
        "Per shift": 216,
    }

    for item in doc.items:
        item_data = {
            "item_name": item.item_name,
            "item_code": item.item_code,
            "qty": item.qty,
            "rate": item.rate,
            "uom": item.uom,
            "amount": item.amount,
            "description": item.description,
            "item_tax_template": item.item_tax_template,
        }
        items_data.append(item_data)

        doc_stock_uom = item.uom  # Replace "Box" with doc.stock_uom
        doc_status_mapping = uom_mapping.get(doc_stock_uom)

        goods_stock_in_item = {
            "commodityGoodsId": "",
            "goodsCode": item.item_code,
            "measureUnit": str(doc_status_mapping),
            "quantity": item.qty,
            "unitPrice": item.rate,
            "remarks": "",
            "fuelTankId": "",
            "lossQuantity": "",
            "originalQuantity": "",
        }
        goods_stock_in_items.append(goods_stock_in_item)

    data = {
        "goodsStockIn": {
            "operationType": "101",
            "supplierTin": doc.supplier_name,
            "supplierName": doc.tax_id,
            "adjustType": "",
            "remarks": "Increase Inventory",
            "stockInDate": doc.posting_date,
            "stockInType": "101",
            "productionBatchNo": "",
            "productionDate": "",
            "branchId": "",
            "invoiceNo": "",
            "isCheckBatchNo": "0",
            "rollBackIfError": "0",
            "goodsTypeCode": "101",
        },
        "goodsStockInItem": goods_stock_in_items,
    }

    json_string = json.dumps(data)
    encoded_json = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    try:
        data_to_post = {
            "data": {
                "content": encoded_json,
                "signature": "",
                "dataDescription": {
                    "codeType": "0",
                    "encryptCode": "1",
                    "zipCode": "0",
                },
            },
            "globalInfo": {
                "appId": "AP04",
                "version": "1.1.20191201",
                "dataExchangeId": "9230489223014123",
                "interfaceCode": "T131",
                "requestCode": "TP",
                "requestTime": datetime_combined,
                "responseCode": "TA",
                "userName": "admin",
                "deviceMAC": "B47720524158",
                "deviceNo": doc.custom_device_number,
                "tin": doc.custom_company_tax_id,
                "brn": "",
                "taxpayerID": "1",
                "longitude": "32.61665",
                "latitude": "0.36601",
                "agentType": "0",
                "extendField": {
                    "responseDateFormat": "dd/MM/yyyy",
                    "responseTimeFormat": "dd/MM/yyyy HH:mm:ss",
                    "referenceNo": "24PL01000221",
                    "operatorName": "administrator",
                },
            },
            "returnStateInfo": {"returnCode": "", "returnMessage": ""},
        }

        print(f"Request Data: {json.dumps(data_to_post, indent=4)}")
        doc.custom_post_request = json.dumps(data_to_post, indent=4)

        api_url = doc.custom_efris_offline_enabler  # Replace with your actual endpoint
        response = requests.post(api_url, json=data_to_post)
        response.raise_for_status()

        response_data = json.loads(response.text)
        json_response = json.dumps(response_data, indent=4)  # Convert the parsed JSON object to a JSON string
        doc.custom_response_ = json_response  # Save the JSON string in the document


        return_message = response_data["returnStateInfo"]["returnMessage"]
        doc.custom_return_status = return_message

        if response.status_code == 200 and return_message == "SUCCESS":
            frappe.msgprint("Thanks, your stock has been successfully recorded in EFIRS.")
        elif return_message == "Partial failure!":
            encoded_content = response_data["data"]["content"]
            decoded_content = base64.b64decode(encoded_content).decode("utf-8")
            data = json.loads(decoded_content)
            erroMessage = data[0]["returnMessage"]
            frappe.throw(title="", msg=erroMessage)
        else:
            frappe.throw(title="EFRIS API Error", msg=f"{return_message}")

            doc.docstatus = 0
            doc.save()
    except requests.exceptions.RequestException as e:
        frappe.msgprint(f"Error making API request: {e}")
        doc.docstatus = 0
        doc.save()
