import base64
from datetime import datetime, timezone, timedelta
import frappe
import requests
import json

# Specify the East Africa Time (EAT) timezone
eat_timezone = timezone(timedelta(hours=3))  # UTC+3

def on_save(doc, method):
    # Check if the checkbox is checked
    if not doc.custom_efris_item:
        # If the checkbox is not checked, skip the rest of the function
        return

    # If the checkbox is checked, execute the code
    current_time = datetime.now(eat_timezone).strftime("%Y-%m-%d %H:%M:%S")
    print("Current time in Uganda (EAT):", current_time)

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
    doc_stock_uom = doc.stock_uom
    # Define doc_status_mapping variable
    doc_status_mapping = uom_mapping.get(doc_stock_uom)

    data = [
        {
            "operationType": "101",
            "goodsName": doc.item_name,
            "goodsCode": doc.item_code,
            "measureUnit": str(doc_status_mapping),
            "unitPrice": doc.standard_rate,
            "currency": "101",
            "commodityCategoryId": doc.custom_goods_category_id,
            "haveExciseTax": "102",
            "description": doc.description,
            "stockPrewarning": "10",
            "pieceMeasureUnit": "",
            "havePieceUnit": "102",
            "pieceUnitPrice": "",
            "packageScaledValue": "",
            "pieceScaledValue": "",
            "exciseDutyCode": "",
            "haveOtherUnit": "",
            "goodsTypeCode": "101",
            "goodsOtherUnits": [],
        }
    ]

    # Serialize the data to a JSON formatted string
    json_string = json.dumps(data)

    # Encode the JSON string to Base64
    encoded_json = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    try:
        data_to_post = {
            "data": {
                "content": encoded_json,
                "signature": "",
                "dataDescription": {"codeType": "0", "encryptCode": "1", "zipCode": "0"},
            },
            "globalInfo": {
                "appId": "AP04",
                "version": "1.1.20191201",
                "dataExchangeId": "9230489223014123",
                "interfaceCode": "T130",
                "requestCode": "TP",
                "requestTime": current_time,
                "responseCode": "TA",
                "userName": "admin",
                "deviceMAC": "B47720524158",
                "deviceNo": doc.custom_device_number,
                "tin": doc.custom_company_tin,
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
        ###print json data to post
        print(f"Request Data: {json.dumps(data_to_post, indent=4)}")

        doc.custom_post_requestefris = data_to_post

        # Make a POST request to the external API
        api_url = doc.custom_offline_enabler  # Replace with your actual endpoint
        response = requests.post(api_url, json=data_to_post)

        
        response.raise_for_status()  # Raise an HTTPError for bad responses.

        # Parse the JSON response content.
        response_data = json.loads(response.text)
        

        # Print the response status code and content.
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")

        response_data = json.loads(response.text)
        doc.custom_ura_responseefris = response_data
        # Access the value of "returnMessage"
        return_message = response_data["returnStateInfo"]["returnMessage"]

        doc.custom_return_status = return_message
        if response.status_code == 200 and return_message == "SUCCESS":

            frappe.msgprint("Item successfully added to EFIRS URA.")
        else:
            frappe.throw(
                title="API Error",
                msg=return_message
            )
            doc.docstatus = 0  # Set the document status to 'Draft'
               
    except requests.exceptions.RequestException as e:
        frappe.msgprint(f"Error making API request: {e}")
        # Set the document status to 'Draft'
        doc.docstatus = 0  # 0 represents 'Draft' status
