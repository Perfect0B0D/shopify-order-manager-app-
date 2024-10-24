import os
import json

# Constants
CONFIG_FILE = 'config.json'
DEFAULT_ORDER_DATA_DIR = os.path.join(os.getcwd(), 'OrderData')


class ConfigManager:
    
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as file:
                    return json.load(file)
            except (FileNotFoundError, json.JSONDecodeError):
                print(f"Invalid JSON in {self.config_file}, reinitializing...")
        return self.initialize_config()

    def initialize_config(self):

        config = {
            'OrderData_Directory': DEFAULT_ORDER_DATA_DIR,
            'last_saved_order_number': 0
        }
        self.save_config(config)
        return config

    def save_config(self, config):

        with open(self.config_file, 'w') as file:
            json.dump(config, file, indent=4)

    def get_order_data_directory(self):

        return self.config.get('OrderData_Directory', DEFAULT_ORDER_DATA_DIR)

    def get_last_saved_order_number(self):
        return self.config.get('last_saved_order_number', 0)

    def update_order_data_directory(self, path):
        self.config['OrderData_Directory'] = path
        self.save_config(self.config)

    def update_last_saved_order_number(self, order_number):
        self.config['last_saved_order_number'] = order_number
        self.save_config(self.config)
