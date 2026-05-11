import sys
import os
import csv
import pytest
from dotenv import load_dotenv

# Load .env trước khi các test file import và đọc os.getenv("API_KEY")
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_csv(tmp_path):
    """File CSV rỗng với header chuẩn."""
    f = tmp_path / "transactions.csv"
    f.write_text(
        "Date,Description,Amount,Transaction Type,Category,Account Name,Month\n",
        encoding="utf-8",
    )
    return str(f)


@pytest.fixture
def temp_csv_with_data(tmp_path):
    """File CSV có sẵn dữ liệu giao dịch mẫu theo USD."""
    f = tmp_path / "transactions.csv"
    rows = [
        ["Date", "Description", "Amount", "Transaction Type", "Category", "Account Name", "Month"],
        ["2026-05-01", "Restaurant - Pho",   "12.50",   "debit",  "Food & Dining",     "Cash",   "2026-05"],
        ["2026-05-02", "Uber",               "8.00",    "debit",  "Transportation",    "Card",   "2026-05"],
        ["2026-05-03", "Paycheck May",       "3000.00", "credit", "Income",            "Bank",   "2026-05"],
        ["2026-05-04", "Coffee",             "5.50",    "debit",  "Food & Dining",     "Cash",   "2026-05"],
        ["2026-05-05", "T-shirt",            "25.00",   "debit",  "Shopping",          "Cash",   "2026-05"],
        ["2026-05-06", "Electric bill",      "90.00",   "debit",  "Bills & Utilities", "Bank",   "2026-05"],
        ["2026-05-07", "Netflix",            "15.99",   "debit",  "Entertainment",     "Bank",   "2026-05"],
        ["2026-05-08", "Burger",             "11.00",   "debit",  "Food & Dining",     "Cash",   "2026-05"],
        ["2026-05-09", "Gas",                "45.00",   "debit",  "Transportation",    "Cash",   "2026-05"],
        ["2026-05-10", "Medicine",           "22.00",   "debit",  "Health",            "Cash",   "2026-05"],
        ["2026-04-01", "Sandwich",           "8.50",    "debit",  "Food & Dining",     "Cash",   "2026-04"],
        ["2026-04-05", "Paycheck Apr",       "3000.00", "credit", "Income",            "Bank",   "2026-04"],
        ["2026-04-10", "Grocery",            "65.00",   "debit",  "Shopping",          "Bank",   "2026-04"],
    ]
    with open(str(f), "w", newline="", encoding="utf-8") as fp:
        csv.writer(fp).writerows(rows)
    return str(f)
