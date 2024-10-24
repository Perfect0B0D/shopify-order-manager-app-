import re
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SHOPIFY_STORE_URL = os.getenv("SHOPIFY_STORE_URL")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Shopify API headers
HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}

def get_unfulfilled_orders():
    url = f"{SHOPIFY_STORE_URL}/admin/api/2023-04/orders.json?fulfillment_status=unfulfilled"
    
    try:
        
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for any 4xx or 5xx response codes

        orders = response.json().get("orders", [])
        if orders:
            print(f"Fetched {len(orders)} unfulfilled orders.")
        else:
            print("No unfulfilled orders found.")
        return orders
    except requests.exceptions.RequestException as e:
        print(f"Error fetching unfulfilled orders: {e}")
        return []

def create_order_folder(base_dir, order_id):
    order_folder = os.path.join(base_dir, f"#{order_id}")
    
    if not os.path.exists(order_folder):
        os.makedirs(order_folder, exist_ok=True)
        print(f"Folder created: {order_folder}")
        return order_folder, True
    else:
        print(f"Order folder already exists: {order_folder}")
        return order_folder, False

def create_item_subfolder(order_folder, item_name):
    safe_item_name = sanitize_folder_name(item_name)
    item_folder = os.path.join(order_folder, safe_item_name)
    
    if not os.path.exists(item_folder):
        os.makedirs(item_folder, exist_ok=True)
        print(f"Subfolder created: {item_folder}")
    else:
        print(f"Item subfolder already exists: {item_folder}")
    return item_folder

def sanitize_folder_name(name):
    return name.replace("/", "-").replace("\\", "-").strip()

def download_image(image_url, folder, filename=None):
    if filename is None:
        # Sanitize the URL to remove invalid characters (like ? and &)
        filename = re.sub(r'[<>:"/\\|?*]', '', image_url.split("/")[-1])
    
    # Define the full path where the image will be saved
    file_path = os.path.join(folder, filename)

    # Download and save the image
    response = requests.get(image_url)
    with open(file_path, 'wb') as f:
        f.write(response.content)

    return file_path


def save_item_text(folder, text_content):
    text_file_path = os.path.join(folder, "order_data.txt")
    try:
        with open(text_file_path, 'a') as text_file:
            text_file.write(text_content)
        # print(f"Item text saved: {text_file_path}")
    except OSError as e:
        print(f"Error saving item text: {e}")

def fetch_all_products():
    products_url = f"{SHOPIFY_STORE_URL}/admin/api/2023-04/products.json"
    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(products_url, headers=headers)
        response.raise_for_status()
        return response.json().get("products", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching products: {e}")
        return []
    
def get_product_images_and_metafield(product_name, products):

    headers = {
        "X-Shopify-Access-Token": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    product = next((p for p in products if p["title"].strip().lower() == product_name.strip().lower()), None)
    if not product:
        print(f"No product found with the name: {product_name}")
        return None, []
    
    try:
        product_id = product["id"]
        print("Product ID:", product_id)

        # Fetch product images
        product_images = product.get("images", [])
        second_image_url = product_images[1]["src"] if len(product_images) > 1 else None

        # Fetch product metafields
        metafields_url = f"{SHOPIFY_STORE_URL}/admin/api/2023-04/products/{product_id}/metafields.json"
        metafields_response = requests.get(metafields_url, headers=headers)
        metafields_response.raise_for_status()

        metafields = metafields_response.json().get("metafields", [])
        builder_images_metafield = next((mf for mf in metafields if mf["namespace"] == "custom" and mf["key"] == "builder_images"), None)

        builder_images_list = []
        if builder_images_metafield:
            builder_images = json.loads(builder_images_metafield["value"])  # Assuming JSON array
            print("Builder Images GIDs:", builder_images)

            image_urls = get_image_urls_from_gids(builder_images)
            builder_images_list.extend(image_urls)

        return second_image_url, builder_images_list

    except requests.exceptions.RequestException as e:
        print(f"Error fetching product images for '{product_name}': {e}")
        return None, []

def get_product_image_url(product_id):
    url = f"{SHOPIFY_STORE_URL}/admin/api/2023-04/products/{product_id}.json"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        product = response.json().get("product", {})
        print("productData", product)
        if "image" in product and product["image"]:
            image_url = product["image"]["src"]
            print(f"Image URL fetched for product {product_id}: {image_url}")
            return image_url
        else:
            print(f"No image found for product {product_id}.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching product image for product {product_id}: {e}")
    
    return None

def get_image_urls_from_gids(gids):
    query = """
    query($ids: [ID!]!) {
      nodes(ids: $ids) {
        ... on MediaImage {
          image {
            originalSrc
          }
        }
      }
    }
    """
    
    variables = {"ids": gids}
    graphql_url = f"{SHOPIFY_STORE_URL}/admin/api/2024-10/graphql.json"
    headers = {
        "Content-Type": "application/json",
        "X-Shopify-Access-Token": ACCESS_TOKEN
    }

    try:
        response = requests.post(graphql_url, headers=headers, json={"query": query, "variables": variables})
        response.raise_for_status()

        response_data = response.json()
        if 'errors' in response_data:
            print(f"GraphQL Error: {response_data['errors']}")
            return []

        image_urls = [
            node.get("image", {}).get("originalSrc")
            for node in response_data.get("data", {}).get("nodes", [])
            if node.get("image", {}).get("originalSrc")
        ]
        return image_urls

    except requests.exceptions.RequestException as e:
        print(f"Error fetching image URLs: {e}")
        return []
