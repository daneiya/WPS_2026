# Wallet and Payment System (WPS)

## 1. Project Overview

The Wallet and Payment System is a Django REST Framework application that allows users to manage digital wallets and perform basic financial transactions.

The system supports wallet creation, wallet balance checking, money top-up, withdrawal, and transfers between users.

It also includes transaction history, idempotency to prevent duplicate transfers, daily transfer limits, wallet freezing, and balance reconciliation.

## 2. Technologies Used

- Python
- Django
- Django REST Framework (DRF)
- MySQL 8
- Django REST Framework Simple JWT
- Django Filter
- DRF Spectacular (Swagger API documentation)
- Python Dotenv
- Postman (API testing)
- Git and GitHub

## 3. Project Setup – Step by Step

### Step 1: Get the Project from GitHub

First, open the terminal in VS Code or Command Prompt.

Navigate to the folder where you want to keep the project.

If you have already cloned the repository, move into the project folder and pull the latest changes:

-----
cd "D:\Camp4 (django REST API)\WPS_2026"
git pull origin main
----

If you are downloading the repository for the first time, use:

----
git clone https://github.com/daneiya/WPS_2026.git
cd WPS_2026
----

### Step 2: Create a Virtual Environment

A virtual environment keeps the packages required for this project separate from other Python projects.

Create the virtual environment:

---
python -m venv myvenv
----

Activate it:

-----
myvenv\Scripts\activate
-----

After activation, the terminal should display:

----
(myvenv)
---

### Step 3: Install Required Packages

Install Django and Django REST Framework:
----
pip install django djangorestframework
----

Install the additional packages required for the project:

----
pip install mysqlclient djangorestframework-simplejwt python-dotenv django-filter drf-spectacular
----

These packages are used for:

- `django`: Main web framework.
- `djangorestframework`: Building REST APIs.
- `mysqlclient`: Connecting Django to MySQL.
- `djangorestframework-simplejwt`: JWT authentication.
- `python-dotenv`: Reading environment variables from the `.env` file.
- `django-filter`: Filtering API results.
- `drf-spectacular`: Generating Swagger API documentation.

### Step 4: Create the Django Project

Create the Django project inside the current folder:

-----
django-admin startproject config .
-----

The dot (`.`) means Django should create the project in the current directory instead of creating another nested folder.

### Step 5: Create the Wallet Application

Create the wallet application:
-----
python manage.py startapp wallet
-----

The `wallet` application contains the functionality related to wallet management and transactions.

### Step 6: Configure Django Settings

Open:


config/settings.py


Configure the following:

1. Register the required Django and third-party applications in `INSTALLED_APPS`.
2. Register the `wallet` application.
3. Configure the MySQL database connection.
4. Load environment variables using `python-dotenv`.
5. Configure Django REST Framework.
6. Configure JWT authentication.
7. Configure Swagger documentation.
8. Set the project timezone to `Asia/Kolkata`.

### Step 7: Configure Environment Variables

Create a `.env` file in the root project folder.

Add your own database credentials and Django secret key:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=wallet_payment_system
DB_USER=root
DB_PASSWORD=your-mysql-password
DB_HOST=localhost
DB_PORT=3306
```

**Important:** Never upload the actual `.env` file or database password to GitHub.

Create a `.env.example` file with placeholder values so other developers know which variables are required.

### Step 8: Create the MySQL Database

Open MySQL Workbench and create the database:

----
CREATE DATABASE wallet_payment_system;
----

Django will use this database to store users, wallets, transactions, transfer requests, and idempotency records.

### Step 9: Configure the Database Connection

In `config/settings.py`, configure the database engine as MySQL and read the database details from the `.env` file.

The database connection uses:

- Database name
- Database username
- Database password
- Database host
- Database port

### Step 10: Check the Django Project

Run:

----
python manage.py check
------
This command checks the Django project for configuration errors.

### Step 11: Create the Database Models

Open:


wallet/models.py


Create the following models:

#### 1. Wallet

Stores wallet information for each user.

Important fields:

- User
- Balance
- Is Frozen
- Created At
- Updated At

Each user has one wallet.

#### 2. Transaction

Stores all wallet transactions.

Important fields:

- Wallet
- Transaction Type
- Amount
- Reference ID
- Related Wallet
- Description
- Created At

Transaction types include:

- TOPUP
- TRANSFER_IN
- TRANSFER_OUT
- WITHDRAWAL

#### 3. TransferRequest

Stores information about money transfers between two wallets.

Important fields:

- Sender Wallet
- Receiver Wallet
- Amount
- Status
- Reference ID
- Created At
- Completed At

#### 4. IdempotencyKey

Stores idempotency information to prevent duplicate transaction requests.

Important fields:

- User
- Key
- Request Hash
- Response Status
- Response Body
- Created At

### Step 12: Create and Apply Migrations

After creating the models, generate migration files:
----
python manage.py makemigrations wallet
----

Apply the migrations to MySQL:
----
python manage.py migrate
----

Migrations convert Django model definitions into database tables.

### Step 13: Configure Django Admin

Open:

----
wallet/admin.py
-----

Register the Wallet, Transaction, TransferRequest, and IdempotencyKey models.

This allows administrators to view and manage these records through the Django admin panel.

Create a superuser:

----
python manage.py createsuperuser
----

The admin panel can be accessed at:
----
http://127.0.0.1:8000/admin/
---

### Step 14: Create Serializers

Open:


wallet/serializers.py


Serializers convert Django model objects into JSON responses and validate incoming API data.

The following serializers were created:

- `WalletSerializer`
- `TransactionSerializer`
- `TopUpSerializer`
- `WithdrawalSerializer`
- `TransferSerializer`
- `TransferRequestSerializer`

Validation is used to check the amount and prevent a user from transferring money to their own wallet.

### Step 15: Create the Service Layer

Create the file:


wallet/services.py


The service layer contains the main business logic of the wallet system.

The following functions were created:

- `get_user_wallet()`: Retrieves the wallet belonging to a user.
- `create_wallet()`: Creates a wallet for a user.
- `check_wallet_status()`: Checks whether a wallet is frozen.
- `top_up_wallet()`: Adds money to a wallet.
- `withdraw_money()`: Deducts money from a wallet.
- `check_daily_transfer_limit()`: Checks the user's daily transfer limit.
- `transfer_money()`: Transfers money from one wallet to another.

Database transactions and row locking are used during money-related operations to help maintain data consistency.

### Step 16: Create API Views

Open:


wallet/views.py


Views receive HTTP requests, call the appropriate serializer and service functions, and return HTTP responses.

The following API views were created:

- `CreateWalletView`
- `WalletDetailView`
- `TopUpView`
- `WithdrawalView`
- `TransferView`
- `TransactionStatementView`
- `WalletReconciliationView`
- `WalletFreezeView`

The transfer view also handles the `Idempotency-Key` request header to prevent duplicate successful transfers.

### Step 17: Configure Wallet URLs

Create:


wallet/urls.py


Define the URL patterns for the wallet application and connect each URL to its corresponding API view.

### Step 18: Configure Main Project URLs

Open:


config/urls.py


Configure the following URL patterns:

- Django Admin
- JWT Token Generation
- JWT Token Refresh
- OpenAPI Schema
- Swagger Documentation
- Wallet Application URLs

The wallet URLs are included under the `/wallet/` prefix.

## 4. Current API Endpoints

The following endpoints have been added to the project URL configuration.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/wallet/create/` | Create a wallet |
| GET | `/wallet/` | View wallet details |
| POST | `/wallet/topup/` | Add money to wallet |
| POST | `/wallet/withdraw/` | Withdraw money |
| POST | `/wallet/transfer/` | Transfer money |
| GET | `/wallet/statement/` | View transaction statement |
| GET | `/wallet/reconcile/` | Reconcile wallet balance |
| PATCH | `/wallet/freeze/<wallet_id>/` | Freeze or unfreeze a wallet |

### Authentication Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/token/` | Obtain JWT access and refresh tokens |
| POST | `/api/token/refresh/` | Refresh an access token |
| GET | `/api/schema/` | View OpenAPI schema |
| GET | `/api/docs/` | Open Swagger documentation |

## 5. Important Concepts Used

### REST API

REST API allows different applications to communicate using HTTP methods such as GET, POST, PUT, PATCH, and DELETE.

### JSON

JSON is the data format used to send information between the client and the server.

### JWT Authentication

JWT stands for JSON Web Token.

It is used to authenticate users when accessing protected API endpoints.

### Serializers

Serializers convert Django model objects into JSON and validate incoming request data.

### Models

Models define the database structure using Python classes.

### Foreign Key

A ForeignKey establishes a relationship between two database tables.

### OneToOneField

A OneToOneField establishes a one-to-one relationship. In this project, each user has one wallet.

### Atomic Transactions

`transaction.atomic()` ensures that a group of database operations succeeds together or rolls back if an error occurs.

### Row Locking

`select_for_update()` locks selected database rows while a transaction is running, helping prevent conflicting simultaneous updates.

### Idempotency

Idempotency prevents the same successful transfer request from being processed more than once when the same idempotency key is reused.

## 6. Remaining Development Steps

The following tasks are the next stages of development. They should be completed and verified before marking the project finished.

- [ ] Run the server and verify all endpoints in Swagger.
- [ ] Test JWT authentication.
- [ ] Test wallet creation and wallet details.
- [ ] Test top-up and withdrawal.
- [ ] Test transfers between two users.
- [ ] Test insufficient balance handling.
- [ ] Test frozen wallet restrictions.
- [ ] Test daily transfer limits.
- [ ] Test duplicate transfer requests using the same `Idempotency-Key`.
- [ ] Verify wallet reconciliation.
- [ ] Verify transaction statement date filtering and pagination.
- [ ] Implement and verify consistent API error responses.
- [ ] Write at least 8 API tests using `APITestCase`.
- [ ] Add concurrency tests using `TransactionTestCase` or threads.
- [ ] Test concurrency behaviour using MySQL.
- [ ] Prepare a Postman collection or complete Swagger documentation.
- [ ] Update this README with final installation, configuration, and testing instructions.
- [ ] Push the completed project to GitHub.

## 7. Run the Project

Activate the virtual environment:

-----
myvenv\Scripts\activate
----

Check the project:

----
python manage.py check
-----

Apply migrations:
-----
python manage.py migrate
-----

Start the development server:

----
python manage.py runserver
-----

Open Swagger documentation:


http://127.0.0.1:8000/api/docs/


Open Django Admin:


http://127.0.0.1:8000/admin/


## 8. Git and GitHub Workflow

Whenever a development milestone is completed, save and push the changes to GitHub.

Check modified files:

----
git status
---

Add the changes:
---
git add .
---

Commit the changes with a meaningful message:

----
git commit -m "Add wallet API functionality"
----

Push the changes:

-----
git push origin main
-----

Before starting work on the next development session, get the latest changes:
-----
git pull origin main
----

## 9. Expected Final Project Structure


WPS_2026/
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── wallet/
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── myvenv/
├── .env
├── .env.example
├── .gitignore
├── manage.py
└── README.md
```

The structure may expand as additional files for error handling, tests, and documentation are added.

## 10. Project Objective

The main objective of this project is to develop a secure and reliable wallet management REST API using Django REST Framework and MySQL.

The system aims to maintain accurate wallet balances, prevent duplicate transfers, handle concurrent transactions safely, and provide proper transaction records and API responses.