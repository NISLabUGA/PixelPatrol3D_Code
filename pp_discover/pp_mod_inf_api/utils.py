import re
import datetime
import string
import random

def generate_random_string(length):
    # Define the characters to choose from (letters and digits)
    characters = string.ascii_letters + string.digits
    # Generate a random string
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def get_current_timestamp():
    # Get the current time
    now = datetime.datetime.now()
    # Format the time as YYYYMMDD.HH.MM
    formatted_timestamp = now.strftime("%Y%m%d.%H.%M")
    return formatted_timestamp

def sterilize_url(url):
    # Replace invalid characters with an underscore
    sanitized = re.sub(r'[\/:*?"<>|]', '_', url)
    
    # Optionally, truncate if the file name is too long (255 character limit)
    return sanitized[:255]