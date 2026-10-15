
# Financial Institutions (FI) API Documentation

**Ultimate Pay Platform**

latest update  30-9-2026  

---

  

## Overview

  

The **Ultimate Pay Financial Institutions (FI) API** enables financial institutions to seamlessly integrate payment, inquiry, biller discovery, and transaction management services. All API requests are authenticated using RSA-SHA256 digital signatures to ensure end-to-end message integrity and non-repudiation.

  

### Base URL

```http

https://tahseeltest.ultimate-pay.net/webserve

```

  

---

  

## 1. Authentication & Security

  

### 1.1 Digital Signature Overview

The digital signature serves as a secure, stateless alternative to traditional username/password authentication. Every HTTP request sent to the platform must include custom security headers generated using an RSA-256 private key.

  

### 1.2 FI Onboarding Steps

1.  **Navigate to Platform Settings**: Log into the **Ultimate Pay Platform** and go to the **Users** screen.

2.  **Create FI User**:

- Create a new user with type **Financial Institution**.

- Assign appropriate permissions.

- Set the user role/type as **Terminal User**.

3.  **Key Exchange**:

- Generate an RSA key pair locally (minimum 2048-bit recommended).

- Upload the `public_key.pem` file or paste its content into the designated text box in the admin portal.

-  **Important Security Notice**: Store `private_key.pem` in a secure location (e.g., HSM, AWS Secrets Manager, Key Vault). *Never share or expose the private key.*

  

---

  

### 1.3 Signature Generation Specification

  

To sign a request, construct a canonical string formatted as follows:

  

```text

<HTTP_METHOD>\n<PATH>\n<TIMESTAMP>\n<NONCE>\n<SHA256_HASH_OF_BODY>

```

  

Where:

-  `<HTTP_METHOD>`: Uppercase HTTP method (`GET`, `POST`, `PUT`, `DELETE`).

-  `<PATH>`: Request endpoint path starting with `/` (e.g., `/api/v1/financial_corp/sub_sector`).

-  `<TIMESTAMP>`: Current Unix timestamp in seconds (string).

-  `<NONCE>`: Unique UUID v4 string for replay protection.

-  `<SHA256_HASH_OF_BODY>`: Lowercase hex digest of the SHA-256 hash of the raw JSON request body (for empty body, use `""`).

  

Sign the UTF-8 encoded canonical string using **RSA PKCS#1 v1.5 with SHA-256**, then Base64 encode the resulting signature.

  

---

  

### 1.4 Required Request Headers

  

Every request sent to the Ultimate Pay platform must include the following headers:

  

| Header Name | Description | Example |

| :--- | :--- | :--- |

| `X-Client-ID` | Unique identifier assigned to the user | `client_corp_17` |

| `X-Timestamp` | Unix timestamp (seconds) when request was sent | `1786981200` |

| `X-Nonce` | UUID v4 generated per request | `c9bf9e57-1685-4c89-bafb-ff5af830be8a` |

| `X-Signature` | Base64-encoded RSA-256 signature | `dGhpcyBpcyBhIHNpZ25hdHVyZQ...` |

| `Content-Type` | Payload content type | `application/json` |

  

> ⚠️ **Verification Note**: The exact raw request body sent in the payload must be used to generate the SHA-256 hash. Any mismatch (e.g., key reordering, spacing differences) will cause signature verification failure on the server.

  

---

  

### 1.5 Python Client SDK Implementation

  

Below is a complete, production-ready Python client class implementing RSA-256 request signing and request execution:

  

```python

import hashlib

import json

import time

import uuid

from base64 import b64encode

from typing import Optional

import requests

from cryptography.hazmat.primitives import hashes, serialization

from cryptography.hazmat.primitives.asymmetric import padding

  

class  RS256ApiClient:

def  __init__(self, base_url: str, client_id: str, private_key_pem: str):

self.base_url = base_url.rstrip("/")

self.client_id = client_id

self.private_key = serialization.load_pem_private_key(

private_key_pem.encode("utf-8"), password=None

)

  

def  _sha256(self, data: str) -> str:

return hashlib.sha256(data.encode("utf-8")).hexdigest()

  

def  _sign(self, canonical: str) -> str:

sig = self.private_key.sign(

canonical.encode("utf-8"),

padding.PKCS1v15(),

hashes.SHA256()

)

return b64encode(sig).decode("utf-8")

  

def  _headers(self, method: str, path: str, body: str,

timestamp: Optional[str] = None, nonce: Optional[str] = None) -> dict:

ts = timestamp or  str(int(time.time()))

n = nonce or  str(uuid.uuid4())

canonical = f"{method}\n{path}\n{ts}\n{n}\n{self._sha256(body)}"

  

return {

"X-Client-ID": self.client_id,

"X-Timestamp": ts,

"X-Nonce": n,

"X-Signature": self._sign(canonical),

"Content-Type": "application/json",

}

  

def  request(self, method: str, path: str, body: str = "",

timestamp: Optional[str] = None, nonce: Optional[str] = None) -> requests.Response:

headers = self._headers(method, path, body, timestamp, nonce)

url = f"{self.base_url}{path}"

return requests.request(method, url, data=body, headers=headers)

  

def  post(self, path: str, body: str = "{}", **kw) -> requests.Response:

return  self.request("POST", path, body, **kw)

  

def  get(self, path: str, **kw) -> requests.Response:

return  self.request("GET", path, "", **kw)

  

def  put(self, path: str, body: str = "{}", **kw) -> requests.Response:

return  self.request("PUT", path, body, **kw)

  

def  delete(self, path: str, **kw) -> requests.Response:

return  self.request("DELETE", path, "", **kw)

  

if  __name__ == "__main__":

with  open("private_key.pem", "r") as f:

pem_key = f.read()

  

client = RS256ApiClient(

base_url="https://tahseeltest.ultimate-pay.net/webserve",

client_id="client_corp_17",

private_key_pem=pem_key

)

  

response = client.get("/api/v1/financial_corp/get_parent_sectors")

print("Status Code:", response.status_code)

print("Response JSON:", response.json())

```

  

---

  

### 1.6 General Error Handling

  

All APIs follow a standardized approach for error handling by using the appropriate **HTTP Status Codes** to indicate the result of each request.

  

Standard HTTP Status Codes used according to the nature of the response. For example:

  

-  `200 OK` — The operation was successful.

-  `400 Bad Request` — The request is invalid or contains invalid data.

-  `401 Unauthorized` — Authentication is required or invalid.

-  `403 Forbidden` — The requester does not have sufficient permissions.

-  `404 Not Found` — The requested resource or data was not found.

-  `500 Internal Server Error` — An unexpected server-side error occurred.

  

In addition to the HTTP Status Code, the API response include a **clear and descriptive error message** that explains the actual reason for the failure.

  

The **Error Message available directly in the API Response** so that the financial corp can understand the error and determine the appropriate handling action without needing to contact another team or refer to an external document or table to understand the meaning of the error.

  

For example:

  

```json

{

"status": "error",

"msg": "Payment reference ID is required",

"error_code":1001

}

```

  

### Errors

  
  

| HTTP Status | Error Code | Error Message |

| --- | --- | --- |

| `400` | `1001` | `X_CLIENT_ID required in request header` |

| `400` | `1002` | `X_TIMESTAMP required in request header` |

| `400` | `1003` | `X_NONCE required in request header` |

| `400` | `1004` | `X_SIGNATURE required in request header` |

| `401` | `1005` | `user not exist in system pelae contact with system administrator` |

| `400` | `1006` | `Request timestamp expired or clock skew limit exceeded` |

| `400` | `1007` | `Invalid X-Timestamp header format` |

| `400` | `1008` | `Replay attack detected. Nonce has already been processed.` |

| `401` | `1009` | `Unknown or unauthorized Client ID` |

| `403` | `1010` | `Invalid signature. Request payload was tampered with or key mismatch.` |

| `401` | `1011` | `signature expired` |

| `401` | `1012` | `invalid signature` |

| `500` | `1013` | `Internal server error from middleware {}` |

| `400` | `1014` | `payer_name is required field` |

| `400` | `1015` | `payer_type is required field add 1 for individuals or 2 for entities` |

| `400` | `1016` | `payer_name must be string data type` |

| `400` | `1017` | `payer_type must be integer data type` |

| `400` | `1018` | `payer_type not foud please add 1 for individuals or 2 for entities` |

| `400` | `1019` | `invalid biller_id value` |

| `400` | `1020` | `invalid paid_amount` |

| `400` | `1021` | `biller_id is required field` |

| `400` | `1022` | `paid_amount is required field` |

| `404` | `1023` | `biller not found` |

| `404` | `1024` | `Financial Corp not found` |

| `400` | `1025` | `currency code is required` |

| `404` | `1026` | `currency not found` |

| `400` | `1027` | `currency not supported for this biller` |

| `400` | `1028` | `currency not supported for this financial corp` |

| `404` | `1029` | `service pay by ref or to account not found` |

| `404` | `1030` | `service for fee payment not found` |

| `404` | `1031` | `commission not found` |

| `400` | `1032` | `cannot process your request because biller not confirmed this service'` |

| `404` | `1033` | `prepaid_reference_id is required field` |

| `404` | `1034` | `prepaid_reference_id not exist in system` |

| `400` | `1035` | `pay by ref biller_id is a required field` |

| `400` | `1036` | `pay by ref service_id is a required field` |

| `400` | `1037` | `pay by ref financial_corp_id is a required field` |

| `400` | `1038` | `pay by ref paid_amount is a required field` |

| `400` | `1039` | `pay by ref currency_code is a required field` |

| `400` | `1040` | `pay by ref financial_corp_payment_id is a required field` |

| `404` | `1041` | `Bill not found` |

| `400` | `1042` | `Bill already paid` |

| `400` | `1043` | `invalid commission_payment_method` |

| `400` | `1044` | `invalid paid amount, remaining is {}` |

| `500` | `1045` | `Internal server error from pay by reference the error is {}` |

| `400` | `1046` | `pay fee biller_id is a required field` |

| `400` | `1047` | `pay fee service_id is a required field` |

| `400` | `1048` | `pay fee financial_corp_id is a required field` |

| `400` | `1049` | `pay fee paid_amount is a required field` |

| `400` | `1050` | `pay fee currency_code is a required field` |

| `400` | `1051` | `pay fee financial_corp_payment_id is a required field` |

| `400` | `1052` | `pay fee invalid due amount` |

| `500` | `1053` | `Internal server error from pay fee the error is {}` |

| `400` | `1054` | `pay to account biller_id is a required field` |

| `400` | `1055` | `pay to account service_id is a required field` |

| `400` | `1056` | `pay to account financial_corp_id is a required field` |

| `400` | `1057` | `pay to account paid_amount is a required field` |

| `400` | `1058` | `pay to account currency_code is a required field` |

| `400` | `1059` | `pay to account financial_corp_payment_id is a required field` |

| `400` | `1060` | `pay to account to_customer_no is a required field` |

| `404` | `1061` | `pay to account biller sector not found` |

| `400` | `1062` | `pay to account invalid due amount` |

| `500` | `1063` | `Internal server error from to_account payment the error is {}` |

| `400` | `1063` | `Payment reference id is required` |

| `400` | `1064` | `Payment reference id must be a string` |

| `400` | `1065` | `Refund cannot be processed the refund not assigned for bills or to_account its for fees` |

| `400` | `1066` | `Refund cannot be processed because the payment has already been collected` |

| `400` | `1067` | `Payment already refunded` |

| `400` | `1068` | `Cannot refund now. Refund allowed after {duration_settings} hours from payment time. Remaining: {remaining_hours} hours.` |

| `500` | `1069` | `Internal server error from refund pay fee not collected the error is {}` |

| `500` | `1070` | `Payment does not exist in system` |

| `400` | `1071` | `parent_sector_id not exist in request please add it and try again` |

| `404` | `1072` | `not found` |

| `500` | `1073` | `Internal server error sub sector {}` |

| `400` | `1074` | `sector_id or service_type[fees or account] not exist in request please add it and try again` |

| `400` | `1075` | `service_type must be fees or account` |

| `404` | `1076` | `not found biler` |

| `404` | `1077` | `service not exist in system please contact with system administator` |

| `500` | `1078` | `Internal server error biller_ist {}` |

| `404` | `1079` | `not found service` |

| `400` | `1080` | `biller_id must be 'int' data type` |

| `400` | `1081` | `biller_id not exist in request please add it and try again` |

| `500` | `1082` | `Internal server error {}` |

| `404` | `1083` | `not found bill` |

| `400` | `1084` | `prepaid_reference_id not exist in request please add it and try again` |

| `500` | `1085` | `Internal server error invoice amount {}` |

| `400` | `1086` | `to_customer_no is a required field` |

| `400` | `1087` | `amount is a required field` |

| `400` | `1088` | `biller_id is a required field` |

| `400` | `1089` | `currency_code is a required field` |

| `404` | `1090` | `Currency not found in system` |

| `400` | `1091` | `currency not assigned to this biller` |

| `404` | `1092` | `fin corp not found in system` |

| `404` | `1093` | `commission not found` |

| `404` | `1094` | `missing biller apis connections` |

| `404` | `1095` | `Cutomer not found` |

| `404` | `1096` | `Biller Not found` |

| `500` | `1097` | `Internal server error {}` |

| `400` | `1098` | `please provide payment_reference_id in request and try again` |

| `400` | `1099` | `payment_reference_id must be string data type` |

| `404` | `1100` | `not found payment_reference_id` |

| `500` | `1101` | `Internal server error from get payment by ref number {}` |

| `400` | `1102` | `please provide financial_corp_payment_id in request and try again` |

| `400` | `1103` | `financial_corp_payment_id must be string data type` |

| `404` | `1104` | `not found financial_corp_payment_id` |

| `500` | `1105` | `Internal server error from get payment by financial corp payment id {}` |

| `404` | `1106` | `not found payments` |

| `500` | `1107` | `Internal server error from get payment {}` |

| `400` | `1108` | `please provide start_with_id in request and try again` |

| `400` | `1109` | `start_with_id cannot be str please change start_with_id to int data type` |

| `404` | `1110` | `not found payments` |

| `500` | `1111` | `Internal server error {}` |

| `404` | `1112` | `not found parent sectors` |

| `500` | `1113` | `Internal server error parent sector` |

| `404` | `1114` | `not found bilers sectors` |

| `500` | `1115` | `Internal server error from biller sectors` |

| `400` | `1116` | `please provide prepaid_reference_id in request and try again` |

| `400` | `1117` | `prepaid_reference_id must be string data type` |

| `404` | `1118` | `not found prepaid_reference_id` |

| `500` | `1119` | `Internal server error from get payment by prepaid reference id {}` |

| `400` | `1120` | `paid_amount must be integer or float data type` |

| `400` | `1121` | `paid_amount must > 0` |




  
  

---

  

## 2. Payment & Refund Endpoints

  

#### Payments Status

| Payment Method | Status | Details |

| :--- | :--- | :--- |

| `Fee` | `Pending` | Payment created but not collected |

| `Fee` | `Collected` | Payment collected by biller |

| `Fee` | `Refund` | the payment has been refunded to the customer *|

| `To account` | `Paid` | Payment status paid |

| `Pay by Ref` | `Paid` | Payment status paid |



---

  

### 2.1 Pay by Ultimate Prepaid Reference Id

Executes payment for an existing invoice using an Ultimate Pay reference ID. 

Notes:
1. Multible parial payment to the same prepaid reference id is allowed.
2. Neither the payment amount should be greater than the invoice amount nor the total of all parial payments.

  

-  **Endpoint**: `POST /api/v1/pay_by_ref_id`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |
| `prepaid_reference_id` | `STR` | Exact (14) | **Must** | Ultimate Pay invoice reference ID |

| `paid_amount` | `DOUBLE` | 15 | **Must** | Total amount collected from customer |

| `financial_corp_payment_id` | `STR` | - | **Must** | Financial institution payment reference |

| `currency_code` | `STR` | Exact (3) | **Must** | ISO currency code |

| `notes` | `STR` | 50 | Optional | Additional transaction remarks |

| `payer_name` | `STR` | 50 | **Must** | Full name of the payer |

| `payer_type` | `INT` | 1 | **Must** | Type of payer (`1` for individuals, `2` for entities) |

  

#### Code Example

```python

payload = json.dumps({

"paid_amount": 550,

"prepaid_reference_id": "26000140973360",

"financial_corp_payment_id": "6952125223621452",

"currency_code": "YER",

"notes": "test",

"payer_name": "test",

"payer_type": 2

})

response = client.post("/api/v1/pay_by_ref_id", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "success payment",

"data": [

{

"id": 125,

"payment_reference_id": "59821123678677183188",

"service_type": "bills",

"financial_corp_commission_amount": 5.5,

"created_at": "2026-08-17T15:42:34.780528Z"

}

]

}
```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `payment_reference_id` | `INT` | Max (10) | **Must** | The payment transaction reference |

| `service_type` | `ENUM(STR)` | - | **Must** | Service code |

| `financial_corp_commission_amount` | `DOUBLE` | Max (10) | **Must** | Financial corp commission amount |

| `created_at` | `STR` | - | - | Timestamp of payment creation |

  **Please note:**
  Payment_reference_id parameter that returned in the response body is NOT the same as prepaid_reference_id parameter that in request body. 
*prepaid_reference_id:* is an identifier that represents the biller invoice, it generated automatically when biller upload his/her invoice(s) to Ultimate Pay platform, which of course before the customer made any payment transactions.
  *payment_reference_id:* is an identifier the represents a single payment transaction that the customer has made.

---

  

### 2.2 Pay Pre-defined Fee Service

Executes payment for a standard pre-defined service fee.

  

-  **Endpoint**: `POST /api/v1/pay_fee`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `biller_id` | `INT` | Max (10) | **Must** | Biller code |

| `service_id` | `INT` | (10) | **Must** | Service code |

| `paid_amount` | `DOUBLE` | 15 | **Must** | Amount paid by customer |

| `financial_corp_payment_id` | `INT` | - | **Must** | Bank payment reference |

| `currency_code` | `STR` | 3 | **Must** | Currency code |

| `notes` | `STR` | 40 | Optional | Transaction remarks |

| `payer_name` | `STR` | 50 | **Must** | Name of payer |

| `payer_type` | `INT` | 1 | **Must** | Type of payer (`1` for individuals, `2` for entities) |

  

#### Code Example

```python

payload = json.dumps({

"biller_id": 1,

"service_id": 1,

"paid_amount": 550,

"financial_corp_payment_id": "6952125223621452",

"currency_code": "YER",

"notes": "test",

"payer_name": "test",

"payer_type": 2

})

response = client.post("/api/v1/pay_fee", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "success payment",

"data": [

{

"id": 127,

"payment_reference_id": "68997631480018377074",

"service_type": "fees",

"financial_corp_commission_amount": 3.5,

"created_at": "2026-08-17T15:57:54.347369Z"

}

]

}

```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `payment_reference_id` | `INT` | Max (10) | **Must** | Transaction reference |

| `service_type` | `ENUM(STR)` | - | **Must** | Service code |

| `financial_corp_commission_amount` | `DOUBLE` | Max (10) | **Must** | Commission amount |

| `created_at` | `STR` | - | - | Transaction timestamp |

  

---

  

### 2.3 Pay to Customer Account

Executes payment directly to a customer account with a commercial entity or bank biller.

  

-  **Endpoint**: `POST /api/v1/pay_to_customer`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `biller_id` | `INT` | Max (10) | **Must** | Biller code |

| `paid_amount` | `DOUBLE` | 15 | **Must** | Amount paid by customer |

| `to_customer_no` | `INT` | 20 | **Must** | Customer number with the biller |

| `financial_corp_payment_id` | `STR` | - | **Must** | Bank payment reference |

| `currency_code` | `STR` | Exact 3 | **Must** | Currency code |

| `to_customer_name` | `STR` | 50 | **Must** | Customer name |

| `payer_name` | `STR` | 50 | **Must** | Name of payer |

| `payer_type` | `INT` | 1 | **Must** | Type of payer (`1` for individuals, `2` for entities) |

  

#### Code Example

```python

payload = json.dumps({

"biller_id": 1,

"paid_amount": 550,

"to_customer_no": "21973",

"financial_corp_payment_id": "6952125223621452",

"currency_code": "YER",

"to_customer_name": "Wisam Saif",

"payer_name": "Sameer Mustafa",

"payer_type": 2

})

response = client.post("/api/v1/pay_to_customer", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "success payment",

"data": [

{

"id": 128,

"payment_reference_id": "79745728271967805491",

"service_type": "account",

"financial_corp_commission_amount": 5.5,

"created_at": "2026-08-17T16:01:12.554402Z"

}

]

}

```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `payment_reference_id` | `INT` | - | **Must** | Transaction reference |

| `service_type` | `ENUM(STR)` | - | **Must** | Service code |

| `financial_corp_commission_amount` | `DOUBLE` | Max (10) | **Must** | Commission amount |

| `created_at` | `STR` | - | - | Creation timestamp |

  

---

  



### 2.4 Refund of a Payment Transaction

Processes a refund transaction of a pending payment status of a pre-defined fee payment transaction. 

**Please note:** 
Refund transaction can be applied to fee payment methond only and only when payment status still "Pending" which mean the customer has paid the fee but the biller still not collected it. If fee payment has been collected by the biller, refund transaction will raise error_code "1066".
  

-  **Endpoint**: `POST /api/v1/financial_corp/refund`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `payment_reference_id` | `INT` | - | **Must** | Transaction reference ID |

  

#### Code Example

```python

payload = json.dumps({

"payment_reference_id": "45892020712920875015"

})

response = client.post("/api/v1/financial_corp/refund", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "refund has been successfully processed",

"data": []

}

```

  

---

  

## 3. Query & Inquiry Endpoints

  

### 3.1 List Parent Sectors

Retrieves all top-level parent business sectors.

  

-  **Endpoint**: `GET /api/v1/financial_corp/get_parent_sectors`

-  **Headers**: Required RSA Security Headers

  
  

#### Code Example

```python

response = client.get("/api/v1/financial_corp/get_parent_sectors")

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Parent sectors found",

"data": [

{

"id": 29,

"name":  "القطاع الخاص بالمفوترين البنكيين"

},

{

"id": 30,

"name":  "القطاع الخاص"

}

]

}





```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `id` | `INT` | 3 | **Must** | Parent sector unique identifier |

| `name` | `STR` | 30 | **Must** | Parent sector localized display name |

  

---

  

### 3.2 List Sub-Sectors

Retrieves sub-sectors associated with a given parent sector ID.

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_sub_sectors`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `parent_sector_id` | `INT` | Max (3) | **Must** | Parent sector ID |

  

#### Code Example

```python

payload = json.dumps({"parent_sector_id": 29})

response = client.post("/api/v1/financial_corp/get_sub_sectors", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Sub sectors found",

"data":

[

{

"id": 30,

"name":  "القطاع العام"

},

{

"id": 35,

"name":  "القطاع الخاص"

}

]
}

```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `id` | `INT` | 10 | **Must** | Sub-sector unique identifier |

| `name` | `STR` | 40 | **Must** | Sub-sector localized display name |

  

---

  

### 3.3 List Billers

Retrieves billers registered under a specified sub-sector and service type filter.

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_billers_list`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `sector_id` | `INT` | Max (10) | **Must** | Sub-sector identifier |

| `service_type` | `ENUM(STR)` | `fees` \| `account` | **Must** | Service category type |

  

#### Code Example

```python

payload = json.dumps({

"sector_id": 29,

"service_type": "fees"

})

response = client.post("/api/v1/financial_corp/get_billers_list", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Billers found",
"data":

[

{

"id": 36,

"currency_codes": ["YER"],

"name":  "المتكامل"

},

{

"id": 28,

"currency_codes": ["SAR", "USD", "YER"],

"name":  "شركة محمد المطار"

},

{

"id": 27,

"currency_codes": ["YER"],

"name": "Test Company"

}

]
}
```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `id` | `INT` | 10 | **Must** | Biller unique identifier |

| `currency_codes` | `ARRAY[STR]` | - | **Must** | List of supported currency ISO codes |

| `biller_name` | `STR` | 40 | **Must** | Biller official business name |

  

---

  

### 3.4 Get Biller Pre-defined Fee Services

Fetches pre-defined fee services of a specific biller.

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_biller_services`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `biller_id` | `INT` | Max (10) | **Must** | Biller unique identifier |

  

#### Code Example

```python

payload = json.dumps({"biller_id": 23})

response = client.post("/api/v1/financial_corp/get_biller_services", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Billers found",

"data":

[

{

"service_id": 20005,

"currency_code": "YER",

"service_name":  "رسوم تحصيل خدمة توصيل2",

"biller_due_amount": 5000.0,

"customer_commission_amount": 500.0,

"total_amount": 5500.0

},

{

"service_id": 20003,

"currency_code": "USD",

"service_name":  "رسوم تسجيل",

"biller_due_amount": 10.0,

"customer_commission_amount": 0.0,

"total_amount": 10.0

}

]
}

```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `service_id` | `INT` | 10 | **Must** | Unique service identifier |

| `currency_code` | `STR` | Exact (3) | **Must** | Currency code (e.g., `YER`, `SAR`, `USD`) |

| `service_name` | `STR` | 40 | **Must** | Localized service description |

| `biller_due_amount` | `DOUBLE` | Max (15) | **Must** | Principal amount due to the biller |

| `customer_commission_amount` | `DOUBLE` | Max (15) | **Must** | Commission charged to customer (0 if biller-paid) |

| `total_amount` | `DOUBLE` | Max (15) | **Must** | Total payable amount (`biller_due_amount` + `customer_commission_amount`) |

  

---

  

### 3.5 Get Invoice Amount by Prepaid  Reference Id

Enquires about invoice details using an Ultimate Pay Prepaid Reference ID.

  

-  **Endpoint**: `POST /api/v1/financial_corp/invoice_amount`

-  **Headers**: Required RSA Security Headers

  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `prepaid_reference_id` | `STR` | Exact (14) | **Must** | Ultimate Pay prepaid reference number |

  

#### Code Example

```python

payload = json.dumps({

"prepaid_reference_id": "26000140973360"

})

response = client.post("/api/v1/financial_corp/invoice_amount", body=payload)

```

#### Payment Status

| :--- |

| `Paid` |

| `Partial paid` |

| `Not paid` |

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg":"Invoice amount found",

"data":{
  "currency_code": "YER",

  "biller_name":"Wisam Saif",

  "payment_status":"Paid",

  "biller_due_amount": 550.0,

  "customer_commission_amount": 55.0,

  "total_amount": 605.0,

  "total_paid_amount":100


}

}

```

  

#### Response Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `biller_name` | `STR` | max (30) | **Must** | Biller name |

| `payment_status` | `STR` | Max (7) | **Must** | Payment status |

| `currency_code` | `STR` | Exact (3) | **Must** | ISO currency code |

| `biller_due_amount` | `INT` | Max (15) | **Must** | Net amount payable to biller |

| `customer_commission_amount` | `INT` | Max (15) | **Must** | Service commission amount |

| `total_amount` | `INT` | Max (15) | **Must** | Final total amount due |

| `total_paid_amount` | `INT` | Max (15) | **Must** | The total paid amount of all of previouse parial payment transactions, if any |

  

---

  




### 3.6 Enquire of a Single Payment by Ulimate Payment Reference Id

Queries the status and metadata of a single payment transaction by providing the Payment Reference Id.

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_payment_by_reference_id`

-  **Headers**: Required RSA Security Headers

  
  

>**Payment status:** please refere to payment status table reference table of more clarification of payment status cases.

  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `payment_reference_id` | `INT` | - | **Must** | Transaction reference ID |

  

#### Code Example

```python

payload = json.dumps({

"payment_reference_id": "63565257557387753329"

})

response = client.post("/api/v1/financial_corp/get_payment_by_reference_id", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Payment found",

"data":

{

"biller": 1,

"payment_reference_id": "81252131095320646359",

"payment_status": "Paid",

"financial_corp_payment_id": "6952125223621452",

"paid_amount": 299,

"due_amount": 470.1,

"service_type": "bills",

"created_at": "2026-09-13T19:37:35.733101Z",

"currency_name": "YER",

"to_customer_no": null,

"to_customer_name": null,

"notes": "test",

"payer_name": "test",

"payer_type": 2,

"prepaid_reference_id": "26000140973360",

"id": 177

}

}

```

  

---

### 3.7 Enquire of a Single Payment  by Financial Corp Payment Id

Queries transaction status and metadata using a Financial corp payment ID.

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_payment_by_fin_payment_id`

-  **Headers**: Required RSA Security Headers

  
  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `financial_corp_payment_id` | `STR` | - | **Must** | Financial corp payemnt ID. |

  

#### Code Example

```python

payload = json.dumps({

"financial_corp_payment_id": "6952125223621452"

})

response = client.post("/api/v1/financial_corp/get_payment_by_fin_payment_id", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Payment found",


"data": [

{

"biller": 1,

"payment_reference_id": "81252131095320646359",

"payment_status": "Paid",

"financial_corp_payment_id": "6952125223621452",

"paid_amount": 299,

"due_amount": 470.1,

"service_type": "bills",

"created_at": "2026-09-13T19:37:35.733101Z",

"currency_name": "YER",

"to_customer_no": null,

"to_customer_name": null,

"notes": "test",

"payer_name": "test",

"payer_type": 2,

"prepaid_reference_id": "26000140973360",

"id": 177

}

]

}

```
  

### 3.8 Get List of Performed Transactions (Date Range Pagination)

Queries transactions that occurred during a selected time period. Supports pagination (10 records per page).

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_payment_by_dates`

-  **Headers**: Required RSA Security Headers

  
  

#### Code Example

```python

payload = json.dumps({

"from_date": "2025-02-01",

"to_date": "2027-02-02",

"page_no": 1

})

response = client.post("/api/v1/financial_corp/get_payment_by_dates", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Payments found",


"data": [

{

"biller": 1,

"payment_reference_id": "81252131095320646359",

"payment_status": "Paid",

"financial_corp_payment_id": "6952125223621452",

"paid_amount": 299,

"due_amount": 470.1,

"service_type": "bills",

"created_at": "2026-09-13T19:37:35.733101Z",

"currency_name": "YER",

"to_customer_no": null,

"to_customer_name": null,

"notes": "test",

"payer_name": "test",

"payer_type": 2,

"prepaid_reference_id": "26000140973360",

"id": 177

}

],

"paginate": {

"records_count": 1,

"num_pages": 1,

"current_page_number": 1,

"next": null,

"prev": null,

"per_page": 80,

"other_pages": [1]

}

}

```

  

---

  

### 3.9 Get List of Performed Transactions Starting from Specific Id(Pagination)

Queries transactions starting from a specified transaction "id" to the latest transaction with pagination support (10 records per page).

please note:
Id parameter is returned on response body of every payment transaction. This is a global sequence id that garantees all the payement transactions will be returned starting from this id number.

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_payment_start_with_id`

-  **Headers**: Required RSA Security Headers

  
  

#### Code Example

```python

payload = json.dumps({

"start_with_id": 177,

"page_no": 1

})

response = client.post("/api/v1/financial_corp/get_payment_start_with_id", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Payments found",


"data": [

{

"biller": 1,

"payment_reference_id": "81252131095320646359",

"payment_status": "Paid",

"financial_corp_payment_id": "6952125223621452",

"paid_amount": 299,

"due_amount": 470.1,

"service_type": "bills",

"created_at": "2026-09-13T19:37:35.733101Z",

"currency_name": "YER",

"to_customer_no": null,

"to_customer_name": null,

"notes": "test",

"payer_name": "test",

"payer_type": 2,

"prepaid_reference_id": "26000140973360",

"id": 177

}

],

"paginate": {

"records_count": 1,

"num_pages": 1,

"current_page_number": 1,

"next": null,

"prev": null,

"per_page": 80,

"other_pages": [1]

}

}

```

  

---

  



  
  
  

---

  

### 3.10 Enquire by Prepaid Reference ID

Queries the payment transaction(s) metadata that has made to a specific Biller invoice by providing the invoice Prepaid Reference ID.

  

-  **Endpoint**: `POST /api/v1/financial_corp/get_payments_by_prepaid_reference_id`

-  **Headers**: Required RSA Security Headers

  
  
  

#### Request Parameters

| Field Name | Type | Length / Constraint | Required | Description |

| :--- | :--- | :--- | :--- | :--- |

| `prepaid_reference_id` | `STR` | - | **Must** | Prepaid Reference ID. |

  

#### Code Example

```python

payload = json.dumps({

"prepaid_reference_id": "26000140973360"

})

response = client.post("/api/v1/financial_corp/get_payments_by_prepaid_reference_id", body=payload)

```

  

#### Response Example (`200 OK`)

```json

{

"status": "success",

"msg": "Payment found",


"data": [

{

"biller": 1,

"payment_reference_id": "81252131095320646359",

"payment_status": "Paid",

"financial_corp_payment_id": "6952125223621452",

"paid_amount": 299,

"due_amount": 470.1,

"service_type": "bills",

"created_at": "2026-09-13T19:37:35.733101Z",

"currency_name": "YER",

"to_customer_no": null,

"to_customer_name": null,

"notes": "test",

"payer_name": "test",

"payer_type": 2,

"prepaid_reference_id": "26000140973360",

"id": 177

},

{

"biller": 1,

"payment_reference_id": "36215742718234805452",

"payment_status": "Paid",

"financial_corp_payment_id": "6952125223621452",

"paid_amount": 156,

"due_amount": 484.4,

"service_type": "bills",

"created_at": "2026-09-13T18:43:58.481998Z",

"currency_name": "YER",

"to_customer_no": null,

"to_customer_name": null,

"notes": "test",

"payer_name": "test",

"payer_type": 2,

"prepaid_reference_id": "26000140973360",

"id": 176

},

{

"biller": 1,

"payment_reference_id": "89622711922941931083",

"payment_status": "Paid",

"financial_corp_payment_id": "6952125223621452",

"paid_amount": 45,

"due_amount": 495.5,

"service_type": "bills",

"created_at": "2026-09-13T18:43:30.854123Z",

"currency_name": "YER",

"to_customer_no": null,

"to_customer_name": null,

"notes": "test",

"payer_name": "test",

"payer_type": 2,

"prepaid_reference_id": "26000140973360",

"id": 175

}

]

}

```



### 3.11 Get Customer Name & Account Details

Queries the biller system to verify customer details and calculate commissions prior to payment.

-    **Endpoint**: `POST /api/v1/financial_corp/customer_name`
-    **Headers**: Required RSA Security Headers


#### Request Parameters
| Field Name | Type | Length / Constraint | Required | Description |
| :--- | :--- | :--- | :--- | :--- |
| `biller_id` | `INT` | Max (10) | **Must** | Target biller identifier |
| `currency_code` | `STR` | Exact (3) | **Must** | ISO currency code (e.g., `YER`) |
| `to_customer_no` | `STR` | Max (250) | **Must** | Customer subscriber/account number |
| `amount` | `INT` | Max (15) | **Must** | Payment amount (used for dynamic commission calculation) |

#### Code Example
```python
payload = json.dumps({
    "biller_id": 23,
    "currency_code": "YER",
    "amount": 500,
    "to_customer_no": "12345"
})
response = client.post("/api/v1/financial_corp/customer_name", body=payload)
```

#### Response Example (`200 OK`)
```json

  {
    "status": "success",
    "msg":"Customer found",
    "data":{

          "to_customer_name": "test",
          "currency_code": "YER",
          "biller_due_amount": 500,
          "customer_commission_amount": 50,
          "total_amount": 550

    }

  }

```




### 3.12 Bank Biller Callback Protocol
For banking billers, contact details must be pre-configured to forward transaction payment notification results.

#### Callback Body Example
```json
{
  "financial_corp_payment_id": "69553362125695632",
  "jsonBody": {
    "id": 128,
    "payment_reference_id": "79745728271967805491",
    "service_type": "account",
    "financial_corp_commission_amount": 5.5,
    "created_at": "2026-08-17T16:01:12.554402Z",
    "financial_corp_payment_id": "69553362125695632"
  }
}
```
