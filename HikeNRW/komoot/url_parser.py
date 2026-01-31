import re


def extract_komoot_id(text):
    # Define the regular expression pattern for 9 to 11 digit numbers
    pattern = r"\b\d{9,11}\b"
    # Find all matches in the text
    matches = re.findall(pattern, text)
    if len(matches) == 0:
        raise ValueError("There is no Komoot ID in the string")
    elif len(matches) > 1:
        raise ValueError("Multiple Komoot ID got detected")
    return matches[0]
