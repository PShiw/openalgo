import os
import secrets
import re
import sys

def generate_key():
    return secrets.token_hex(32)

def update_env():
    # Get params from environment
    replacements = {
        'BROKER_API_KEY': os.environ.get('BROKER_API_KEY', ''),
        'BROKER_API_SECRET': os.environ.get('BROKER_API_SECRET', ''),
        'APP_KEY': os.environ.get('APP_KEY', '') or generate_key(),
        'API_KEY_PEPPER': os.environ.get('API_KEY_PEPPER', '') or generate_key(),
        'HOST_SERVER': os.environ.get('HOST_SERVER', 'http://127.0.0.1:5000'),
        'FLASK_PORT': os.environ.get('FLASK_PORT', '5000'),
        'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO')
    }

    env_file = '.env'
    if not os.path.exists(env_file):
        print(f"Error: {env_file} not found.")
        sys.exit(1)

    # Read .env file
    with open(env_file, 'r') as f:
        content = f.read()

    # Perform replacements
    for key, value in replacements.items():
        # Escape single quotes for the file content
        safe_value = value.replace("'", "\\'")
        
        # Regex to match KEY = 'VALUE' or KEY='VALUE'
        regex = r'^' + key + r'\s*=\s*[\'"][^\'"]*[\'"]'
        replacement = f"{key} = '{safe_value}'"
        
        if re.search(regex, content, re.MULTILINE):
            content = re.sub(regex, replacement, content, flags=re.MULTILINE)
        else:
            content += f'\n{replacement}'

    with open(env_file, 'w') as f:
        f.write(content)
    
    print("Successfully updated .env file with environment variables.")

if __name__ == "__main__":
    update_env()