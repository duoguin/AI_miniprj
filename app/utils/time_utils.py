from datetime import datetime, timedelta

def getCurrentDateTime() -> str:
    """
    Returns current datetime in ISO format.
    """
    return datetime.now().isoformat()

def getCurrentDate() -> str:
    """
    Returns current date in YYYY-MM-DD format.
    """
    return datetime.now().strftime('%Y-%m-%d')

def getCurrentMonth() -> str:
    """
    Returns current month in YYYY-MM format.
    """
    return datetime.now().strftime('%Y-%m')

def normalizeDate(date: str) -> str:
    """
    Normalize common natural language dates.
    """
    today = datetime.now()

    if not date:
        return today.strftime('%Y-%m-%d')

    date = date.lower().strip()

    if date in ["today", "hôm nay"]:
        return today.strftime('%Y-%m-%d')
    elif date in ["yesterday", "hôm qua"]:
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')

    # fallback: assume already correct
    return date

def extractMonthFromDate(date: str) -> str:
    return date[:7]