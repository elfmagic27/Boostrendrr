import uuid
import time

def _get_db():
    import db
    return db

def main_menu():
    while True:
        print("\n1. Generate Key")
        print("2. List Keys")
        print("3. Delete Key")
        print("4. Clear All Keys")
        print("5. Exit")
        choice = input("Enter your choice: ")
        handle_choice(choice)

def handle_choice(choice):
    if choice == "1":
        handle_key_generation()
    elif choice == "2":
        handle_list_keys()
    elif choice == "3":
        handle_delete_key()
    elif choice == "4":
        handle_clear_file()
    elif choice == "5":
        print("Exiting program.")
        exit()
    else:
        print("Invalid choice. Please try again.")

def handle_key_generation():
    month = int(input("Enter month (e.g., 1 or 3): "))
    amount = int(input("Enter amount: "))
    quantity = int(input("Enter quantity of keys: "))
    keys = load_keys_from_file(None)
    generate_key(keys, month, amount, quantity, None)

def handle_list_keys():
    keys = load_keys_from_file(None)
    print("All Keys:", list_keys(keys))

def handle_delete_key():
    key_to_delete = input("Enter the key to delete: ")
    delete_key(None, key_to_delete)
    print("Key deleted.")

def handle_clear_file():
    clear_file(None)
    print("Keys cleared.")

def load_keys_from_file(file_path):
    try:
        return _get_db().load_keys()
    except Exception:
        return []

def save_keys_to_file(keys, file_path):
    _get_db().save_keys(keys)

def generate_key(keys, month, amount, quantity, file_path):
    import secrets as _sec
    new_keys = []
    for _ in range(quantity):
        k = f"BOOST-{''.join(_sec.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))}-{''.join(_sec.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))}-{''.join(_sec.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))}"
        new_keys.append({"key": k, "month": month, "amount": amount})
    _get_db().add_keys_bulk(new_keys)
    return new_keys

def list_keys(keys):
    return keys

def delete_key(keys, key):
    _get_db().delete_key_entry(key)

def clear_file(file_path):
    _get_db().clear_all_keys()

def exit_program():
    print("Exiting program.")
    exit()

if __name__ == "__main__":
    main_menu()
