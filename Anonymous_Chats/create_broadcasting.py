import random
import string
import logging
import hashlib

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_random_alphanumeric(length):
    """
    Generate a random alphanumeric string of specified length.
    
    Args:
        length: The length of the random string to generate
        
    Returns:
        A random alphanumeric string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def create_broadcasting_channel_id(user_id, anony_name):
    """
    Generate a broadcasting channel ID for a broadcaster.
    
    Format: [/]BCST:[5digits_RANDOM_NO(including alphabet)][USER_ID][3digits_RANDOM_NO(including alphabet)][ANONY_NAME][4digits_RANDOM_NO(including alphabet)]
    
    Args:
        user_id: The user's ID
        anony_name: The user's anonymous name
        
    Returns:
        A formatted broadcasting channel ID string
    """
    try:
        # Generate random parts
        random_part1 = generate_random_alphanumeric(2).upper()
        random_part2 = generate_random_alphanumeric(3).upper()
        random_part3 = generate_random_alphanumeric(4).upper()
        
        # Create the broadcasting channel ID
        channel_id = f"/BCST{random_part1}{user_id}{random_part2}{anony_name}{random_part3}"
        logger.info(f"Generated broadcasting channel ID: {channel_id}")
        return channel_id
    except Exception as e:
        logger.error(f"Error generating broadcasting channel ID: {e}")
        return None

def validate_listener_channel_id(channel_id):
    """
    Validate that a listener's input channel ID starts with "/BCST"
    
    Args:
        channel_id: The channel ID to validate
        
    Returns:
        Boolean indicating if the channel ID is valid
    """
    if not channel_id:
        return False
    
    return channel_id.strip().startswith("/BCST")

def extract_broadcaster_id(channel_id):
    """
    Extract the broadcaster ID from a broadcasting channel ID.
    
    Format: /BCST:[5digits_RANDOM_NO][USER_ID][3digits_RANDOM_NO][ANONY_NAME][4digits_RANDOM_NO]
    
    Args:
        channel_id: The broadcasting channel ID
        
    Returns:
        The extracted broadcaster ID or None if not found
    """
    try:
        # Check if the channel ID starts with /BCST
        if not channel_id.startswith("/BCST"):
            return None
        
        # Use a regular expression to extract the user ID
        import re
        
        # Pattern to match: 5 chars, then digits (user ID), then the rest
        # The user ID is the first group of consecutive digits after the first 5 characters
        match = re.search(r'/BCST:.{5}(\d+)', channel_id)
        
        if match:
            user_id = match.group(1)
            logger.info(f"Extracted user ID from channel ID: {channel_id} -> {user_id}")
            return user_id
        
        # If the regex approach fails, try a simpler approach
        # Skip the "/BCST:" prefix and the first 5 random characters
        if len(channel_id) > 11:  # "/BCST:" (6 chars) + 5 random chars
            content = channel_id[11:]
            
            # Find the first sequence of digits
            digit_sequence = ""
            for char in content:
                if char.isdigit():
                    digit_sequence += char
                elif digit_sequence:  # If we've already started collecting digits and hit a non-digit
                    break
            
            if digit_sequence:
                logger.info(f"Extracted user ID from channel ID (alternate method): {channel_id} -> {digit_sequence}")
                return digit_sequence
        
        logger.error(f"Could not extract user ID from channel ID: {channel_id}")
        return None
    except Exception as e:
        logger.error(f"Error extracting broadcaster ID: {e}")
        return None

def convert_to_fixed_code(channel_id):
    """
    Convert a broadcasting channel ID to a fixed 6-digit alphanumeric code.
    The same input will always generate the same output.
    
    Args:
        channel_id: The broadcasting channel ID to convert
        
    Returns:
        A fixed 6-digit alphanumeric code
    """
    try:
        # Extract the broadcaster ID from the channel ID
        broadcaster_id = extract_broadcaster_id(channel_id)
        
        if not broadcaster_id:
            logger.error(f"Could not extract broadcaster ID from channel ID: {channel_id}")
            # Fallback to using the whole channel ID
            hash_input = channel_id
        else:
            # Use the broadcaster ID as the hash input to ensure consistency
            hash_input = broadcaster_id
        
        # Create a hash of the broadcaster ID
        hash_object = hashlib.md5(hash_input.encode())
        hash_hex = hash_object.hexdigest()
        
        # Take the first 6 characters of the hash and ensure they're alphanumeric
        # Convert any non-alphanumeric characters to alphanumeric
        code = ""
        for i in range(6):
            char = hash_hex[i]
            if not char.isalnum():
                # Convert to a letter based on its ASCII value
                code += chr(97 + (ord(char) % 26))  # Convert to lowercase letter
            else:
                code += char
        
        logger.info(f"Converted channel ID to fixed code: {channel_id} -> {code} (using broadcaster ID: {broadcaster_id})")
        return code
    except Exception as e:
        logger.error(f"Error converting channel ID to fixed code: {e}")
        return None

def handle_broadcasting_option(bot, user_id, option, anony_name=None, channel_id=None):
    """
    Handle broadcasting options (Listener or Broadcaster)
    
    Args:
        bot: The Telegram bot instance
        user_id: The user's ID
        option: The selected option ('listener' or 'broadcaster')
        anony_name: The user's anonymous name (required for broadcaster)
        channel_id: The channel ID (for listener validation)
        
    Returns:
        Response message or None on error
    """
    try:
        if option.lower() == 'broadcaster':
            if not anony_name:
                return "Error: Anonymous name is required for broadcasting."
            
            # Generate broadcasting channel ID
            channel_id = create_broadcasting_channel_id(user_id, anony_name)
            
            if not channel_id:
                return "Error generating broadcasting channel ID. Please try again."
            
            # Convert to fixed 6-digit code
            fixed_code = convert_to_fixed_code(channel_id)
            
            if not fixed_code:
                return "Error generating fixed code. Please try again."
            
            return f"Your broadcasting channel ID is unique and can be shared publicly.\n\nShare this code with your listeners."
            
        elif option.lower() == 'listener':
            if channel_id:
                # Validate the channel ID
                if validate_listener_channel_id(channel_id):
                    # Convert to fixed 6-digit code
                    fixed_code = convert_to_fixed_code(channel_id)
                    
                    if not fixed_code:
                        return "Error generating fixed code. Please try again."
                    
                    # Here you would implement the logic to connect to the broadcaster
                    return f"Successfully connected to broadcasting channel: {channel_id}"
                else:
                    return "Invalid broadcasting channel ID. It must start with '/BCST'."
            else:
                return "Please enter the broadcasting channel ID starting with '/BCST'."
        else:
            return "Invalid option. Please select either 'Listener' or 'Broadcaster'."
    except Exception as e:
        logger.error(f"Error handling broadcasting option: {e}")
        return "An error occurred. Please try again later."