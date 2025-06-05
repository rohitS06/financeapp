import sqlite3
import hashlib
import getpass
from datetime import datetime


class Database:
    def __init__(self, db_name="financedb.db"):
        self.db_name = db_name
        self.connection = sqlite3.connect(self.db_name)
        print(f"Database connected at: {self.db_name}")
        self.cursor = self.connection.cursor()
        self.create_user_table()
        self.create_transactions_table()
        self.create_budgets_table()

    def create_user_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        """)
        self.connection.commit()

    def create_transactions_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                amount REAL,
                date TEXT NOT NULL,
                type TEXT,
                category TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        self.connection.commit()

    def create_budgets_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                category TEXT,
                amount REAL,
                month TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)
        self.connection.commit()

    def close(self):
        self.connection.close()


def register_user(db, username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        db.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        db.connection.commit()
        print("User registered successfully.")
    except sqlite3.IntegrityError:
        print("Username already exists. Please try another.")


def authenticate(db, username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    db.cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = db.cursor.fetchone()
    if user:
        print(f"Welcome {username}!")
        return user[0]  # user_id
    else:
        print("Authentication failed.")
        return None


def add_transaction(db, user_id, amount, trans_type, category):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.cursor.execute("""
        INSERT INTO transactions (user_id, amount, type, category, date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, trans_type, category, date))
    db.connection.commit()
    print("Transaction added.")


def update_transaction(db, transaction_id, amount, trans_type, category):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.cursor.execute("""
        UPDATE transactions
        SET amount = ?, type = ?, category = ?, date = ?
        WHERE id = ?
    """, (amount, trans_type, category, date, transaction_id))
    db.connection.commit()
    print("Transaction updated.")


def delete_transaction(db, transaction_id):
    db.cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    db.connection.commit()
    print("Transaction deleted.")


def view_transactions(db, user_id):
    db.cursor.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
    transactions = db.cursor.fetchall()
    if transactions:
        for tx in transactions:
            print(f"ID: {tx[0]}, Amount: {tx[2]}, Type: {tx[4]}, Category: {tx[5]}, Date: {tx[3]}")
    else:
        print("No transactions found.")


def monthly_report(db, user_id):
    db.cursor.execute("""
        SELECT strftime('%Y-%m', date) AS month,
               SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
               SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
        FROM transactions
        WHERE user_id = ?
        GROUP BY month
        ORDER BY month DESC
    """, (user_id,))
    reports = db.cursor.fetchall()
    for month, income, expense in reports:
        savings = income - expense
        print(f"Month: {month}, Income: {income}, Expense: {expense}, Savings: {savings}")


def yearly_report(db, user_id):
    db.cursor.execute("""
        SELECT strftime('%Y', date) AS year,
               SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
               SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expense
        FROM transactions
        WHERE user_id = ?
        GROUP BY year
        ORDER BY year DESC
    """, (user_id,))
    reports = db.cursor.fetchall()
    for year, income, expense in reports:
        savings = income - expense
        print(f"Year: {year}, Income: {income}, Expense: {expense}, Savings: {savings}")


def set_budget(db, user_id, amount, category, month):
    db.cursor.execute("""
        INSERT OR REPLACE INTO budgets (user_id, category, amount, month)
        VALUES (?, ?, ?, ?)
    """, (user_id, category, amount, month))
    db.connection.commit()
    print(f"Budget set for {month} in category {category}.")


def check_budget(db, user_id, category, month):
    db.cursor.execute("""
        SELECT amount FROM budgets WHERE user_id = ? AND category = ? AND month = ?
    """, (user_id, category, month))
    budget = db.cursor.fetchone()

    if not budget:
        print("No budget set for this category and month.")
        return

    budget_amount = budget[0]
    db.cursor.execute("""
        SELECT SUM(amount) FROM transactions
        WHERE user_id = ? AND category = ? AND strftime('%Y-%m', date) = ?
        AND type = 'expense'
    """, (user_id, category, month))
    total_spent = db.cursor.fetchone()[0] or 0

    remaining = budget_amount - total_spent
    print(f"Budget for {category} in {month}: {budget_amount}, Spent: {total_spent}, Remaining: {remaining}")


def main():
    db = Database()
    user_id = None

    while True:
        print("\n==== Finance App Menu ====")
        print("1. Register")
        print("2. Login")
        print("3. Add Transaction")
        print("4. View Transactions")
        print("5. Update Transaction")
        print("6. Delete Transaction")
        print("7. Monthly Report")
        print("8. Yearly Report")
        print("9. Set Budget")
        print("10. Check Budget")
        print("11. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            register_user(db, username, password)

        elif choice == "2":
            username = input("Username: ")
            password = getpass.getpass("Password: ")
            user_id = authenticate(db, username, password)

        elif choice == "3" and user_id:
            try:
                amount = float(input("Amount: "))
                trans_type = input("Type (income/expense): ").strip().lower()
                category = input("Category: ")
                add_transaction(db, user_id, amount, trans_type, category)
            except ValueError:
                print("Invalid input for amount.")

        elif choice == "4" and user_id:
            view_transactions(db, user_id)

        elif choice == "5" and user_id:
            try:
                transaction_id = int(input("Transaction ID: "))
                amount = float(input("New Amount: "))
                trans_type = input("New Type: ")
                category = input("New Category: ")
                update_transaction(db, transaction_id, amount, trans_type, category)
            except ValueError:
                print("Invalid input.")

        elif choice == "6" and user_id:
            try:
                transaction_id = int(input("Transaction ID to delete: "))
                delete_transaction(db, transaction_id)
            except ValueError:
                print("Invalid transaction ID.")

        elif choice == "7" and user_id:
            monthly_report(db, user_id)

        elif choice == "8" and user_id:
            yearly_report(db, user_id)

        elif choice == "9" and user_id:
            category = input("Category: ")
            month = input("Month (YYYY-MM): ")
            try:
                amount = float(input("Budget Amount: "))
                set_budget(db, user_id, amount, category, month)
            except ValueError:
                print("Invalid amount.")

        elif choice == "10" and user_id:
            category = input("Category: ")
            month = input("Month (YYYY-MM): ")
            check_budget(db, user_id, category, month)

        elif choice == "11":
            db.close()
            print("Thank you for using Finance App!")
            break

        else:
            print("Invalid choice or please login first.")


if __name__ == "__main__":
    main()
