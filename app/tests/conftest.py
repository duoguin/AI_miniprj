import sys
import os
import csv
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def temp_csv(tmp_path):
    """Empty CSV with proper headers."""
    f = tmp_path / "transactions.csv"
    f.write_text(
        "Date,Description,Amount,Transaction Type,Category,Account Name,Month\n",
        encoding="utf-8",
    )
    return str(f)


@pytest.fixture
def temp_csv_with_data(tmp_path):
    """CSV pre-populated with realistic test transactions."""
    f = tmp_path / "transactions.csv"
    rows = [
        ["Date", "Description", "Amount", "Transaction Type", "Category", "Account Name", "Month"],
        ["2026-05-01", "Phở bò", "50000", "debit", "Ăn uống", "Tiền mặt", "2026-05"],
        ["2026-05-02", "Grab Bike", "25000", "debit", "Di chuyển", "MoMo", "2026-05"],
        ["2026-05-03", "Lương tháng 5", "15000000", "credit", "Lương", "TPBank", "2026-05"],
        ["2026-05-04", "Cà phê Highland", "65000", "debit", "Ăn uống", "Tiền mặt", "2026-05"],
        ["2026-05-05", "Áo thun", "250000", "debit", "Mua sắm", "Tiền mặt", "2026-05"],
        ["2026-05-06", "Tiền điện", "450000", "debit", "Hóa đơn", "TPBank", "2026-05"],
        ["2026-05-07", "Netflix", "99000", "debit", "Giải trí", "TPBank", "2026-05"],
        ["2026-05-08", "Bún bò Huế", "45000", "debit", "Ăn uống", "Tiền mặt", "2026-05"],
        ["2026-05-09", "Xăng xe", "120000", "debit", "Di chuyển", "Tiền mặt", "2026-05"],
        ["2026-05-10", "Thuốc tháng 5", "85000", "debit", "Sức khỏe", "Tiền mặt", "2026-05"],
        ["2026-04-01", "Phở gà", "45000", "debit", "Ăn uống", "Tiền mặt", "2026-04"],
        ["2026-04-05", "Lương tháng 4", "15000000", "credit", "Lương", "TPBank", "2026-04"],
        ["2026-04-10", "Siêu thị", "380000", "debit", "Mua sắm", "TPBank", "2026-04"],
    ]
    with open(str(f), "w", newline="", encoding="utf-8") as fp:
        csv.writer(fp).writerows(rows)
    return str(f)
