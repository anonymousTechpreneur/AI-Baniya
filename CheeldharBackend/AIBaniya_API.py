import os
import io
import logging
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.api_core.client_options import ClientOptions
import pandas as pd
import vertexai
from vertexai.generative_models import (
    Content,
    FunctionDeclaration,
    GenerationConfig,
    GenerativeModel,
    Part,
    Tool,
)
from google.cloud import bigquery
from google.cloud import storage
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

google_credentials = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
if not google_credentials:
    # Set the environment variable programmatically
    credentials_path = "D:\\CheeldharBackend\\key_STT.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
    google_credentials = credentials_path  # Update local variable to reflect change

# Verify if the environment variable is correctly set
if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
    print("Nahi Chla Error 2")

# Initialize the BigQuery client
client = bigquery.Client()

# Hardcoded credentials
VALID_EMAIL = "user@example.com"
VALID_PASSWORD = "securepassword"
project_id = "planar-method-425304-t6"
region = "us-central1"
recognizer_id = "test-recognizer"

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def model_init(project_id, region):
    vertexai.init(project=project_id, location=region)
    model = GenerativeModel("gemini-1.5-flash-001")
    return model

model = model_init(project_id, region)

current_session = {
    "customer_id": None,
    "bill_id": None
}

def update_current_action(action_data):
    global current_action
    current_action = action_data

def get_current_action():
    global current_action
    return current_action

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",  # Frontend application URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, e.g., GET, POST, PUT, DELETE
    allow_headers=["*"],  # Allows all headers
)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    if request.email == VALID_EMAIL and request.password == VALID_PASSWORD:
        return {"message": "Login successful"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

class TempDatabase:
    def __init__(self):
        self.dataframes = {}  # Dictionary to store multiple dataframes

    def create_dataframe(self, name: str, columns: list):
        """Create a new dataframe with specified columns."""
        if name in self.dataframes:
            raise ValueError(f"DataFrame with name '{name}' already exists.")
        self.dataframes[name] = pd.DataFrame(columns=columns)

    def add_data(self, name: str, data: list):
        """Add data to an existing dataframe."""
        if name not in self.dataframes:
            raise ValueError(f"DataFrame with name '{name}' does not exist.")
        df = self.dataframes[name]
        new_df = pd.DataFrame(data, columns=df.columns)
        self.dataframes[name] = pd.concat([df, new_df], ignore_index=True)

    def delete_data(self, name: str, condition):
        """Delete rows from an existing dataframe based on a condition."""
        if name not in self.dataframes:
            raise ValueError(f"DataFrame with name '{name}' does not exist.")
        df = self.dataframes[name]
        self.dataframes[name] = df[~condition(df)]

    def change_data(self, name: str, condition, new_values):
        """Change data in an existing dataframe based on a condition."""
        if name not in self.dataframes:
            raise ValueError(f"DataFrame with name '{name}' does not exist.")
        df = self.dataframes[name]
        self.dataframes[name].loc[condition(df), :] = new_values

    def clear_dataframe(self, name: str):
        """Clear data from an existing dataframe."""
        if name not in self.dataframes:
            raise ValueError(f"DataFrame with name '{name}' does not exist.")
        self.dataframes[name] = pd.DataFrame(columns=self.dataframes[name].columns)

    def get_dataframe(self, name: str):
        """Retrieve an existing dataframe."""
        if name not in self.dataframes:
            raise ValueError(f"DataFrame with name '{name}' does not exist.")
        return self.dataframes[name]

    def list_dataframes(self):
        """List the names of all existing dataframes."""
        return list(self.dataframes.keys())

db = TempDatabase()

#create empty data frames
db.create_dataframe('Products', ['SKU_No', 'Name', 'Category', 'ProductDescription', 'productAudio', 'productImage'])
db.create_dataframe('Supplier', ['SupplierId', 'SupplierName', 'SupplierPhoneNo', 'SupplierAddress', 'SupplierGSTNo', 'SupplierFirmName', 'SupplierBankAccountNo', 'SupplierIFSCCode', 'SupplierBank', 'SupplierPAN', 'SupplierFSSAI', 'SupplierRTALNo', 'SupplierManager'])
db.create_dataframe('Inventory', ["InventoryID", "Quantity", "PerPieceWeight", "TotalPieces", "ExpiryDate", "PurchaseBillDate", "HSNNumber", "CostPerPrice", "ExtraCostPerPrice", "MinimumSellingPrice", "MaximumSellingPrice", "GST_Percentage", "PurchaseBillNo", "PurchaseFirmName", "SupplierId", "TotalBillAmount", "BillPhoto", "SKU_No"])
db.create_dataframe('Customer', ["CustomerId", "Name", "PhoneNumber", "EmailId", "Address", "GSTNumber", "NameAudioFile", "CustomerImageFile"])
db.create_dataframe('Firms', ["FirmID", "FirmName", "FirmPhoneNo", "FirmAddress", "FirmGSTNo", "FirmBankAccountNo", "FirmIFSCCode", "FirmBank", "FirmPAN", "FirmFSSAI", "FirmRTALNo", "FirmManager"])
db.create_dataframe('Bill', ["BillID", "CustomerId", "PaymentType", "TotalBillAmount", "PaidAmount", "RemainingAmount", "BillDate"])
db.create_dataframe('Orders', ["OrderId", "BillID", "SKU_No", "WeightQuantity", "TotalPieces", "Discount", "SellingPrice", "FirmID", "GST_Percentage", "TotalGST", "TotalAmount"])

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    logger.info('File %s uploaded to %s.', source_file_name, destination_blob_name)

def get_new_id(table, column_name, df):
    query = f"""
    SELECT IFNULL(MAX(CAST({column_name} AS INT64)), 0) AS max_id
    FROM `AI_Baniya.{table}`
    """
    query_job = client.query(query)
    result = query_job.result()
    max_id = next(result).max_id

    new_id = max_id + 1

    # Step 2: Check if the new BillID exists in the DataFrame
    if df is not None:
        while new_id in df[column_name].values:
            new_id += 1

    return new_id

def get_bq_data(table, column_name):
    query = f"""
    SELECT {column_name}
    FROM `AI_Baniya.{table}`
    """

    # Execute the query
    query_job = client.query(query)
    result = query_job.result()

    data = []
    for row in result:
        data.append(row[column_name])
    return data

from rapidfuzz import fuzz, process

def add_customer(customer_data):
    customer_id = get_new_id("Customer", "CustomerId", db.get_dataframe("Customer"))
    name = customer_data.get("name", None)
    phone_number = customer_data.get("phone_number", None)
    email_id = customer_data.get("email_id", None)
    address = customer_data.get("address", None)
    gst_number = customer_data.get("gst_number", None)
    name_audio_file = customer_data.get("name_audio_file", None)
    customer_image_file = customer_data.get("customer_image_file", None)

    # Check for existing customers with similar names
    existing_customers = db.get_dataframe("Customer")
    customer_names = existing_customers["Name"].tolist()
    similar_customers = process.extract(name, customer_names, scorer=fuzz.partial_ratio, limit=5)

    # Filter similar customers with a similarity score above a threshold (e.g., 80)
    similar_customers = [customer for customer in similar_customers if customer[1] >= 80]

    if similar_customers:
        similar_customers_data = []
        for match in similar_customers:
            matched_name = match[0]
            customer_record = existing_customers[existing_customers["Name"] == matched_name].to_dict(orient="records")
            similar_customers_data.extend(customer_record)
        
        # Return similar customers for UI to choose from
        return {"similar_customers": similar_customers_data}

    # Add new customer data to the dataframe
    new_customer = {
        "CustomerId": customer_id,
        "Name": name,
        "PhoneNumber": phone_number,
        "EmailId": email_id,
        "Address": address,
        "GSTNumber": gst_number,
        "NameAudioFile": name_audio_file,
        "CustomerImageFile": customer_image_file
    }

    db.add_data("Customer", [new_customer])
    return {"message": "Customer added successfully"}

def place_order(order_data):
    customer_name = order_data.get("customer_name")
    product_name = order_data.get("product_name")
    quantity = order_data.get("quantity")
    discount = order_data.get("discount", 0)

    existing_customers = db.get_dataframe("Customer")
    customer = existing_customers[existing_customers["Name"] == customer_name]
    if customer.empty:
        return {"error": "Customer not found"}

    customer_id = customer.iloc[0]["CustomerId"]

    if current_session["customer_id"] != customer_id:
        current_session["customer_id"] = customer_id
        current_session["bill_id"] = get_new_id("Bill", "BillID", db.get_dataframe("Bill"))

    bill_id = current_session["bill_id"]

    existing_products = db.get_dataframe("Products")
    similar_products = process.extract(product_name, existing_products["Name"].tolist(), scorer=fuzz.partial_ratio, limit=5)
    similar_products = [product for product in similar_products if product[1] >= 80]

    if similar_products:
        product_name = similar_products[0][0]
        product = existing_products[existing_products["Name"] == product_name].iloc[0]
    else:
        product_id = get_new_id("Products", "SKU_No", db.get_dataframe("Products"))
        new_product = {
            "SKU_No": product_id,
            "Name": product_name,
            "Category": None,
            "ProductDescription": None,
            "productAudio": None,
            "productImage": None
        }
        db.add_data("Products", [new_product])
        product = new_product

    SKU_No = product["SKU_No"]
    price = product.get("CostPerPrice", 0)
    gst_percentage = product.get("GST_Percentage", 0)
    total_price = quantity * price * (1 + gst_percentage / 100) - discount

    order_id = get_new_id("Orders", "OrderId", db.get_dataframe("Orders"))

    new_order = {
        "OrderId": order_id,
        "BillID": bill_id,
        "SKU_No": SKU_No,
        "WeightQuantity": None,
        "TotalPieces": quantity,
        "Discount": discount,
        "SellingPrice": price,
        "FirmID": None,
        "GST_Percentage": gst_percentage,
        "TotalGST": total_price * gst_percentage / 100,
        "TotalAmount": total_price
    }
    db.add_data("Orders", [new_order])

    new_bill = {
        "BillID": bill_id,
        "CustomerId": customer_id,
        "PaymentType": None,
        "TotalBillAmount": total_price,
        "PaidAmount": 0,
        "RemainingAmount": total_price,
        "BillDate": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    existing_bill = db.get_dataframe("Bill")[db.get_dataframe("Bill")["BillID"] == bill_id]
    if existing_bill.empty:
        db.add_data("Bill", [new_bill])
    else:
        db.change_data("Bill", lambda df: df["BillID"] == bill_id, {
            "TotalBillAmount": existing_bill["TotalBillAmount"].iloc[0] + total_price,
            "RemainingAmount": existing_bill["RemainingAmount"].iloc[0] + total_price
        })

    return {"message": "Order placed successfully", "order_id": order_id, "bill_id": bill_id, "total_amount": total_price}

def change_order(order_data):
    order_id = order_data.get("order_id")
    changes = order_data.get("changes", {})

    # Find the order
    existing_orders = db.get_dataframe("Orders")
    order = existing_orders[existing_orders["OrderId"] == order_id]
    if order.empty:
        return {"error": "Order not found"}

    order = order.iloc[0]
    for key, value in changes.items():
        if key in order:
            order[key] = value

    # Recalculate totals if necessary
    if "TotalPieces" in changes or "SellingPrice" in changes or "Discount" in changes or "GST_Percentage" in changes:
        quantity = changes.get("TotalPieces", order["TotalPieces"])
        price = changes.get("SellingPrice", order["SellingPrice"])
        discount = changes.get("Discount", order["Discount"])
        gst_percentage = changes.get("GST_Percentage", order["GST_Percentage"])
        total_price = quantity * price * (1 + gst_percentage / 100) - discount
        order["TotalAmount"] = total_price
        order["TotalGST"] = total_price * gst_percentage / 100

    db.change_data("Orders", lambda df: df["OrderId"] == order_id, order)
    return {"message": "Order changed successfully", "order_id": order_id}

def remove_order(order_data):
    order_id = order_data.get("order_id")

    # Find the order
    existing_orders = db.get_dataframe("Orders")
    order = existing_orders[existing_orders["OrderId"] == order_id]
    if order.empty:
        return {"error": "Order not found"}

    # Remove the order
    db.delete_data("Orders", lambda df: df["OrderId"] == order_id)
    return {"message": "Order removed successfully"}

@app.get("/current-action")
async def get_current_action_info():
    current_action = get_current_action()
    if current_action:
        return {"current_action": current_action}
    else:
        raise HTTPException(status_code=404, detail="No current action found")

@app.post("/chatbot")
async def chatbot(file: UploadFile = File(...)):
    audio_path = "D:\\Cheeldhar\\AI-Baniya\\order.wav"
    try:
        with open(audio_path, "wb") as audio_file:
            content = await file.read()
            audio_file.write(content)
        upload_blob("ai_baniya_data", audio_path, "sample_audio_files/order.wav")

        audio_path_uri = "gs://ai_baniya_data/sample_audio_files/order.wav"
        audio_file = Part.from_uri(audio_path_uri, mime_type="audio/wav")

        action_data = LLMChat(model, audio_file)
        update_current_action(action_data)
        
        action = action_data.get("action")
        details = action_data.get("details")

        if action == "Add Customer":
            current_session["customer_id"] = None  # Reset current session
            response_data = add_customer(details)
            return {"message": "Operation successful", "details": db.get_dataframe('Customer')}
        elif action == "Place Order":
            response_data = place_order(details)
            return {"message": "Operation successful", "details": details}
        elif action == "Change Order":
            response_data = change_order(details)
        elif action == "Remove Order":
            response_data = remove_order(details)
        else:
            raise HTTPException(status_code=500, detail=f"Error during process: {str(e)}")

        return {"message": "Operation successful", "details": response_data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during process: {str(e)}")

def LLMChat(model, audio_file):

    prompt = """
    You are an AI assistant that extracts actionable information from audio recordings. The audio recordings contain various user instructions. Your task is to:
    1. Identify the action the user wants to perform.
    2. Extract relevant details associated with the action.
    3. Return the information in a structured JSON format.

    Actions include:
    - Add Customer
    - Add Product
    - Place Order
    - Change Order
    - Remove Order
    - Query Inventory

    For each action, extract the following details if mentioned:
    - Add Customer: name, phone_number, email_id, address, gst_number, name_audio_file, customer_image_file
    - Add Product: SKU_No, name, category, product_description, product_audio, product_image
    - Place Order: customer_name, product_name, quantity, discount
    - Change Order: order_id, changes (as a dictionary)
    - Remove Order: order_id
    - Query Inventory: SKU_No, quantity

    Return the output in the following JSON format:{"action":"<action>","details":{"<detail_key>": "<detail_value>",...}}

    Examples:
    Input: "I want to add a customer named John Doe. His phone number is 1234567890."
    Output:{"action":"Add Customer","details":{"name":"John Doe","phone_number":"1234567890","email_id":null,"address":null,"gst_number":null,"name_audio_file":null,"customer_image_file":null}}

    Input: "Place an order for 10 units of product with SKU 12345."
    Output:{"action":"Place Order","details":{"customer_name": null,"product_name":"product with SKU 12345","quantity":10,"discount": null}}"""

    contents = [audio_file, prompt]

    response = model.generate_content(contents)
    logger.info(response.text)
    try:
        response_json = response.text.strip()  # Assuming the response is in JSON format
        # data = json.load(response_json[8:-4])  # Parse JSON string to Python dictionary
        y = response_json[8:-4]
        print(y)
        try:
            data = json.loads(y)
        except:
            data = eval(y)
        print(data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Error parsing response: {str(e)}")

    # Ensure the response has the necessary keys
    if not isinstance(data, dict):
        raise HTTPException(status_code=500, detail="Invalid response format")

    # Default return if keys are missing
    return {
        "action": data.get("action", "unknown"),
        "details": data.get("details", {})
    }