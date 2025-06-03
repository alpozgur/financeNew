# utils.py

import re

def normalize_turkish_text(text):
    replacements = {
        'İ': 'i', 'ı': 'i', 'I': 'i',
        'Ğ': 'g', 'ğ': 'g',
        'Ü': 'u', 'ü': 'u', 
        'Ş': 's', 'ş': 's',
        'Ö': 'o', 'ö': 'o',
        'Ç': 'c', 'ç': 'c'
    }
    normalized = text.lower()
    for turkish_char, replacement in replacements.items():
        normalized = normalized.replace(turkish_char.lower(), replacement)
        normalized = normalized.replace(turkish_char.upper(), replacement)
    return normalized

def extract_company_from_fund_name(fund_name):
    patterns = [
        r"^(.*?)\s+PORTFÖY",
        r"^(.*?)\s+ASSET MANAGEMENT",
        r"^(.*?)\s+PORTFOLIO",
        r"^(.*?)\s+FUND",
    ]
    for pattern in patterns:
        m = re.match(pattern, fund_name, re.IGNORECASE)
        if m:
            return m.group(1).strip().upper()
    return " ".join(fund_name.split()[:2]).upper()
