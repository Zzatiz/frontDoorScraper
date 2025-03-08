import pandas as pd
import requests
import os
import math

# 🔑 Replace with your actual Google API Key (must enable Geocoding, Street View, and Roads APIs)
GOOGLE_API_KEY = ""

# 📍 Function to get latitude & longitude from an address
def get_lat_lon(address):
    formatted_address = address.replace(" ", "+").strip()
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={formatted_address}&key={GOOGLE_API_KEY}"
    
    response = requests.get(url).json()
    
    if response["status"] == "OK" and response["results"]:
        location = response["results"][0]["geometry"]["location"]
        print(f"[SUCCESS] Found location for {address}: {location}")
        return location["lat"], location["lng"]
    else:
        print(f"[ERROR] Could not find location for {address}. Response: {response}")
        return None, None

# 🚗 Function to get the nearest road to the house
def get_nearest_road(lat, lon):
    url = f"https://roads.googleapis.com/v1/nearestRoads?points={lat},{lon}&key={GOOGLE_API_KEY}"
    
    response = requests.get(url).json()
    
    if "snappedPoints" in response:
        road_point = response["snappedPoints"][0]["location"]
        print(f"[SUCCESS] Found nearest road: {road_point}")
        return road_point["latitude"], road_point["longitude"]
    else:
        print(f"[ERROR] No road found near {lat}, {lon}. Response: {response}")
        return None, None

# 📐 Function to calculate the heading (angle) from road to house
def calculate_heading(lat1, lon1, lat2, lon2):
    delta_lon = lon2 - lon1
    y = math.sin(math.radians(delta_lon)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(delta_lon))
    heading = math.degrees(math.atan2(y, x))
    return (heading + 360) % 360  # Normalize angle

# 🏡 Function to fetch **FRONT-FACING** Street View images
def get_street_view(lat, lon, heading, save_path):
    fov = 80  # Field of view (adjust zoom)
    pitch = 0  # Keep the camera level
    radius = 50  # Search for a better view within 50 meters

    streetview_url = f"https://maps.googleapis.com/maps/api/streetview?size=600x400&location={lat},{lon}&heading={heading}&fov={fov}&pitch={pitch}&radius={radius}&key={GOOGLE_API_KEY}"
    
    response = requests.get(streetview_url)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
        print(f"[SUCCESS] Image saved: {save_path}")
        return save_path
    else:
        print(f"[ERROR] Failed to download image for {lat}, {lon}")
        return None

# 📂 Load CSV file
input_csv = "addresses.csv"
df = pd.read_csv(input_csv)

# 🔄 Ensure output directory exists
output_dir = "street_view_images"
os.makedirs(output_dir, exist_ok=True)

# 🔍 Process each address
image_paths = []
for index, row in df.iterrows():
    if "Address" in df.columns:
        address = row["Address"]
    else:
        city = row.get("City", "")
        state = row.get("State", "")
        zip_code = row.get("Zip", "")
        address = f"{city}, {state} {zip_code}".strip()

    lat, lon = get_lat_lon(address)

    if lat and lon:
        road_lat, road_lon = get_nearest_road(lat, lon)

        if road_lat and road_lon:
            heading = calculate_heading(road_lat, road_lon, lat, lon)  # From road to house
            print(f"[INFO] Calculated heading: {heading}")

            image_path = os.path.join(output_dir, f"{index}.jpg")
            saved_image = get_street_view(road_lat, road_lon, heading, image_path)
            image_paths.append(saved_image)
        else:
            print(f"[WARNING] No nearby road found for {address}. Skipping image download.")
            image_paths.append(None)
    else:
        image_paths.append(None)

# 📝 Add image path to CSV
df["Street_View_Image"] = image_paths
output_csv = "addresses_with_images.csv"
df.to_csv(output_csv, index=False)

print(f"✅ Processing complete. Updated CSV saved as {output_csv}")
