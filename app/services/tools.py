import csv
from datetime import datetime
from config import DATA_FILE

def log_transaction(
    date: str, 
    description: str, 
    amount: float, 
    transaction_type: str, 
    category: str, 
    account_name: str
) -> str:
    """
    REQUIRED: Call this tool when the user wants to log, save, or record a new expense or income.
    
    Args:
        date: The transaction date in 'YYYY-MM-DD' format (e.g., '2026-05-03'). 
              If the user says 'today', use the current date.
        description: A brief label of the transaction (e.g., 'Phở bò', 'Lương tháng 4').
        amount: The numerical value of the transaction. ALWAYS POSITIVE.
        transaction_type: Must be exactly 'debit' (for expenses) or 'credit' (for income).
        category: The category (e.g., 'Ăn uống', 'Di chuyển', 'Mua sắm', 'Lương').
        account_name: The payment method used (e.g., 'Tiền mặt', 'MoMo', 'TPBank'). Default to 'Tiền mặt' if not specified.
    """
    try:
        month = date[:7] 
    except:
        month = datetime.now().strftime('%Y-%m')

    try:
        with open(DATA_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([date, description, amount, transaction_type, category, account_name, month])
        
        return f"System Log: Successfully recorded {amount} for {description} ({category}) via {account_name}."
    except Exception as e:
        return f"System Error: Could not save transaction. Details: {e}"

def get_monthly_summary(month: str) -> str:
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
        return f"Database Report for {month}: Total Income = {total_income}, Total Expense = {total_expense}, Net Balance = {balance}."
    
    except FileNotFoundError:
        return "System Warning: No data found. The database is empty."

def get_category_spending(month: str, category: str) -> str:
    """
    REQUIRED: Call this tool when the user asks how much they spent on a specific category (e.g., Food, Transport) in a given month.
    
    Args:
        month: The month to query in 'YYYY-MM' format (e.g., '2026-05').
        category: The category name to search for (e.g., 'Ăn uống', 'Di chuyển').
    """
    total = 0.0
    transactions_list = []
    
    try:
        with open(DATA_FILE, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['Month'] == month and row['Category'].lower() == category.lower() and row['Transaction Type'] == 'debit':
                    total += float(row['Amount'])
                    transactions_list.append(f"{row['Description']} ({row['Amount']})")
        
        details = ", ".join(transactions_list) if transactions_list else "None"
        return f"Database Report for {month} - Category '{category}': Total Spent = {total}. Details: {details}."
        
    except FileNotFoundError:
        return "System Warning: No data found."