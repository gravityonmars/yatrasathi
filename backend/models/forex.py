import requests

def get_forex(from_currency: str, to_currency: str, amount: float) -> dict:
    """Convert an amount and retrieve recent exchange rate history for a currency pair.

    Args:
        from_currency (str): 3-letter ISO code of the currency to convert from (e.g., "USD").
        to_currency (str): 3-letter ISO code of the currency to convert to (e.g., "EUR").
        amount (float, optional): Value to convert. Defaults to 1.0.

    Returns:
        dict: Conversion result with the current rate, converted amount, and 5-day rate history.
    """
    url = (
        f"https://open.er-api.com/v6/latest/{from_currency}"
    )

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return {"error": f"Failed to retrieve currency data: {str(e)}"}

    if "rates" not in data or to_currency not in data["rates"]:
        return f"Error: Unable to fetch exchange rate for {from_currency} to {to_currency}."

    converted_amount = data["rates"][to_currency] * amount
    rate_per_unit = converted_amount / amount if amount > 0 else 0


    result = [
        {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "amount": amount,
            "converted_amount": converted_amount,
            "rate_per_unit": rate_per_unit
        }
    ]

    return {
        "result": result,
    }

print(get_forex("USD", "NPR", 1.0))