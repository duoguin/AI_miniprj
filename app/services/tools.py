import csv
from datetime import datetime
from config import DATA_FILE, BUDGET_FILE


def logTransaction(
    date: str,
    description: str,
    amount: float,
    transaction_type: str,
    category: str,
    account_name: str,
) -> str:
    """
    REQUIRED: Call this tool when the user wants to log, save, or record a new expense or income.

    Args:
        date: The transaction date in 'YYYY-MM-DD' format (e.g., '2026-05-10').
              If the user says 'today', use the current date.
        description: A brief label of the transaction (e.g., 'Lunch', 'May Paycheck').
        amount: The numerical value of the transaction in USD. ALWAYS POSITIVE.
        transaction_type: Must be exactly 'debit' (for expenses) or 'credit' (for income).
        category: One of [Food & Dining, Transportation, Shopping, Bills & Utilities,
                  Income, Entertainment, Health, Other].
        account_name: The payment method used (e.g., 'Cash', 'Credit Card', 'Bank'). Default to 'Cash' if not specified.
    """
    try:
        month = date[:7]
    except Exception:
        month = datetime.now().strftime('%Y-%m')

    try:
        with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([date, description, amount, transaction_type, category, account_name, month])
        return f"System Log: Successfully recorded ${amount} for '{description}' ({category}) via {account_name}."
    except Exception as e:
        return f"System Error: Could not save transaction. Details: {e}"


def getMonthlySummary(month: str) -> str:
    """
    REQUIRED: Call this tool when the user asks for their total spending, total income, or balance for a specific month.

    Args:
        month: The month to query in 'YYYY-MM' format (e.g., '2026-05').
    """
    total_expense = 0.0
    total_income = 0.0

    try:
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Month'] == month:
                    if row['Transaction Type'] == 'debit':
                        total_expense += float(row['Amount'])
                    elif row['Transaction Type'] == 'credit':
                        total_income += float(row['Amount'])

        balance = total_income - total_expense
        return (
            f"Database Report for {month}: "
            f"Total Income = {total_income}, "
            f"Total Expense = {total_expense}, "
            f"Net Balance = {balance}."
        )
    except FileNotFoundError:
        return "System Warning: No data found. The database is empty."


def getCategorySpending(month: str, category: str) -> str:
    """
    REQUIRED: Call this tool when the user asks how much they spent on a specific category in a given month.

    Args:
        month: The month to query in 'YYYY-MM' format (e.g., '2026-05').
        category: The category name (e.g., 'Food & Dining', 'Transportation', 'Shopping').
    """
    total = 0.0
    transactions_list = []
    matched_category = category

    try:
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if (
                    row['Month'] == month
                    and row['Category'].lower() == category.lower()
                    and row['Transaction Type'] == 'debit'
                ):
                    total += float(row['Amount'])
                    matched_category = row['Category']
                    transactions_list.append(f"{row['Description']} (${row['Amount']})")

        details = ", ".join(transactions_list) if transactions_list else "None"
        return (
            f"Database Report for {month} - Category '{matched_category}': "
            f"Total Spent = {total}. Details: {details}."
        )
    except FileNotFoundError:
        return "System Warning: No data found."


def setCategoryBudget(category: str, amount: float, month: str = None) -> str:
    """
    REQUIRED: Gọi tool này khi người dùng muốn đặt hoặc cập nhật ngân sách cho một danh mục.

    Args:
        category: Tên danh mục (ví dụ: 'Food & Dining', 'Transportation').
        amount: Số tiền ngân sách bằng USD (luôn dương).
        month: Tháng theo định dạng 'YYYY-MM'. Mặc định là tháng hiện tại nếu không cung cấp.
    """
    if not month:
        month = datetime.now().strftime('%Y-%m')

    rows = []
    updated = False

    try:
        with open(BUDGET_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Category'].lower() == category.lower() and row['Month'] == month:
                    row['Amount'] = amount
                    updated = True
                rows.append(row)
    except FileNotFoundError:
        rows = []

    if not updated:
        rows.append({'Category': category, 'Amount': amount, 'Month': month})

    try:
        with open(BUDGET_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Category', 'Amount', 'Month'])
            writer.writeheader()
            writer.writerows(rows)
        action = "Cập nhật" if updated else "Đặt mới"
        return f"System Log: {action} ngân sách '{category}' = ${amount} cho tháng {month}."
    except Exception as e:
        return f"System Error: Không thể lưu ngân sách. Chi tiết: {e}"


def getBudgetStatus(month: str = None) -> str:
    """
    REQUIRED: Gọi tool này khi người dùng muốn xem tình trạng ngân sách tháng
    (đã chi bao nhiêu so với ngân sách đặt ra).

    Args:
        month: Tháng theo định dạng 'YYYY-MM'. Mặc định là tháng hiện tại nếu không cung cấp.
    """
    if not month:
        month = datetime.now().strftime('%Y-%m')

    # Đọc ngân sách từ budgets.csv
    budgets = {}
    try:
        with open(BUDGET_FILE, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row['Month'] == month:
                    budgets[row['Category'].lower()] = {
                        'name': row['Category'],
                        'budget': float(row['Amount']),
                    }
    except FileNotFoundError:
        return "System Warning: Chưa có dữ liệu ngân sách."

    if not budgets:
        return f"System Warning: Chưa đặt ngân sách cho tháng {month}."

    # Đọc chi tiêu thực tế từ personal_transactions.csv
    spending = {}
    try:
        with open(DATA_FILE, mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                if row['Month'] == month and row['Transaction Type'] == 'debit':
                    key = row['Category'].lower()
                    spending[key] = spending.get(key, 0.0) + float(row['Amount'])
    except FileNotFoundError:
        pass

    # Tổng hợp báo cáo
    lines = [f"Budget Status for {month}:"]
    for key, info in budgets.items():
        spent = round(spending.get(key, 0.0), 2)
        budget = info['budget']
        percent = round((spent / budget * 100) if budget > 0 else 0, 1)
        status = "⚠ OVER" if spent > budget else ("⚡ WARNING" if percent >= 80 else "✓ OK")
        lines.append(
            f"  {info['name']}: spent ${spent} / budget ${budget} ({percent}%) {status}"
        )

    return "\n".join(lines)
