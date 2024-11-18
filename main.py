import sys
import os
import re
import json
import time
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
from config_manager import ConfigManager  # Import the ConfigManager class
from datetime import datetime
import sqlite3


from fetch_unfulfilled_orders import (
    get_unfulfilled_orders,
    create_item_subfolder,
    download_image,
    create_fulfillment,
    get_product_image_url
)
from pdf_builder import create_pdf
from purchase_gift_card import (purchase_gift_card, get_claim_and_pin_codes)


class OrderFetcher(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int, str)
    updateLastSavedOrder = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    message = QtCore.pyqtSignal(str)
    errorMessage = QtCore.pyqtSignal(str)
    
    
    
    def __init__(self, data_path, last_order_num):
        super().__init__()
        self.data_path = data_path
        self.last_order_num = last_order_num
        self.temp_last_order_num = last_order_num
        self.gift_card_data = None
        with open('./asset/gift_card/shop-card-id.json', 'r') as file:
            self.gift_card_data = json.load(file)
    # connect to sqlite(gift_card.db)
        self.sqlConn = sqlite3.connect("./asset/gift_card.db", check_same_thread=False)
        self.cursor = self.sqlConn.cursor()

    def run(self):
     
        # Fetch unfulfilled orders
        unfulfilled_orders = get_unfulfilled_orders()

        if not unfulfilled_orders:
            self.message.emit("No unfulfilled orders found.")
            self.finished.emit()
            return

        total_orders = len(unfulfilled_orders)

        self.progress.emit(0, total_orders, f"Processing 0 of {total_orders} orders")

        # products_data = fetch_all_products()
        
        if total_orders > 0:
            current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        current_order_data_folder = os.path.join(self.data_path, current_time)
        os.makedirs(current_order_data_folder, exist_ok=True)
        
        for index, order in enumerate(unfulfilled_orders):
            # print("order=================>",order["line_items"])
            order_id = order["order_number"]
            # order_folder, created = create_order_folder(self.data_path, order_id)

            # if not created:
            
            #     print(f"Order folder for #{order_id} already exists.")
            #     continue
            # if order_id != 1071:
            #     continue

             # Update last order number
            

             # Update progress bar
            self.progress.emit(index + 1, 0, f"Processing {index + 1} of {total_orders} orders")

            sucess = self.process_order_items(order, current_order_data_folder)
            if sucess:
             if order_id > self.last_order_num:
                self.last_order_num = order_id 
            else:
                break

        # Emit the final message and finish signal
        self.updateLastSavedOrder.emit(self.last_order_num)
        self.message.emit(f"{total_orders} Orders have been successfully fetched and saved.")
        self.finished.emit()

    def process_order_items(self, order, order_folder):
        # print("Order===========>", order)
        fulfillment_flag = True
        order_num = order["order_number"]
        order_id = order["id"]
        index = 1
        for  item in order["line_items"]:
            item_name = item["name"]
            # product_id = item["product_id"]
            # item_description = item["title"]
            item_quantity = item["quantity"]
            
            properties_to_save = {
                "radio-buttons-14": "",
                "1b. Custom Design Upload-1": "",
                "2b. Custom Design Upload-2": "",
                "3b. Custom Design Upload-3": "",
                "1. Box Designs": "",
                "2. Gift ": "",
                "3. Add on ": "",
                "Font": "",
                "Type your message here": "",
                "Pictures and/or Logo-1": "",
                "Pictures and/or Logo-2": "",
                "Pictures and/or Logo-3": "",
                "_main_prd": "",
                "Bonus Gift" : "",

                "Print": "",
                "font": "",
                "Gift": "",
                "To": "",
                "From": "",
                "Message" : "",
                "upload1" : "",
                "upload2" : "",
                "upload3" : "",
                "Shipping" : "",
                "3. Gift Cards" : "",
                "date-range-16" : ""
            }

            for prop in item["properties"]:
                prop_name = prop["name"]
                prop_value = prop["value"]

                if prop_name in properties_to_save:
                    properties_to_save[prop_name] = prop_value
            temp_folder = "./temp"
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)
                
            if "Print" in item["title"] and len(item["properties"]) == 0:
                design_product_name = item_name
                # Strip pricing info from the design product name
                match = re.search(r'^(.*?)\s*\(\s*\+\$[\d,.]+\s*\)', design_product_name)
                if match:
                    design_product_name = match.group(1).strip()
                
                # Find product directory in ./asset/products
                product_directory = os.path.join("./asset/products", design_product_name)


                if os.path.exists(product_directory):
                    inner_image_path = os.path.join(product_directory, "inner.jpg")
                    outer_image_path = os.path.join(product_directory, "outer.jpg")

                    if not os.path.exists(inner_image_path):
                        self.errorMessage.emit(f"inner.png not found in {product_directory}")
                        fulfillment_flag = False
                        continue
                    if not os.path.exists(outer_image_path):
                        self.errorMessage.emit(f"outer.png not found in {product_directory}")
                        fulfillment_flag = False
                        continue
                else:
                    self.errorMessage.emit(f"Product directory '{design_product_name}' not found in ./asset/products")
                    fulfillment_flag = False
                    continue
                if fulfillment_flag:
                    output_pdf = f"{order_folder}/#{order_num}__{index}-{item_quantity}.pdf"
                    create_pdf("","", "", "", "", "", "", order_num, "", output_pdf, outer_image_path, inner_image_path)
                    self.errorMessage.emit(f"{order_folder}/#{order_num}__{index}-{item_quantity}.pdf created")
                    index += 1  
            if properties_to_save.get("radio-buttons-14"):
                # if item_quantity:
                #  item_directory_name = f"#{index} - " + item_name + f" - {item_quantity }"
                # else:
                #  item_directory_name = f"#{index} - " + item_name
                # item_folder = create_item_subfolder(order_folder, item_directory_name)
                gift = properties_to_save.get("2. Gift ", "")
                designOption = properties_to_save.get("radio-buttons-14")
                
                if designOption == "Designed by you":
                    item_folder = create_item_subfolder(order_folder, f"#{order_num}__{index}-{item_quantity}-(designed by you)" )
                    # save_item_text(item_folder, f"Designed by you. \n")
                    if properties_to_save.get("1b. Custom Design Upload-1"):
                     download_image(properties_to_save.get("1b. Custom Design Upload-1"),item_folder,"Custom Design-1.jpg")
                    if properties_to_save.get("2b. Custom Design Upload-2"):
                     download_image(properties_to_save.get("1b. Custom Design Upload-2"),item_folder,"Custom Design-2.jpg")
                    if properties_to_save.get("3b. Custom Design Upload-3"):
                     download_image(properties_to_save.get("3b. Custom Design Upload-3"),item_folder,"Custom Design-3.jpg")
                    if properties_to_save.get("Pictures and/or Logo-1"):
                     download_image(properties_to_save.get("Pictures and/or Logo-1"),item_folder,"Logo-1.jpg")
                    if properties_to_save.get("Pictures and/or Logo-2"):
                     download_image(properties_to_save.get("Pictures and/or Logo-2"),item_folder,"Logo-2.jpg")
                    if properties_to_save.get("Pictures and/or Logo-3"):
                     download_image(properties_to_save.get("Pictures and/or Logo-3"),item_folder,"Logo-3.jpg")
                if "Designed for you" in designOption:
                    item_folder = create_item_subfolder(order_folder, f"#{order_num}__{index}-{item_quantity}-(designed for you)" )
                    # save_item_text(item_folder, f"Designed for you, $50 added to invoice. \n")
                    if properties_to_save.get("Pictures and/or Logo-1"):
                     download_image(properties_to_save.get("Pictures and/or Logo-1"),item_folder,"Logo-1.jpg")
                    if properties_to_save.get("Pictures and/or Logo-2"):
                     download_image(properties_to_save.get("Pictures and/or Logo-2"),item_folder,"Logo-2.jpg")
                    if properties_to_save.get("Pictures and/or Logo-3"):
                     download_image(properties_to_save.get("Pictures and/or Logo-3"),item_folder,"Logo-3.jpg")
                if designOption == "Choose from our designs":
                    # check date range
                    creatable_pdf = False
                    if properties_to_save.get("1. Box Designs"):
                        date_range_from = properties_to_save.get("date-range-16", "")
                        if order_num <= self.temp_last_order_num:
                            if date_range_from != "":
                                date_range_from = date_range_from[:10]
                                date_range_from_datetime = datetime.strptime(date_range_from, "%Y-%m-%d")
                                current_datetime = datetime.now()
                                if current_datetime >= date_range_from_datetime:
                                    creatable_pdf = True
                                else:
                                    creatable_pdf = False
                                    fulfillment_flag = False
                        else:
                             if date_range_from != "":
                                date_range_from = date_range_from[:10]
                                date_range_from_datetime = datetime.strptime(date_range_from, "%Y-%m-%d")
                                current_datetime = datetime.now()
                                if current_datetime >= date_range_from_datetime:
                                    creatable_pdf = True
                                else:
                                    creatable_pdf = False
                                    fulfillment_flag = False
                             else:
                                 creatable_pdf = True
                            
                    if creatable_pdf:
                        design_product_name = properties_to_save['1. Box Designs']
                        # Strip pricing info from the design product name
                        match = re.search(r'^(.*?)\s*\(\s*\+\$[\d,.]+\s*\)', design_product_name)
                        if match:
                            design_product_name = match.group(1).strip()
                        # Find product directory in ./asset/products
                        product_directory = os.path.join("./asset/products", design_product_name)
                        if os.path.exists(product_directory):
                            inner_image_path = os.path.join(product_directory, "inner.jpg")
                            outer_image_path = os.path.join(product_directory, "outer.jpg")

                            if not os.path.exists(inner_image_path):
                                self.errorMessage.emit(f"inner.png not found in {product_directory}")
                                fulfillment_flag = False
                                continue
                            if not os.path.exists(outer_image_path):
                                self.errorMessage.emit(f"outer.png not found in {product_directory}")
                                fulfillment_flag = False
                                continue
                        else:
                            self.errorMessage.emit(f"Product directory '{design_product_name}' not found in ./asset/products")
                            fulfillment_flag = False
                            continue
                        # Collect user images (default to empty string if not provided)
                        user_custom_image = ["","",""] 
                        if properties_to_save["Pictures and/or Logo-1"]:
                            user_custom_image[0] = properties_to_save["Pictures and/or Logo-1"]
                            download_image(user_custom_image[0], temp_folder, "custom_0.png")
                        if properties_to_save["Pictures and/or Logo-2"]:
                            user_custom_image[1] = properties_to_save["Pictures and/or Logo-2"]
                            download_image(user_custom_image[1], temp_folder, "custom_1.png")
                        if properties_to_save["Pictures and/or Logo-3"]:
                            user_custom_image[2] = properties_to_save["Pictures and/or Logo-3"]
                            download_image(user_custom_image[2], temp_folder, "custom_2.png")

                        # Additional properties
                        text_font = properties_to_save.get("Font","Questrial")
                        if text_font == "":
                            text_font = "Questrial"
                        font_path = f'./asset/font/{text_font}/{text_font}.ttf'
                        if not os.path.exists(font_path):
                         self.errorMessage.emit(f"{font_path} does not exist in {order_num}-{index} order")
                         fulfillment_flag = False
                         continue
                        text_description = properties_to_save.get("Type your message here", "")
                        
                        gift_card = properties_to_save.get("3. Gift Cards", "")
                        gift = properties_to_save.get("2. Gift ","")
                        addon = properties_to_save.get("3. Add on ", "")
                        gift_product_img_url, gift_product_title = "", ""
                        addon_img_url, addon_title = "", ""
                        gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url, gift_card_title, error_meassage = "", "", "", "", "", ""
                        gift_card_price = 0
                        _main_prd = item["variant_id"]
                        if gift != "":
                             for line_item in order["line_items"]:
                                if line_item["gift_card"] == False and line_item["properties"][0]["value"] == f"{_main_prd}" and line_item["title"] in gift:
                                    gift_product_img_url = get_product_image_url(line_item["product_id"])
                                    gift_product_title = line_item["title"]
                                    download_image(gift_product_img_url, temp_folder, "gift_product_img.png")
                                    break
                        if addon != "":
                             for line_item in order["line_items"]:
                                if line_item["gift_card"] == False and line_item["properties"][0]["value"] == f"{_main_prd}" and line_item["title"] in addon:
                                    addon_img_url = get_product_image_url(line_item["product_id"])
                                    addon_title = line_item["title"]
                                    download_image(addon_img_url, temp_folder, "addon_img.png")
                                    break
                        if gift_card != "":
                            downloaded_card_img = False
                            for inner_index in range(item["quantity"]):
                                for line_item in order["line_items"]:
                                    if line_item["gift_card"] == True and line_item["properties"][0]["value"] == f"{_main_prd}":
                                        gift_card_sku = line_item["sku"]
                                        gift_card_order_id = self.gift_card_data.get(gift_card_sku, None)
                                        if gift_card_order_id == None:
                                            self.errorMessage.emit(f"Not found gift card id. please check shop-card-id.json - {gift_card_sku}")
                                            fulfillment_flag = False
                                        elif gift_card_order_id == 0:
                                            gift_image_url = get_product_image_url(line_item["product_id"])
                                            download_image(gift_image_url, temp_folder, "gift_card.png")
                                        else:
                                            gift_card_price = line_item["price"]
                                            gift_card_title = line_item["title"]
                                            item_index = f"{order_num}__{index}-{item_quantity}-{inner_index + 1}"
                                            res = self.cursor.execute("SELECT * FROM gift_tb WHERE item_index = ?", (item_index,))
                                            gift_res_data = res.fetchone()
                                            if gift_res_data != None:
                                                if gift_res_data[2] != '':
                                                        gift_card_claim_code = gift_res_data[2]
                                                        gift_card_pin_code = gift_res_data[3]
                                                        gift_card_text = gift_res_data[4]
                                                        gift_image_url = gift_res_data[5]
                                                else:
                                                    purchase_url = gift_res_data[1]
                                                    gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url, error_meassage = get_claim_and_pin_codes(purchase_url)
                                                    if error_meassage != "":
                                                        fulfillment_flag = False
                                                        _error_message = f"when purchase gift card in {order_num} order, " + error_meassage
                                                        self.errorMessage.emit(f"{_error_message}")
                                                        break
                                            else:
                                                gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url, error_meassage, purchase_url = purchase_gift_card(3426, "alex@greetabl.com")
                                                self.cursor.execute("""
                                                    INSERT INTO gift_tb (item_index, purchase_url, gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url)
                                                    VALUES (?, ?, ?, ?, ?, ?)
                                                """, (item_index, purchase_url, gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url))

                                                # Commit the transaction
                                                self.sqlConn.commit()
                                                if error_meassage != "":
                                                    fulfillment_flag = False
                                                    _error_message = f"when purchase gift card in {order_num} order, " + error_meassage
                                                    self.errorMessage.emit(f"{_error_message}")
                                                    break
                                            if not downloaded_card_img:
                                             download_image(gift_image_url, temp_folder, "gift_card.png")
                                             downloaded_card_img = True
                                            if fulfillment_flag:
                                                output_pdf = f"{order_folder}/#{order_num}__{index}-{item_quantity}-{inner_index + 1}.pdf"
                                                create_pdf(gift_card_claim_code,gift_card_pin_code, gift_card_text, gift_image_url,gift_product_img_url, gift_product_title, gift_card_price, order_num, gift_card_title, output_pdf,outer_image_path, inner_image_path, user_custom_image,"",text_description,"", text_font , addon_img_url, addon_title)
                                                self.errorMessage.emit(f"{order_folder}/#{order_num}__{index}-{item_quantity}-{inner_index + 1}.pdf created")
                            
                            if not fulfillment_flag:
                                    for filename in os.listdir(f"{order_folder}"):
                                        if f"{order_folder}/#{order_num}__{index}-{item_quantity}-" in filename and filename.endswith(".pdf"):
                                            file_path = os.path.join(f"{order_folder}", filename)
                                            try:
                                                os.remove(file_path)
                                                print(f"Deleted: {file_path}")
                                            except Exception as e:
                                                print(f"Error deleting {file_path}: {e}")
                        else:
                            # Create PDF with customization
                            if fulfillment_flag:
                                output_pdf = f"{order_folder}/#{order_num}__{index}-{item_quantity}.pdf"
                                create_pdf(gift_card_claim_code,gift_card_pin_code, gift_card_text, gift_image_url, gift_product_img_url, gift_product_title, gift_card_price, order_num, gift_card_title, output_pdf, outer_image_path, inner_image_path, user_custom_image,"", text_description,"", text_font , addon_img_url, addon_title)
                                self.errorMessage.emit(f"{order_folder}/#{order_num}__{index}-{item_quantity}.pdf created")                       
                            # print(f"PDF created: {output_pdf}")
                index += 1

            if properties_to_save.get("Print"):
                design_product_name = item_name
                # Strip pricing info from the design product name
                match = re.search(r'^(.*?)\s*\(\s*\+\$[\d,.]+\s*\)', design_product_name)
                if match:
                    design_product_name = match.group(1).strip()
                
                # Find product directory in ./asset/products
                product_directory = os.path.join("./asset/products", design_product_name)


                if os.path.exists(product_directory):
                    inner_image_path = os.path.join(product_directory, "inner.jpg")
                    outer_image_path = os.path.join(product_directory, "outer.jpg")

                    if not os.path.exists(inner_image_path):
                        self.errorMessage.emit(f"inner.png not found in {product_directory}")
                        fulfillment_flag = False
                        continue
                    if not os.path.exists(outer_image_path):
                        self.errorMessage.emit(f"outer.png not found in {product_directory}")
                        fulfillment_flag = False
                        continue
                else:
                    self.errorMessage.emit(f"Product directory '{design_product_name}' not found in ./asset/products")
                    fulfillment_flag = False
                    continue

                # Collect user images (default to empty string if not provided)
                user_custom_image = ["","",""] 
                if properties_to_save["upload1"]:
                    user_custom_image[0] = properties_to_save["upload1"]
                    download_image(user_custom_image[0], temp_folder, "custom_0.png")

                if properties_to_save["upload2"]:
                    user_custom_image[1] = properties_to_save["upload2"]
                    download_image(user_custom_image[1], temp_folder, "custom_1.png")

                if properties_to_save["upload3"]:
                    user_custom_image[2] = properties_to_save["upload3"]
                    download_image(user_custom_image[2], temp_folder, "custom_2.png")


                # Additional properties
                text_font = properties_to_save.get("font", "Questrial")
                if text_font == "":
                     text_font = "Questrial"
                font_path = f'./asset/font/{text_font}/{text_font}.ttf'
                if not os.path.exists(font_path):
                    self.errorMessage.emit(f"{font_path} does not exist in {order_num}-{index} order")
                    fulfillment_flag = False
                    continue
                
                text_description = properties_to_save.get("Message", "")
                text_to = properties_to_save.get("To", "")
                text_from = properties_to_save.get("From", "")
                gift = properties_to_save.get("Gift","")
                gift_card = properties_to_save.get("Bonus Gift", "")
                gift_product_img_url = ""
                gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url, gift_card_title, error_meassage = "", "", "", "", "", ""
                gift_product_title = ""
                gift_card_price = 0
                _main_prd = properties_to_save.get("_main_prd", "")
                if gift != "":
                   for line_item in order["line_items"]:
                        if line_item["gift_card"] == False and line_item["properties"][0]["value"] == _main_prd:
                            gift_product_img_url = get_product_image_url(line_item["product_id"]) 
                            gift_product_title = line_item["title"]
                            download_image(gift_product_img_url, temp_folder, "gift_product_img.png")
                            break
                if gift_card != "":
                    for line_item in order["line_items"]:
                        if line_item["gift_card"] == True and line_item["properties"][0]["value"] == _main_prd:
                            gift_card_sku = line_item["sku"]
                            gift_card_order_id = self.gift_card_data.get(gift_card_sku, None)
                            if gift_card_order_id == None:
                                self.errorMessage.emit(f"Not found gift card id. please check shop-card-id.json - {gift_card_sku}")
                                fulfillment_flag = False
                            elif gift_card_order_id == 0:
                                gift_image_url = get_product_image_url(line_item["product_id"])
                                download_image(gift_image_url, temp_folder, "gift_card.png")
                            else:
                                gift_card_price = line_item["price"]
                                gift_card_title = line_item["title"]
                                item_index = f"{order_num}__{index}-{item_quantity}"
                                res = self.cursor.execute("SELECT * FROM gift_tb WHERE item_index = ?", (item_index,))
                                gift_res_data = res.fetchone()
                                if gift_res_data != None:
                                  if gift_res_data[2] != '':
                                        gift_card_claim_code = gift_res_data[2]
                                        gift_card_pin_code = gift_res_data[3]
                                        gift_card_text = gift_res_data[4]
                                        gift_image_url = gift_res_data[5]
                                  else:
                                       purchase_url = gift_res_data[1]
                                       gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url, error_meassage = get_claim_and_pin_codes(purchase_url)
                                       if error_meassage != "":
                                        fulfillment_flag = False
                                        _error_message = f"when purchase gift card in {order_num} order, " + error_meassage
                                        self.errorMessage.emit(f"{_error_message}")
                                        break
                                else:
                                    gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url, error_meassage, purchase_url = purchase_gift_card(gift_card_order_id, "alex@greetabl.com")
                                    self.cursor.execute("""
                                                    INSERT INTO gift_tb (item_index, purchase_url, gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url)
                                                    VALUES (?, ?, ?, ?, ?, ?)
                                                """, (item_index, purchase_url, gift_card_claim_code, gift_card_pin_code, gift_card_text, gift_image_url))
                                    self.sqlConn.commit()
                                    if error_meassage != "":
                                     fulfillment_flag = False
                                     _error_message = f"when purchase gift card in {order_num} order, " + error_meassage
                                     self.errorMessage.emit(f"{_error_message}")
                                     break
                                download_image(gift_image_url, temp_folder, "gift_card.png")
                # Create PDF with customization
                if fulfillment_flag:
                    output_pdf = f"{order_folder}/#{order_num}__{index}-{item_quantity}.pdf"
                    create_pdf(gift_card_claim_code,gift_card_pin_code, gift_card_text, gift_image_url, gift_product_img_url, gift_product_title, gift_card_price, order_num, gift_card_title, output_pdf, outer_image_path, inner_image_path, user_custom_image,text_to, text_description, text_from, text_font)
                    self.errorMessage.emit(f"{order_folder}/#{order_num}__{index}-{item_quantity}.pdf created")
                    index += 1                 
                # print(f"PDF created: {output_pdf}")
                
        # make fulfullment status as fulfilled
        # if fulfillment_flag:
        #     create_fulfillment(order_id)
        if fulfillment_flag:
          item_index = f"{order_num}__"
          item_index_pattern = f"{item_index}%"
          self.cursor.execute("DELETE FROM gift_tb WHERE item_index LIKE ?", (item_index_pattern,))
          self.sqlConn.commit()
        return fulfillment_flag
            
class MainWindow(QtWidgets.QDialog):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('main.ui', self)

        # self.setWindowIcon(QtGui.QIcon("./asset/greetabl_g.png"))
        self.config_manager = ConfigManager()
        self.data_path = self.config_manager.get_order_data_directory()
        if self.data_path == "" or not os.path.exists(self.data_path):
            self.config_manager.initialize_config()
            self.data_path = os.path.join(os.getcwd(), 'OrderData')
        self.temp_data_path = self.data_path
        self.last_order_num = self.config_manager.get_last_saved_order_number()
        self.new_ordered_num = 0
        self.processing_order_num = 0
        self.is_fetching = False
        self.fetching_new_order_num()
        self.init_ui()
        

    def init_ui(self):
        self.selectDirectoryBtn = self.findChild(QtWidgets.QToolButton, 'selectDirectoryBtn')
        self.locationLET = self.findChild(QtWidgets.QLineEdit, 'directoryLET')
        self.getOrderBtn = self.findChild(QtWidgets.QPushButton, 'getOrderBtn')
        self.lastOrderNumLET = self.findChild(QtWidgets.QLineEdit, 'lastOrderNumLET')
        self.saveBtn = self.findChild(QtWidgets.QPushButton, 'saveBtn')
        self.cancelBtn = self.findChild(QtWidgets.QPushButton, 'cancelBtn')
        self.progressBar = self.findChild(QtWidgets.QProgressBar, 'progressBar')
        self.newOrderLAB = self.findChild(QtWidgets.QLabel, 'new_orderd_num')
        self.processingOrderLAB = self.findChild(QtWidgets.QLabel, 'processing_orders_num')
        self.errorLog = self.findChild(QtWidgets.QPlainTextEdit, 'errorLog')
        self.progressBar.setValue(0)

        self.locationLET.setText(self.data_path)
        self.lastOrderNumLET.setText(str(self.last_order_num))


        self.selectDirectoryBtn.clicked.connect(self.set_location)
        self.getOrderBtn.clicked.connect(self.start_order_fetching)
        self.saveBtn.clicked.connect(self.save_setting_data)
        self.cancelBtn.clicked.connect(self.cancel_setting_data)
        self.newOrderLAB.setText(f'New Orders: {self.new_ordered_num}')
        self.processingOrderLAB.setText(f'Processing Orders: {self.processing_order_num}')

    def fetching_new_order_num(self):
        unfulfilled_orders = get_unfulfilled_orders()
        total_unfulfilled_orders = len(unfulfilled_orders)
        if not unfulfilled_orders:
            print("No unfulfilled orders found.")
            return
        self.new_ordered_num = 0
        for  order in unfulfilled_orders:
            order_id = order["order_number"]
            if order_id > self.last_order_num:
                self.new_ordered_num += 1
        self.processing_order_num = total_unfulfilled_orders - self.new_ordered_num

    def closeEvent(self, event):
        if self.is_fetching:
            event.ignore()  # Ignore the close event
            QtWidgets.QMessageBox.warning(self, "Warning", "Cannot close while fetching orders.")
        else:
            event.accept()

    def set_location(self):
        selected_folder = QFileDialog.getExistingDirectory(self, "Select Folder", self.data_path)
        if selected_folder:
            self.temp_data_path = selected_folder
            self.locationLET.setText(self.temp_data_path)
            self.saveBtn.setEnabled(True)
            self.cancelBtn.setEnabled(True)

    def save_setting_data(self):
        self.config_manager.update_order_data_directory(self.temp_data_path)
        self.data_path = self.temp_data_path
        self.saveBtn.setEnabled(False)
        self.cancelBtn.setEnabled(False)
        QtWidgets.QMessageBox.information(self, "Success", f"Order data directory updated to: {self.data_path}")

    def cancel_setting_data(self):
        self.locationLET.setText(self.data_path)
        self.saveBtn.setEnabled(False)
        self.cancelBtn.setEnabled(False)

    def start_order_fetching(self):
        if self.data_path != self.temp_data_path:
            self.save_setting_data()
        self.getOrderBtn.setText("")
        self.selectDirectoryBtn.setEnabled(False)
        self.is_fetching = True

        self.spinner_movie = QtGui.QMovie('./asset/spinner.gif')
        self.spinner_label = QtWidgets.QLabel(self.getOrderBtn)
        self.spinner_label.setGeometry(45, 0, 40, 40)
        self.spinner_movie.setScaledSize(QtCore.QSize(40, 40))
        self.spinner_label.setMovie(self.spinner_movie)
        self.spinner_movie.start()
        self.spinner_label.show()

        self.getOrderBtn.setEnabled(False)
        
        self.thread = QtCore.QThread()
        self.worker = OrderFetcher(self.data_path, self.last_order_num)
        self.worker.moveToThread(self.thread)
        
        self.worker.progress.connect(self.update_progress)
        self.worker.message.connect(self.show_message)
        self.worker.errorMessage.connect(self.show_error_message)
        self.worker.updateLastSavedOrder.connect(self.updateLastSavedOrder)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.finished.connect(self.reset_get_order_button)
        self.thread.started.connect(self.worker.run)

        self.thread.start()

    def updateLastSavedOrder(self, value):
        self.last_order_num = value
        self.lastOrderNumLET.setText(str(self.last_order_num))
        self.config_manager.update_last_saved_order_number(self.last_order_num)

    def update_progress(self, value, total_order_num, text):
        if total_order_num > 0:
         self.progressBar.setMaximum(total_order_num)  
        self.progressBar.setValue(value)
        self.progressBar.setFormat(text)

    def show_message(self, message):
        QtWidgets.QMessageBox.information(self, "Information", message)
        
    def show_error_message(self, message):
        self.errorLog.insertPlainText(f"{message}\n")

    def reset_get_order_button(self):
        self.is_fetching = False
        self.spinner_movie.stop()
        self.spinner_label.hide()
        self.getOrderBtn.setText("GET ORDER")
        self.getOrderBtn.setEnabled(True)
        self.selectDirectoryBtn.setEnabled(True)
        self.progressBar.setValue(0)
        self.progressBar.setFormat("")
        self.fetching_new_order_num()
        self.newOrderLAB.setText(f'New Orders: {self.new_ordered_num}')
        self.processingOrderLAB.setText(f'Processing Orders: {self.processing_order_num}')

# Start the application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    app.setWindowIcon(QtGui.QIcon("./asset/greetabl_g.png"))
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%Y-%m-%d")
   
    window = MainWindow()
    window.setWindowTitle(f"Greetabl Gift   {formatted_date}")
    window.show()
    sys.exit(app.exec_())
