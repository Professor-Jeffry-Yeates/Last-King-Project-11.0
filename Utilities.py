__version__ = "11.0"
""" Varoius utility functions"""

def setDictionaryValueAsBoolean(dictionary, key, defaultValue=True):
    # Insure a dictionary value is boolean, even if a string value is provided
    dictionary.setdefault(key, defaultValue)
    currentValue = dictionary[key]
    if type(currentValue) == str:
        booleanValue = currentValue.lower() == "true"
        dictionary[key] = booleanValue