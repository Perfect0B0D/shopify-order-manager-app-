import sys
import os
import re
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
from config_manager import ConfigManager  # Import the ConfigManager class

from fetch_unfulfilled_orders import (
    get_unfulfilled_orders,
    create_order_folder,
    create_item_subfolder,
    get_product_images_and_metafield,
    save_item_text,
    fetch_all_products
)
from pdf_builder import create_pdf


class OrderFetcher(QtCore.QObject):
    progress = QtCore.pyqtSignal(int, int, str)
    updateLastSavedOrder = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()
    message = QtCore.pyqtSignal(str)

    def __init__(self, data_path, last_order_num):
        super().__init__()
        self.data_path = data_path
        self.last_order_num = last_order_num

    def run(self):
        # Fetch unfulfilled orders
        unfulfilled_orders = get_unfulfilled_orders()

        if not unfulfilled_orders:
            self.message.emit("No unfulfilled orders found.")
            self.finished.emit()
            return

        total_orders = len(unfulfilled_orders)

        self.progress.emit(0, total_orders, f"Processing 0 of {total_orders} orders")

        products_data = fetch_all_products()

        for index, order in enumerate(unfulfilled_orders):
            print("order=================>",order)
            order_id = order["order_number"]
            order_folder, created = create_order_folder(self.data_path, order_id)

            if not created:
                print(f"Order folder for #{order_id} already exists.")
                continue

            if order_id > self.last_order_num:
                self.last_order_num = order_id  # Update last order number
            

             # Update progress bar
            self.progress.emit(index + 1, 0, f"Processing {index + 1} of {total_orders} orders")

            self.process_order_items(order, order_folder, products_data)

           

        # Emit the final message and finish signal
        self.updateLastSavedOrder.emit(self.last_order_num)
        self.message.emit(f"{total_orders} Orders have been successfully fetched and saved.")
        self.finished.emit()

    def process_order_items(self, order, order_folder, products_data):
        # print("Order===========>", order)
        for item in order["line_items"]:
            item_name = item["name"]
            product_id = item["product_id"]
            item_description = item["title"]
            item_quantity = item["quantity"]
            item_directory_name = ""
            if item_quantity:
                item_directory_name = item_name + f" - {item_quantity}" 

            # Create a subfolder for the item
            item_folder = create_item_subfolder(order_folder, item_directory_name)

            # Save item text (title)
            # save_item_text(item_folder, f"Product description: {item_description}")

            properties_to_save = {
                "1. Box Designs": None,
                "2. Gift ": None,
                "Font": None,
                "Type your message here": None,
                "Pictures and/or Logo-1": None,
                "Pictures and/or Logo-2": None,
                "Pictures and/or Logo-3": None,

                "Print": None,
                "font": None,
                "Gift": None,
                "To": None,
                "From": None,
                "Message" : None,
                "upload1" : None,
                "upload2" : None,
                "upload3" : None
            }

            for prop in item["properties"]:
                prop_name = prop["name"]
                prop_value = prop["value"]

                if prop_name in properties_to_save:
                    properties_to_save[prop_name] = prop_value

            if properties_to_save.get("1. Box Designs"):
                # save_item_text(item_folder, f"\n1. Box Designs: {properties_to_save['1. Box Designs']}")
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
                        print(f"inner.png not found in {product_directory}")
                        continue
                    if not os.path.exists(outer_image_path):
                        print(f"outer.png not found in {product_directory}")
                        continue
                else:
                    print(f"Product directory '{design_product_name}' not found in ./asset/products")
                    continue

                # Collect user images (default to empty string if not provided)
                user_custom_image = ["","",""] 
                if properties_to_save["Pictures and/or Logo-1"]:
                    user_custom_image[0] = properties_to_save["Pictures and/or Logo-1"]
                if properties_to_save["Pictures and/or Logo-2"]:
                    user_custom_image[1] = properties_to_save["Pictures and/or Logo-2"]
                if properties_to_save["Pictures and/or Logo-3"]:
                    user_custom_image[2] = properties_to_save["Pictures and/or Logo-3"]

                # Additional properties
                text_font = properties_to_save.get("Font","Questrial")
                if text_font == "":
                 text_font = "Questrial"
                text_description = properties_to_save.get("Type your message here", "")

                # Create PDF with customization
                output_pdf = f"{item_folder}/product_customization.pdf"
                create_pdf(output_pdf, outer_image_path, inner_image_path, user_custom_image,"", text_description,"", text_font)
                # print(f"PDF created: {output_pdf}")
            
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
                        print(f"inner.png not found in {product_directory}")
                        continue
                    if not os.path.exists(outer_image_path):
                        print(f"outer.png not found in {product_directory}")
                        continue
                else:
                    print(f"Product directory '{design_product_name}' not found in ./asset/products")
                    continue

                # Collect user images (default to empty string if not provided)
                user_custom_image = ["","",""] 
                if properties_to_save["upload1"]:
                    user_custom_image[0] = properties_to_save["upload1"]
                if properties_to_save["upload2"]:
                    user_custom_image[1] = properties_to_save["upload2"]
                if properties_to_save["upload3"]:
                    user_custom_image[2] = properties_to_save["upload3"]

                # Additional properties
                text_font = properties_to_save.get("font", "Questrial")
                if text_font == "":
                 text_font = "Questrial"
                text_description = properties_to_save.get("Message", "")
                text_to = properties_to_save.get("To", "")
                text_from = properties_to_save.get("From", "")
                gift = properties_to_save.get("Gift","")

                # Create PDF with customization
                output_pdf = f"{item_folder}/product_customization.pdf"
                create_pdf(output_pdf, outer_image_path, inner_image_path, user_custom_image,text_to, text_description, text_from, text_font)
                # print(f"PDF created: {output_pdf}")

class MainWindow(QtWidgets.QDialog):

    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi('main.ui', self)

        self.setWindowIcon(QtGui.QIcon("./asset/greetabl_g.png"))
       

        self.config_manager = ConfigManager()
        self.data_path = self.config_manager.get_order_data_directory()
        if self.data_path == "":
            self.config_manager.initialize_config()
            self.data_path = self.config_manager.get_order_data_directory()
        self.temp_data_path = self.config_manager.get_order_data_directory()
        self.last_order_num = self.config_manager.get_last_saved_order_number()
        self.new_ordered_num = 0
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
        self.progressBar.setValue(0)

        self.locationLET.setText(self.data_path)
        self.lastOrderNumLET.setText(str(self.last_order_num))


        self.selectDirectoryBtn.clicked.connect(self.set_location)
        self.getOrderBtn.clicked.connect(self.start_order_fetching)
        self.saveBtn.clicked.connect(self.save_setting_data)
        self.cancelBtn.clicked.connect(self.cancel_setting_data)
        self.newOrderLAB.setText(f'New orders: {self.new_ordered_num}')

    def fetching_new_order_num(self):
        unfulfilled_orders = get_unfulfilled_orders()

        if not unfulfilled_orders:
            print("No unfulfilled orders found.")
            return
        self.new_ordered_num = 0
        for  order in unfulfilled_orders:
            order_id = order["order_number"]
            if order_id > self.last_order_num:
                self.new_ordered_num += 1

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
        self.worker.updateLastSavedOrder.connect(self.updateLastSavedOrder)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.started.connect(self.worker.run)
        self.thread.finished.connect(self.reset_get_order_button)

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

    def reset_get_order_button(self):
        self.is_fetching = False
        self.spinner_movie.stop()
        self.spinner_label.hide()
        self.getOrderBtn.setText("GET ORDER")
        self.getOrderBtn.setEnabled(True)
        self.selectDirectoryBtn.setEnabled(True)
        self.newOrderLAB.setText(f'New orders: 0')


# Start the application
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    app.setWindowIcon(QtGui.QIcon("./asset/greetabl_g.png"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
