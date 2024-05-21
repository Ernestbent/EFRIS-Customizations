import base64
from datetime import datetime
from erpnext.stock.doctype import item
import frappe
import requests
from frappe.model.document import Document
from frappe.utils.data import image_to_base64
import json


from datetime import datetime, timezone, timedelta

# Specify the East Africa Time (EAT) timezone
eat_timezone = timezone(timedelta(hours=3))  # UTC+3

# Get the current time in the EAT timezone
current_time = datetime.now(eat_timezone).strftime("%Y-%m-%d %H:%M:%S")


def on_stock(doc, event):
    ##check if checkbox is checked
    if not doc.custom_efris_pi:
        return
    date_str = doc.posting_date  # Assuming doc.posting_date holds the date string
    time_str = doc.posting_time  # Assuming doc.posting_time holds the time string

    # Concatenate the date and time strings to form one string
    datetime_combined = date_str + " " + time_str
    items_data = []
    for item in doc.items:
        item_data = {
            "item_name": item.item_name,
            "item_code": item.item_code,
            # 'custom_goods_category': item.custom_goods_category,
            "qty": item.qty,
            "rate": item.rate,
            "uom": item.uom,
            "amount": item.amount,
            "description": item.description,
            "item_tax_template": item.item_tax_template,
        }
        # Append the item_data dictionary to the items_data list
        items_data.append(item_data)

        # Define the mapping of stock_uom to numeric values
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

        # Assume the value of doc.stock_uom will be selected by the user or retrieved from the system
        doc_stock_uom = item.uom  # Replace "Box" with doc.stock_uom

        # Define doc_status_mapping variable
        doc_status_mapping = uom_mapping.get(
            doc_stock_uom,
        )

        goods_stock_in = {
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
        # adjustment_type_mapping = {
        #     "Expired Goods": "101",
        #     "Damaged Goods": "102",
        #     "Personal Uses": "103",
        #     "Raw Materials": "105",
        #     # "Others (Please Specify)":"104"
        # }
        # # Assuming you have a field called 'adjustment_reason' in your document
        # adjust_reason = doc.adjustment_type
        # adjustTypes = adjustment_type_mapping.get(
        #     adjust_reason, ""
        # )  # Get corresponding adjustment type based on the reason
        # # frappe.msgprint(f"EFRIS Stock decreased ")
        # if doc.stock_in_type == "Increase Inventory":
        #     operation_type = "101"
        #     stock_in_type = "102"
        #     supplierName = doc.supplier_name
        #     supplierTin = doc.tax_id
        #     adjustType = ""
        #     remarks = "Increase Inventory"
        #     # frappe.msgprint(f"EFRIS Stock Increased ")
        # else:
        #     operation_type = "102"
        #     stock_in_type = ""
        #     supplierName = ""
        #     supplierTin = ""
        #     adjustType = adjustTypes
        #     remarks = "Inventory Reduction"

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
            "goodsStockInItem": [goods_stock_in],
        }

        # Serialize the data to a JSON formatted string
        json_string = json.dumps(data)
        # Encode the JSON string to Base64
        encoded_json = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

        # Define the mapping of stock_uom to numeric values
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
            ##print Json data to post
            print(f"Request Data: {json.dumps(data_to_post, indent=4)}")
            ###Fetching Post request message from backend
            doc.custom_post_request = json.dumps(data_to_post, indent=4)

            # Make a POST request to the external API
            api_url = doc.custom_efris_offline_enabler  # Replace with your actual endpoint
            response = requests.post(api_url, json=data_to_post)
            response.raise_for_status()  # Raise an HTTPError for bad responses.

            # Parse the JSON response content.
            response_data = json.loads(response.text)

            # Print the response status code and content.
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Content: {response.text}")

            # Parse the JSON response content.
            response_data = json.loads(response.text)
            json_response= json.dumps(response_data)

            #Fetching the return status from the backend
            doc.custom_response_ = json_response
            
            # Access the value of "returnMessage"
            return_message = response_data["returnStateInfo"]["returnMessage"]
            doc.custom_return_status = return_message
            # Handle the response status code
            if response.status_code == 200 and return_message == "SUCCESS":
                # frappe.msgprint(f"{remarks}" )
                frappe.msgprint("Thanks, your stocks have been successfully recorded in EFIRS.")

            # Print the error on screen
            elif return_message == "Partial failure!":
                # Extract and decode the 'content' string.
                encoded_content = response_data["data"]["content"]
                decoded_content = base64.b64decode(encoded_content).decode("utf-8")
                # Print the decoded content

                data = json.loads(decoded_content)
                erroMessage = data[0]["returnMessage"]
                frappe.throw(title="", msg=erroMessage)

            else:
                frappe.throw(title="EFRIS API Error", msg=f"{return_message}")

                doc.docstatus = 0
                # Save the document
                doc.save()
        except requests.exceptions.RequestException as e:
            frappe.msgprint(f"Error making API request: {e}")
            # Set the document status to 'Draft'
            doc.docstatus = 0  # 0 represents 'Draft' status
            doc.save()
