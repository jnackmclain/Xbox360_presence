import requests
from pypresence import Presence
import time
from datetime import datetime, timedelta
import sys

client_id = 'YOUR_CLIENT_ID_HERE'
RPC = Presence(client_id)  # Standard Presence for synchronous use

# Fetch the JSON data
def fetch_game_names():
    # shout out albertofustinoni for the original, i just had some formatting updates for gh/rb
    url = "https://gist.githubusercontent.com/jnackmclain/be1495767a2536b8f455fc7e293255c8/raw/950174f1e1eceda361a8dd3047883f8d890c7084/Xbox360TitleIDs.json"
    response = requests.get(url)
    return {game['TitleID']: game['Title'] for game in response.json()}

game_names = fetch_game_names()

def fetch_title_id(ip_address):
    url = f"http://{ip_address}:9999/title"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to connect to the Xbox at {url}")
        return None
    
    data = response.json()
    title_id = data.get('titleid', None)
    
    if not title_id:
        print("TitleId not found in the response")
        return None
    
    if title_id.startswith("0x"):
        title_id = title_id[2:]  # Remove '0x' prefix
    
    return title_id

def get_elapsed_time(start_time):
    elapsed = datetime.now() - start_time
    days, remainder = divmod(elapsed.total_seconds(), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    
    if days > 0:
        return f"for {int(days)} day{'s' if days > 1 else ''}, {int(hours)} hour{'s' if hours != 1 else ''}, and {int(minutes)} minute{'s' if minutes != 1 else ''}"
    elif hours > 0:
        return f"for {int(hours)} hour{'s' if hours != 1 else ''} and {int(minutes)} minute{'s' if minutes != 1 else ''}"
    else:
        return f"for {int(minutes)} minute{'s' if minutes != 1 else ''}"

def set_game(ip_address, start_time, last_title_id):
    title_id = fetch_title_id(ip_address)
    
    if not title_id:
        return start_time, last_title_id

    if title_id == '00000000':
        game_name = "Aurora"
        image_url = "http://xboxunity.net/Resources/Lib/Icon.php?tid=00000166"
    else:
        game_name = game_names.get(title_id.upper(), f"Unknown Title ID: {title_id}")
        image_url = f"http://www.xboxunity.net/Resources/Lib/Icon.php?tid={title_id}"
    
        # Check if the image exists
        response = requests.get(image_url)
        if response.status_code != 200:
            image_url = "https://gentle-drum.flywheelsites.com/wp-content/uploads/2013/01/xbox-logo-square-web.jpg"
    
    # Reset start_time if a new game is detected
    if title_id != last_title_id:
        start_time = datetime.now()
        last_title_id = title_id

    elapsed_time = get_elapsed_time(start_time)
    RPC.update(
        state=f"{elapsed_time.capitalize()}",
        details=f"Playing {game_name}",
        large_image=image_url,
        large_text=game_name
    )
    print(f"Displaying game '{game_name}' with Title ID: {title_id} and image from {image_url}. {elapsed_time.capitalize()}.")
    
    return start_time, last_title_id

def main():
    RPC.connect()

    # Allow IP to be given as an argument
    if len(sys.argv) > 1:
        ip_address = sys.argv[1]
    else:
        ip_address = input("Enter the IP address of your Xbox (Ensure Nova Web UI is running): ")
    
    start_time = datetime.now()
    last_title_id = None
    
    try:
        while True:
            start_time, last_title_id = set_game(ip_address, start_time, last_title_id)
            time.sleep(15)  # Update every 15 seconds
    except KeyboardInterrupt:
        print("Disconnecting from Discord...")
        RPC.clear()
        RPC.close()
        print("Disconnected. Goodbye!")

if __name__ == "__main__":
    main()
