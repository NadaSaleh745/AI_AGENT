# To run this code you need to install the following dependencies:
# pip install google-genai

import os
import sys
import argparse
import google.generativeai as genai
import sqlite3
from pathlib import Path
from dotenv import load_dotenv


conn = sqlite3.connect("/Users/nada/PycharmProjects/AI_AGENTS_PROJECT/erp_demo.db")
cursor = conn.cursor()

env_path = Path(__file__).resolve().parent / ".env"
dotenv_used = False
dotenv_available = load_dotenv is not None
if dotenv_available and env_path.exists():
    try:
        load_dotenv(dotenv_path=str(env_path), override=False)
        dotenv_used = True
    except Exception:
        dotenv_used = False

# CLI arg to override API key
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--api-key", dest="cli_api_key", default=None)
known_args, _ = parser.parse_known_args()

# Read key with extended alias list and CLI override
alias_vars = [
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
]

api_key = known_args.cli_api_key or next((os.getenv(v) for v in alias_vars if os.getenv(v)), None)
api_key_source = "--api-key" if known_args.cli_api_key else next((v for v in alias_vars if os.getenv(v)), None)


genai.configure(api_key=api_key)

schema = """
PRAGMA foreign_keys = ON;

-- Customers
CREATE TABLE Customers (
    CustomerId        INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerCode      TEXT UNIQUE NOT NULL,
    CustomerName      TEXT NOT NULL,
    Email             TEXT NULL,
    Phone             TEXT NULL,
    BillingAddress1   TEXT NULL,
    BillingCity       TEXT NULL,
    BillingCountry    TEXT NULL,
    CreatedAt         TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt         TEXT NULL,
    IsActive          INTEGER NOT NULL DEFAULT 1
);

-- Vendors
CREATE TABLE Vendors (
    VendorId      INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorCode    TEXT UNIQUE NOT NULL,
    VendorName    TEXT NOT NULL,
    Email         TEXT NULL,
    Phone         TEXT NULL,
    AddressLine1  TEXT NULL,
    City          TEXT NULL,
    Country       TEXT NULL,
    CreatedAt     TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt     TEXT NULL,
    IsActive      INTEGER NOT NULL DEFAULT 1
);

-- Sites
CREATE TABLE Sites (
    SiteId      INTEGER PRIMARY KEY AUTOINCREMENT,
    SiteCode    TEXT UNIQUE NOT NULL,
    SiteName    TEXT NOT NULL,
    AddressLine1 TEXT NULL,
    City        TEXT NULL,
    Country     TEXT NULL,
    TimeZone    TEXT NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt   TEXT NULL,
    IsActive    INTEGER NOT NULL DEFAULT 1
);

-- Locations (self-referencing)
CREATE TABLE Locations (
    LocationId       INTEGER PRIMARY KEY AUTOINCREMENT,
    SiteId           INTEGER NOT NULL,
    LocationCode     TEXT NOT NULL,
    LocationName     TEXT NOT NULL,
    ParentLocationId INTEGER NULL,
    CreatedAt        TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt        TEXT NULL,
    IsActive         INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT UQ_Locations_SiteCode UNIQUE (SiteId, LocationCode),
    CONSTRAINT FK_Locations_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    CONSTRAINT FK_Locations_Parent FOREIGN KEY (ParentLocationId) REFERENCES Locations(LocationId)
);

-- Items
CREATE TABLE Items (
    ItemId         INTEGER PRIMARY KEY AUTOINCREMENT,
    ItemCode       TEXT UNIQUE NOT NULL,
    ItemName       TEXT NOT NULL,
    Category       TEXT NULL,
    UnitOfMeasure  TEXT NULL,
    CreatedAt      TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt      TEXT NULL,
    IsActive       INTEGER NOT NULL DEFAULT 1
);

-- Assets
CREATE TABLE Assets (
    AssetId       INTEGER PRIMARY KEY AUTOINCREMENT,
    AssetTag      TEXT UNIQUE NOT NULL,
    AssetName     TEXT NOT NULL,
    SiteId        INTEGER NOT NULL,
    LocationId    INTEGER NULL,
    SerialNumber  TEXT NULL,
    Category      TEXT NULL,
    Status        TEXT NOT NULL DEFAULT 'Active',
    Cost          NUMERIC NULL,
    PurchaseDate  TEXT NULL,
    VendorId      INTEGER NULL,
    CreatedAt     TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt     TEXT NULL,
    CONSTRAINT FK_Assets_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId),
    CONSTRAINT FK_Assets_Location FOREIGN KEY (LocationId) REFERENCES Locations(LocationId),
    CONSTRAINT FK_Assets_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

-- Bills
CREATE TABLE Bills (
    BillId       INTEGER PRIMARY KEY AUTOINCREMENT,
    VendorId     INTEGER NOT NULL,
    BillNumber   TEXT NOT NULL,
    BillDate     TEXT NOT NULL,
    DueDate      TEXT NULL,
    TotalAmount  NUMERIC NOT NULL,
    Currency     TEXT NOT NULL DEFAULT 'USD',
    Status       TEXT NOT NULL DEFAULT 'Open',
    CreatedAt    TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt    TEXT NULL,
    CONSTRAINT UQ_Bills_Vendor_BillNumber UNIQUE (VendorId, BillNumber),
    CONSTRAINT FK_Bills_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId)
);

-- Purchase Orders
CREATE TABLE PurchaseOrders (
    POId        INTEGER PRIMARY KEY AUTOINCREMENT,
    PONumber    TEXT NOT NULL,
    VendorId    INTEGER NOT NULL,
    PODate      TEXT NOT NULL,
    Status      TEXT NOT NULL DEFAULT 'Open',
    SiteId      INTEGER NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt   TEXT NULL,
    CONSTRAINT UQ_PurchaseOrders_Number UNIQUE (PONumber),
    CONSTRAINT FK_PurchaseOrders_Vendor FOREIGN KEY (VendorId) REFERENCES Vendors(VendorId),
    CONSTRAINT FK_PurchaseOrders_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

-- Purchase Order Lines
CREATE TABLE PurchaseOrderLines (
    POLineId    INTEGER PRIMARY KEY AUTOINCREMENT,
    POId        INTEGER NOT NULL,
    LineNumber  INTEGER NOT NULL,
    ItemId      INTEGER NULL,
    ItemCode    TEXT NOT NULL,
    Description TEXT NULL,
    Quantity    NUMERIC NOT NULL,
    UnitPrice   NUMERIC NOT NULL,
    CONSTRAINT UQ_PurchaseOrderLines UNIQUE (POId, LineNumber),
    CONSTRAINT FK_PurchaseOrderLines_PO FOREIGN KEY (POId) REFERENCES PurchaseOrders(POId),
    CONSTRAINT FK_PurchaseOrderLines_Item FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
);

-- Sales Orders
CREATE TABLE SalesOrders (
    SOId        INTEGER PRIMARY KEY AUTOINCREMENT,
    SONumber    TEXT NOT NULL,
    CustomerId  INTEGER NOT NULL,
    SODate      TEXT NOT NULL,
    Status      TEXT NOT NULL DEFAULT 'Open',
    SiteId      INTEGER NULL,
    CreatedAt   TEXT NOT NULL DEFAULT (datetime('now')),
    UpdatedAt   TEXT NULL,
    CONSTRAINT UQ_SalesOrders_Number UNIQUE (SONumber),
    CONSTRAINT FK_SalesOrders_Customer FOREIGN KEY (CustomerId) REFERENCES Customers(CustomerId),
    CONSTRAINT FK_SalesOrders_Site FOREIGN KEY (SiteId) REFERENCES Sites(SiteId)
);

-- Sales Order Lines
CREATE TABLE SalesOrderLines (
    SOLineId    INTEGER PRIMARY KEY AUTOINCREMENT,
    SOId        INTEGER NOT NULL,
    LineNumber  INTEGER NOT NULL,
    ItemId      INTEGER NULL,
    ItemCode    TEXT NOT NULL,
    Description TEXT NULL,
    Quantity    NUMERIC NOT NULL,
    UnitPrice   NUMERIC NOT NULL,
    CONSTRAINT UQ_SalesOrderLines UNIQUE (SOId, LineNumber),
    CONSTRAINT FK_SalesOrderLines_SO FOREIGN KEY (SOId) REFERENCES SalesOrders(SOId),
    CONSTRAINT FK_SalesOrderLines_Item FOREIGN KEY (ItemId) REFERENCES Items(ItemId)
);

-- Asset Transactions
CREATE TABLE AssetTransactions (
    AssetTxnId     INTEGER PRIMARY KEY AUTOINCREMENT,
    AssetId        INTEGER NOT NULL,
    FromLocationId INTEGER NULL,
    ToLocationId   INTEGER NULL,
    TxnType        TEXT NOT NULL,
    Quantity       INTEGER NOT NULL DEFAULT 1,
    TxnDate        TEXT NOT NULL DEFAULT (datetime('now')),
    Note           TEXT NULL,
    CONSTRAINT FK_AssetTransactions_Asset FOREIGN KEY (AssetId) REFERENCES Assets(AssetId),
    CONSTRAINT FK_AssetTransactions_FromLoc FOREIGN KEY (FromLocationId) REFERENCES Locations(LocationId),
    CONSTRAINT FK_AssetTransactions_ToLoc FOREIGN KEY (ToLocationId) REFERENCES Locations(LocationId)
)
"""


retrieval_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=f"""
        You are a helpful AI assistant specialized in databases and backend engineering.
        Always provide clear, structured explanations. Convert user questions into valid SQLite SQL queries.
        Return ONLY the SQL query. Generate valid sqlite3 query. Do not alter the tables or columns, do not drop any too.
        Do not explain anything. Return ONLY raw SQL. Do NOT use markdown. Do NOT wrap the query in backticks. When returning the result rows,
        only return the related columns to the request.
        Use this schema:
        {schema}
        """
)

explanation_model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=f"""
        You are a helpful AI assistant specialized in databases and backend engineering, and you're also very good at explaining things.
        You receive sql results and explain them in human readable friendly format.
        """
)

print("Hello! I'm your assistant. How can I help you today?")
retrieval_chat = retrieval_model.start_chat()

while True:
    user_input = input("You: ")
    response = retrieval_chat.send_message(user_input)
    sql_query = response.text.strip()
    print(f"SQL Query: {sql_query}")

    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()
        print("Results:")
        for row in rows:
            print(row)
        if rows:
            explanation_prompt = f"""
                User question: {user_input}
    
                SQL query executed:
                {sql_query}
    
                SQL result rows:
                {rows}
    
                Explain these results clearly in a friendly human-readable way.
                """

            explanation_response = explanation_model.generate_content(explanation_prompt)
            explanation_text = explanation_response.text.strip()

            print("\nExplanation:")
            print(explanation_text)
        else:
            print("\nExplanation:")
            print("No records were found matching your request.")

    except Exception as e:
        print("SQL Error:", e)




