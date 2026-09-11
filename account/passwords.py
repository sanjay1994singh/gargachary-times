def get_mobile_password(mobile):
    """Use the same national mobile digits as the existing reset command."""
    digits = ''.join(char for char in (mobile or '') if char.isdigit())
    return digits[-10:]
