# 🏠 RentFlow

> **Simple property, tenant & rent management — all in one place.**

RentFlow is a lightweight desktop application for managing properties, units, tenants, rent payments, expenses, and financial reports from a single interface.

**Built by ShadowKami 🖤**

---

## ✨ Features

### 🏢 Property Management

- Add and manage multiple properties
- Store property addresses and notes
- Manage multiple units within each property
- Track unit number/name and type
- Set default monthly rent
- Track rent changes over time

### 👤 Tenant Management

- Add and manage tenants
- Store phone and email
- Assign tenants to properties and units
- Track lease start and end dates
- Track security deposits
- Manage active and moved-out tenants
- Search tenant records

### 💰 Rent Management

- Generate monthly rent records
- Track rent amount due
- Record payments
- Calculate outstanding balances
- Track payment status
- Record payment dates
- Record payment methods
- Add payment notes
- Mark multiple months as paid
- Track overdue rent

### 📊 Dashboard

View important information at a glance:

- Total rent due
- Total collected
- Pending rent
- Overdue tenants
- Property occupancy
- Monthly rent status

### 🧾 Expense Management

Track property expenses such as:

- Maintenance
- Repairs
- Property Tax
- Insurance
- Utilities
- Cleaning
- Legal/Admin
- Other

Expenses can be linked to a specific property or recorded as general expenses.

### 📈 Reports

View yearly rental information including:

- Monthly collection
- Total amount due
- Total amount collected
- Pending balances
- Collection rate
- Tenant-wise yearly summary
- Total expenses
- Net income

### 📤 CSV Export

Export:

- Rent records
- Payments
- Tenants
- Tenant yearly summaries

### 🌙 Light & Dark Mode

Switch between light and dark themes depending on your preference.

---

## 🖥️ Application Structure

                    🏠 RentFlow
                         │
          ┌──────────────┼──────────────┐
          │              │              │
      Properties      Tenants         Rent
          │              │              │
        Units         Leases         Payments
          │              │              │
    Rent Periods       Deposit       Balances
          │                             │
          └──────────────┬──────────────┘
                         │
                    📊 Reports
                         │
                    🧾 Expenses

---

## 🛠️ Tech Stack

    Python
    ├── Tkinter / ttk
    ├── SQLite
    ├── CSV
    └── JSON

RentFlow uses a local SQLite database, so it can operate without an online service or cloud account.

---

## 🔒 Local & Private

RentFlow is designed to work locally.

Your:

- Tenant information
- Property information
- Rent records
- Payment records
- Expenses

are stored on your computer.

> **Never share your database or exported files publicly if they contain personal or financial information.**

---

## 🚀 Installation

### Requirements

- Python 3.x
- Tkinter

The project currently uses Python's standard library and does not require external pip packages.

### Clone

    git clone https://github.com/ShadowKami/RentFlow.git
    cd RentFlow

### Run

    python main.py

---

## 🪟 Windows

Don't want to install Python?

Download the latest Windows executable from:

### [📥 Download RentFlow](https://github.com/ShadowKamiDev/RentFlow/releases/)

Download → Run → Start managing your properties.

---

## 📁 Project Structure

    RentFlow/
    │
    ├── main.py
    ├── db.py
    ├── widgets.py
    │
    ├── tabs_dashboard.py
    ├── tabs_properties.py
    ├── tabs_tenants.py
    ├── tabs_rent.py
    ├── tabs_expenses.py
    ├── tabs_reports.py
    │
    ├── icon.png
    ├── icon.ico
    ├── requirements.txt
    └── README.md

---

## 💾 Data Structure

    Properties
        │
        └── Units
              │
              ├── Rent Periods
              │
              └── Tenants
                    │
                    └── Rent Records
                          │
                          └── Payments

    Properties
        │
        └── Expenses

Rent periods allow different rent amounts to be tracked over different time periods.

---

## 💳 Payment Methods

RentFlow supports:

- Cash
- Bank Transfer
- UPI
- Cheque
- Card
- Other

---

## 📊 Example Workflow

    1. Add Property
           ↓
    2. Add Units
           ↓
    3. Set Monthly Rent
           ↓
    4. Add Tenant
           ↓
    5. Assign Tenant → Unit
           ↓
    6. Generate Monthly Rent
           ↓
    7. Record Payment
           ↓
    8. Track Balance
           ↓
    9. Review Reports
           ↓
    10. Export CSV

---

## 🔮 Roadmap

- [ ] PDF rent receipts
- [ ] Automated rent reminders
- [ ] WhatsApp / email reminders
- [ ] Advanced analytics
- [ ] Property-wise dashboards
- [ ] Tenant document management
- [ ] Scheduled backups
- [ ] Multi-user support
- [ ] Cloud synchronization

---

## ☕ Support ShadowKami

If RentFlow helps you manage your properties and saves you time, consider supporting its development.

### ☕ Support ShadowKami

If you find RentFlow useful and want to support future development:

### [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support%20ShadowKami-yellow?style=for-the-badge&logo=buymeacoffee&logoColor=black)](https://buymeacoffee.com/uroshan)

Your support helps **ShadowKami** build and release more useful applications.

---

    $ python main.py

    > initializing RentFlow...
    > loading database...
    > loading properties...
    > loading tenants...
    > loading rent records...
    > system ready.

    ────────────────────────────────────────────

            MANAGE • TRACK • GROW

                     ShadowKami 🖤

    ────────────────────────────────────────────

<p align="center">
  <b>RentFlow</b> · Property & Rent Management
  <br>
  <sub>Useful software. Built by ShadowKami.</sub>
</p>
