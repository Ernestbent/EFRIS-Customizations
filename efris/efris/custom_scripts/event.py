from io import BytesIO
import json
import os
import tempfile
import frappe
from frappe.model.document import Document
from frappe.utils.data import image_to_base64
import requests
import random
import base64
from datetime import datetime, timedelta
import json
import frappe
from frappe.model.document import Document
import requests
import uuid
from datetime import datetime, timezone, timedelta

# Example events.py
import random


# Specify the East Africa Time (EAT) timezone
eat_timezone = timezone(timedelta(hours=3))  # UTC+3

# Get the current time in the EAT timezone
current_time = datetime.now(eat_timezone).strftime("%Y-%m-%d %H:%M:%S")
print("Current time in Uganda (EAT):", current_time)


def generate_unique_reference_number():
    return str(uuid.uuid4().int)[:10]  # Extract the first 10 digits of the UUID


unique_reference_number = generate_unique_reference_number()


def generate_random_8_digits():
    return random.randint(10000000, 99999999)


# Example usage
random_8_digits = generate_random_8_digits()

# Hooking into the on-submit controller
def on_send(doc, event):
    if not doc.custom_efris_invoice:
        
        return
    # Example values from variables
    date_str = doc.posting_date  # Assuming doc.posting_date holds the date string
    time_str = doc.posting_time  # Assuming doc.posting_time holds the time string

    # Concatenate the date and time strings to form one string
    datetime_combined = date_str + " " + time_str

    def generate_unique_reference_number():
        return str(uuid.uuid4().int)[:10]  # Extract the first 10 digits of the UUID

    unique_reference_number = generate_unique_reference_number()

    def generate_random_8_digits():
        return random.randint(10000000, 99999999)

    # Example usage
    random_8_digits = generate_random_8_digits()

    items_data = []
    goods_details = []
    # Initialize goods_details list outside
    tax_categories = {}
    # Track the number of items created
    item_count = 0

    # Iterate through each item in the 'items' child table
    for item in doc.items:
        item_count += 1

        # Collect item details in a dictionary
        item_data = {
            "item_name": item.item_name,
            "item_code": item.item_code,
            # 'custom_goods_category': item.custom_goods_category,
            "qty": item.qty,
            "rate": item.rate,
            "uom": item.uom,
            "amount": item.amount,
            "description": item.description,
            "goods_category_id":item.custom_goods_category_id,
            "item_tax_template": item.item_tax_template,
        }
        # Append the item_data dictionary to the items_data list
        items_data.append(item_data)

        if item.item_tax_template == "Exempt - MCL":
            tax_rate = "-"
            tax_category_code = "03"
            tax = 0
            grossAmount = item.amount
            taxAmount = 0
            netAmount = item.amount
        elif item.item_tax_template == "Tax Zero(0%) - MCL":
            tax_rate = 0
            tax_category_code = "02"
            tax = 0
            grossAmount = item.amount
            taxAmount = 0
            netAmount = item.amount

        else:
            tax_category_code = "01"
            tax_rate = "0.18"
            tax = round((18 / 118) * item.qty * item.rate, 2)
            grossAmount = item.amount
            taxAmount = round(((18 / 118) * item.amount), 2)
            netAmount = grossAmount - tax

        # Check if tax template already exists in tax_categories dictionary
        if item.item_tax_template in tax_categories:
            # Update values for existing tax template
            tax_categories[item.item_tax_template]["grossAmount"] += item.amount
            tax_categories[item.item_tax_template]["taxAmount"] += taxAmount
            tax_categories[item.item_tax_template]["netAmount"] += netAmount
            # Create goods_detail dictionary
        else:
            # Create new entry for tax template
            tax_categories[item.item_tax_template] = {
                "taxCategoryCode": tax_category_code,
                "netAmount": netAmount,
                "taxRate": tax_rate,
                "taxAmount": taxAmount,
                "grossAmount": item.amount,
                "exciseUnit": "",
                "exciseCurrency": "",
                "taxRateName": "",
            }
            # Round off the netAmount after completing all calculations
        for category in tax_categories.values():
            category["netAmount"] = round(category["netAmount"], 2)
            category["taxAmount"] = round(category["taxAmount"], 2)

            # Convert tax_categories dictionary to a list
        tax_categories_list = list(tax_categories.values())
        print(f"Rate: {item.item_tax_template}")

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

        goods_detail = {
            "item": item.item_name,
            "itemCode": item.item_code,
            "qty": item.qty,
            "unitOfMeasure": str(doc_status_mapping),
            "unitPrice": item.rate,
            "total": item.amount,
            "taxRate": tax_rate,
            "tax": tax,
            "discountTotal": "",
            "discountTaxRate": "",
            "orderNumber": str(
                len(goods_details)
            ),  # Use the length of goods_details as the orderNumber
            "discountFlag": "2",
            "deemedFlag": "2",
            "exciseFlag": "2",
            "categoryId": "",
            "categoryName": "",
            "goodsCategoryId": item.custom_goods_category_id,
            "goodsCategoryName": "",
            "exciseRate": "",
            "exciseRule": "",
            "exciseTax": "",
            "pack": "",
            "stick": "",
            "exciseUnit": "",
            "exciseCurrency": "",
            "exciseRateName": "",
            "vatApplicableFlag": "1",
        }

        goods_details.append(goods_detail)

        total_tax_amount = sum(
            tax_category["taxAmount"] for tax_category in tax_categories_list
        )

        print("\n\n\n\n")
        linked_doc = frappe.get_doc("Sales Taxes and Charges Template", doc.taxes)
        for taxes in linked_doc.taxes:
            taxes = {
                # 'rate': taxes.rate,
                "tax_amount": taxes.tax_amount,
                # Add other fields from the 'taxes' table as needed
            }
        # Print the values to the terminal
        # print(f"Item Name: {item.item_name}")
        # print(f"Item Code: {item.item_code}")
        # print(f"Goods category Id: {item.custom_goods_category}")
        # print(f"Qty: {item.qty}")
        # print(f"rate: {item.rate}")
        # print(f"uom: {item.uom}")

        # Add other print statements for additional fields if needed
        print("\n")  # Add a line break for better readabilit

    # Your logic for on_submit event
    # Generate invoices, interact with ERPNext API, etc.

    # Now 'items_data' contains a list of dictionaries, each representing an item with details from the 'items' child table.
    # You can use this data as needed for further processing or for constructing your JSON payload.

    # Assign item_name and item_code values to your JSON data
    # Get the current time and format it as a string

    json_data = [
        {
            "sellerDetails": {
                "tin": doc.company_tax_id,
                "ninBrn": "",
                "legalName": doc.custom_legal_name,
                "businessName": doc.custom_legal_name,
                "address": "Plot 473 Ntinda Kigowa Rd, Kampala",
                "mobilePhone": "256782466840",
                "linePhone": "256782466240",
                "emailAddress": "consulting@tgs-osillo.com",
                "placeOfBusiness": "NTINDA",
                "referenceNo": unique_reference_number,
                "branchId": "",
                "isCheckReferenceNo": "",
            },
            "basicInformation": {
                "invoiceNo": "",
                "antifakeCode": "",
                "deviceNo": doc.custom_device_number,
                "issuedDate": datetime_combined,
                "operator": doc.custom_legal_name,
                "currency": "UGX",
                "oriInvoiceId": "1",
                "invoiceType": "1",
                "invoiceKind": "1",
                "dataSource": "106",
                "invoiceIndustryCode": "",
                "isBatch": "0",
            },
            "buyerDetails": {
                "buyerTin": doc.tax_id,
                "buyerNinBrn": "",
                "buyerPassportNum": "",
                "buyerLegalName": doc.customer,
                "buyerBusinessName": doc.customer,
                "buyerAddress": "",
                "buyerEmail": doc.custom_email_id,
                "buyerMobilePhone": "",
                "buyerLinePhone": "",
                "buyerPlaceOfBusi": "",
                "buyerType": "1",
                "buyerCitizenship": "",
                "buyerSector": "1",
                "buyerReferenceNo": "",
            },
            "buyerExtend": {
                "propertyType": "abc",
                "district": "",
                "municipalityCounty": "",
                "divisionSubcounty": "",
                "town": "",
                "cellVillage": "",
                "effectiveRegistrationDate": "",
                "meterStatus": "",
            },
            "goodsDetails": goods_details,
            "taxDetails": tax_categories_list,
            "summary": {
                "netAmount": round((doc.total - total_tax_amount), 2),
                "taxAmount": round((total_tax_amount), 2),
                "grossAmount": doc.total,
                "itemCount": item_count,
                "modeCode": "0",
                "remarks": "We appreciate your continued support",
                "qrCode": "",
            },
            "payWay": {
                "paymentMode": "102",
                "paymentAmount": doc.total,
                "orderNumber": "a",
            },
            "extend": {"reason": "reason", "reasonCode": "102"},
            "importServicesSeller": {
                "importBusinessName": "",
                "importEmailAddress": "",
                "importContactNumber": "",
                "importAddress": "",
                "importInvoiceDate": "",
                "importAttachmentName": "",
                "importAttachmentContent": "",
            },
            "airlineGoodsDetails": [
                {
                    "item": "",
                    "itemCode": "",
                    "qty": "",
                    "unitOfMeasure": "",
                    "unitPrice": "",
                    "total": "",
                    "taxRate": "",
                    "tax": "",
                    "discountTotal": "",
                    "discountTaxRate": "",
                    "orderNumber": "",
                    "discountFlag": "",
                    "deemedFlag": "",
                    "exciseFlag": "",
                    "categoryId": "",
                    "categoryName": "",
                    "goodsCategoryId": "",
                    "goodsCategoryName": "",
                    "exciseRate": "",
                    "exciseRule": "",
                    "exciseTax": "",
                    "pack": "1",
                    "stick": "",
                    "exciseUnit": "",
                    "exciseCurrency": "",
                    "exciseRateName": "",
                }
            ],
            "edcDetails": {
                "tankNo": "",
                "pumpNo": "",
                "nozzleNo": "",
                "controllerNo": "",
                "acquisitionEquipmentNo": "",
                "levelGaugeNo": "",
                "mvrn": "",
            },
        }
    ]

    # Convert JSON object to JSON-formatted string
    json_string = json.dumps(json_data)

    # Encode the JSON string to Base64
    encoded_json = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")
    # print(encoded_json)

    if not doc.is_return:
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
                    "interfaceCode": "T109",
                    "requestCode": "TP",
                    "requestTime": datetime_combined,
                    "responseCode": "TA",
                    "userName": "admin",
                    "deviceMAC": "B47720524158",
                    "deviceNo": doc.custom_device_number,
                    "tin": doc.company_tax_id,
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
            #print Json Data
            print(f"Request Data: {json.dumps(data_to_post, indent=4)}")
            ###assign request in sales invoice
            doc.custom_post_request = {json.dumps(data_to_post, indent=4)}

            # Make a POST request to the external API.
            api_url = doc.custom_efris_offline_enabler_url
            headers = {"Content-Type": "application/json"}

            response = requests.post(api_url, json=data_to_post)
            ####response 
            
            response.raise_for_status()

            # Parse the JSON response content.
            response_data = json.loads(response.text)
            json_response= json.dumps(response_data, indent=4)

            ##########
            doc.custom_response = json_response

            return_message = response_data["returnStateInfo"]["returnMessage"]
            doc.custom_return_status = return_message
            # Handle the response status code
            if response.status_code == 200 and return_message == "SUCCESS":
                frappe.msgprint("Sales Invoice successfully submitted to EFIRS URA.")

                # Print the response status code and content.
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")

                # Parse the JSON response content.
                response_data = json.loads(response.text)
                return_message = response_data["returnStateInfo"]["returnMessage"]

                # Extract and decode the 'content' string.
                encoded_content = response_data["data"]["content"]
                decoded_content = base64.b64decode(encoded_content).decode("utf-8")
                # Print the decoded content
                print("Decoded Content:", decoded_content)

                data = json.loads(decoded_content)

                # Access the 'basicInformation' key using camelCase.
                doc.custom_device_number = data.get("basicInformation", {}).get("deviceNo")
                # doc.qrcode = data.get("summary", {}).get("qrCode").
                doc.custom_verification_code = data.get("basicInformation", {}).get(
                    "antifakeCode"
                )
                doc.custom_fiscal_document_number = data.get("basicInformation", {}).get("invoiceNo")
                doc.custom_qr_code = data.get("summary", {}).get("qrCode")
                doc.custom_invoice_number = data.get("basicInformation", {}).get("invoiceId")


                # Check if qr_data is not None and not an empty string.

                print("Device No:", doc.custom_device_number)
                print("QR Code:", doc.custom_qr_code)
                print("Verification Code:", doc.custom_verification_code)
                print("Fiscal Document Number:", doc.custom_fiscal_document_number)
                print("Invoice ID:", doc.custom_invoice_number)

                doc.save()

            else:
                frappe.throw(
                    title="EFRIS API Error",
                    msg=return_message,
                )
                doc.docstatus = 0
               

        except requests.exceptions.RequestException as e:
            frappe.msgprint(f"Error making API request: {e}")
            # Set the document status to 'Draft'
            doc.docstatus = 0  # 0 represents 'Draft' status
            doc.save()

    else:
        data = {
            "oriInvoiceId": doc.custom_invoice_number,
            "oriInvoiceNo": doc.custom_fiscal_document_number,
            "reasonCode": "102",
            "reason": "Refund",
            "applicationTime": datetime_combined,
            "invoiceApplyCategoryCode": "101",
            "currency": "UGX",
            "contactName": "",
            "contactMobileNum": "",
            "contactEmail": "",
            "source": "106",
            "remarks": "Remarks",
            "sellersReferenceNo": "",
            "goodsDetails": goods_details,
            "taxDetails": tax_categories_list,
            "summary": {
                "netAmount": round((doc.total - total_tax_amount), 2),
                "taxAmount": round((total_tax_amount), 2),
                "grossAmount": doc.total,
                "itemCount": item_count,
                "modeCode": "0",
                "remarks": "We appreciate your continued support",
                "qrCode": doc.custom_qr_code,
            },
            "payWay": {
                "paymentMode": "102",
                "paymentAmount": doc.total,
                "orderNumber": "a",
            },
            "buyerDetails": {
                "buyerTin": doc.tax_id,
                "buyerNinBrn": "",
                "buyerPassportNum": "",
                "buyerLegalName": doc.customer,
                "buyerBusinessName": doc.customer,
                "buyerAddress": "",
                "buyerEmail": doc.custom_email_id,
                "buyerMobilePhone": "",
                "buyerLinePhone": "",
                "buyerPlaceOfBusi": "",
                "buyerType": "1",
                "buyerCitizenship": "",
                "buyerSector": "1",
                "buyerReferenceNo": "",
            },
            "importServicesSeller": {
                "importBusinessName": "",
                "importEmailAddress": "",
                "importContactNumber": "",
                "importAddress": "",
                "importInvoiceDate": "",
                "importAttachmentName": "",
                "importAttachmentContent": "",
            },
            "basicInformation": {
                "operator": "TGS-OSILLO CONSULTING",
                "invoiceKind": "1",
                "invoiceIndustryCode": "",
                "branchId": "",
            },
        }
        # Convert JSON object to JSON-formatted string
        json_string2 = json.dumps(data)

        # Encode the JSON string to Base64
        encoded_json2 = base64.b64encode(json_string2.encode("utf-8")).decode("utf-8")
        try:
            data_to_post2 = {
                "data": {
                    "content": encoded_json2,
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
                    "interfaceCode": "T110",
                    "requestCode": "TP",
                    "requestTime": datetime_combined,
                    "responseCode": "TA",
                    "userName": "admin",
                    "deviceMAC": "B47720524158",
                    "deviceNo": doc.custom_device_number,
                    "tin": doc.company_tax_id,
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
            print(f"Request data: {json.dumps(data_to_post2, indent=4)}")
            # Make a POST request to the external API.
            api_url = doc.custom_efris_offline_enabler_url  # Replace with your actual endpoint
            headers = {"Content-Type": "application/json"}

            response = requests.post(api_url, json=data_to_post2)
            response.raise_for_status()  # Raise an HTTPError for bad responses.
            
            # Print the response status code and content.
            print(f"Response Status Code: {response.status_code}")
            print(f"Response Content: {response.text}")
            
              # Parse the JSON response content.
            response_data2 = json.loads(response.text)
            return_message2 = response_data2["returnStateInfo"]["returnMessage"]

            # Handle the response status code
            if response.status_code == 200 and return_message2 == "SUCCESS":

                frappe.msgprint("Credit Note Submitted Successfully")
                
            else:
                frappe.throw(
                title='EFRIS API Error',
                msg=f"{return_message2}"
            )
                doc.docstatus = 0

        except requests.exceptions.RequestException as e:
            frappe.msgprint(f"Error making API request: {e}")
            
            # Set the document status to 'Draft'
            doc.docstatus = 0  # 0 represents 'Draft' status
            doc.save()
