from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Static, Select, Markdown
from textual import events # Added import for events
import pyperclip # Import pyperclip

# Assuming these modules are in the same directory or accessible
# and their methods are suitable for use in a non-CLI context.
# Adjust imports as necessary based on your project structure.
try:
    from CheckSQL import sql_injection_check as check
    from Users import User
    from Staffs import Staff, Manager, Admin
    from People import generate as generate_person # Added import
    import mariadb
    import hashlib # Import for SHA-512
except ImportError as e:
    print(f"Error importing necessary modules: {e}")
    print("Please ensure CheckSQL.py, Users.py, and Staffs.py are in the correct path.")
    # In a real TUI, you might show this on an error screen.
    exit(1)

# --- Database Connection (Consider refactoring to a separate module) ---
def get_db_connection_details():
    # In a real app, these might come from a config file
    return {"user": "Staff", "passwd": "Staff@Bank", "database": "Banking"}

# --- Screens ---

class LoginChoiceScreen(Screen):
    """Screen to choose between User and Staff portal."""

    def compose(self) -> ComposeResult:
        yield Header(name="Bankify TUI")
        yield Footer()
        with Vertical(id="login-choice-container", classes="screen-container"):
            yield Label("Welcome to Bankify", id="welcome-label")
            yield Button("User Portal", id="user-portal-button", variant="primary")
            yield Button("Staff Portal", id="staff-portal-button", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.app.log(f"LoginChoiceScreen: Button '{event.button.id}' pressed.")
        if event.button.id == "user-portal-button":
            self.app.push_screen(UserLoginScreen())
        elif event.button.id == "staff-portal-button":
            self.app.push_screen(StaffLoginScreen())


class UserLoginScreen(Screen):
    """Screen for user login."""
    
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(name="User Login")
        yield Footer()
        with Vertical(id="user-login-form", classes="form-container"):
            yield Label("User ID:")
            yield Input(placeholder="Enter your User ID", id="user_id_input")
            yield Label("Password:")
            yield Input(placeholder="Enter your password", password=True, id="user_password_input")
            yield Button("Login", id="user-login-button", variant="success")
            yield Static(id="user-login-status", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user-login-button":
            user_id_input = self.query_one("#user_id_input", Input)
            password_input = self.query_one("#user_password_input", Input)
            status_label = self.query_one("#user-login-status", Static)

            user_id = user_id_input.value
            password = password_input.value

            if not user_id or not password:
                status_label.update("[b red]User ID and Password cannot be empty.[/b red]")
                self.app.log.warning("User login attempt with empty fields.")
                return

            try:
                self.app.log(f"Attempting user login for User ID: {user_id}")
                current_user = User(user_id, password)
                self.app.user_session = current_user
                self.app.log(f"User '{user_id}' logged in successfully.")
                self.app.push_screen(UserPortalScreen())
                status_label.update("") 
            except Exception as e:
                self.app.log.error(f"User login failed for User ID '{user_id}': {e}")
                status_label.update(f"[b red]Login error: {e}. Check credentials or user existence.[/b red]")


class StaffLoginScreen(Screen):
    """Screen for staff login."""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(name="Staff Login")
        yield Footer()
        with Vertical(id="staff-login-form", classes="form-container"):
            yield Label("Staff ID:")
            yield Input(placeholder="Enter your Staff ID", id="staff_id_input")
            yield Label("Password:")
            yield Input(placeholder="Enter your password", password=True, id="staff_password_input")
            yield Button("Login", id="staff-login-button", variant="success")
            yield Static(id="staff-login-status", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "staff-login-button":
            staff_id_input = self.query_one("#staff_id_input", Input)
            password_input = self.query_one("#staff_password_input", Input)
            status_label = self.query_one("#staff-login-status", Static)

            staff_id = staff_id_input.value
            password = password_input.value

            if not staff_id or not password:
                status_label.update("[b red]Staff ID and Password cannot be empty.[/b red]")
                self.app.log.warning("Staff login attempt with empty fields.")
                return

            current_staff = None
            try:
                self.app.log(f"Attempting staff login for Staff ID: {staff_id}")
                db_config = get_db_connection_details()
                conn = mariadb.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("SELECT Type FROM Staff WHERE ID = %s", (staff_id,))
                result = cursor.fetchone()
                
                if result:
                    staff_type = result[0]
                    if staff_type == 0:
                        current_staff = Staff(staff_id, password)
                    elif staff_type == 1:
                        current_staff = Manager(staff_id, password)
                    elif staff_type == 2:
                        current_staff = Admin(staff_id, password)
                    else:
                        status_label.update(f"[b red]Invalid staff type: {staff_type}.[/b red]")
                        conn.close()
                        return
                    
                    if current_staff:
                        self.app.staff_session = current_staff
                        self.app.log(f"Staff '{staff_id}' logged in successfully as type {staff_type}.")
                        self.app.push_screen(StaffPortalScreen())
                        status_label.update("")
                    else: 
                        self.app.log.error(f"Failed to initialize staff object for Staff ID '{staff_id}'.")
                        status_label.update("[b red]Failed to initialize staff object. Password might be incorrect.[/b red]")
                else:
                    self.app.log.warning(f"Invalid Staff ID '{staff_id}' on login attempt.")
                    status_label.update("[b red]Invalid Staff ID.[/b red]")
                if conn: conn.close()
            except mariadb.Error as e:
                self.app.log.error(f"Database error during staff login for '{staff_id}': {e}")
                status_label.update(f"[b red]Database error: {e}[/b red]")
            except ValueError as e: # Catch specific error from Staffs.py for bad password
                 self.app.log.error(f"Staff login failed for Staff ID '{staff_id}': {e}")
                 status_label.update(f"[b red]Login error: {e}. Check credentials.[/b red]")
            except Exception as e: 
                self.app.log.error(f"Unexpected error during staff login for Staff ID '{staff_id}': {e}")
                status_label.update(f"[b red]An unexpected error occurred: {e}[/b red]")


class CreateAccountScreen(Screen):
    """Screen for a user to create a new bank account."""

    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(name="Create New Bank Account")
        yield Footer()
        with Vertical(id="create-account-form", classes="form-container"):
            yield Label("New Account Password:")
            yield Input(placeholder="Enter password for the new account", password=True, id="new_account_password_input")
            yield Button("Create Account", id="create-account-button", variant="success")
            yield Static(id="create-account-status", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-account-button":
            password_input = self.query_one("#new_account_password_input", Input)
            status_label = self.query_one("#create-account-status", Static)
            new_password = password_input.value

            if not new_password:
                status_label.update("[b red]Password cannot be empty.[/b red]")
                self.app.log.warning("Create account attempt with empty password.")
                return

            if not self.app.user_session:
                status_label.update("[b red]Error: No active user session.[/b red]")
                self.app.log.error("Create account attempt with no active user session.")
                return

            try:
                self.app.log(f"User '{self.app.user_session.user_id}' attempting to create a new account.")
                self.app.user_session.create_account(new_password)
                status_label.update("[b green]Account creation request submitted successfully! It may require staff approval.[/b green]")
                self.app.log.info(f"Account creation request submitted by user '{self.app.user_session.user_id}'.")
                password_input.value = "" 
            except Exception as e:
                self.app.log.error(f"Account creation failed for user '{self.app.user_session.user_id}': {e}")
                status_label.update(f"[b red]Error creating account: {e}[/b red]")


class SelectAccountScreen(Screen):
    """Screen for user to select an account and enter password to log in."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    accounts_list = reactive([])
    selected_account_id = reactive(None)

    def on_mount(self) -> None:
        if not self.app.user_session:
            self.app.log.warning("SelectAccountScreen mounted without user session. Popping.")
            self.app.pop_screen()
            return
        self.app.user_session.get_accounts() 
        self.accounts_list = self.app.user_session.accounts
        self.app.log.info(f"SelectAccountScreen: User '{self.app.user_session.user_id}' has accounts: {self.accounts_list}")
        account_options = [(str(acc_id), str(acc_id)) for acc_id in self.accounts_list] # Ensure string keys
        select_widget = self.query_one(Select)
        select_widget.set_options(account_options)
        if account_options:
            select_widget.value = account_options[0][1] 
            self.selected_account_id = account_options[0][1]

    def compose(self) -> ComposeResult:
        yield Header(name="Log In to Account")
        yield Footer()
        with Vertical(id="select-account-form", classes="form-container"):
            yield Label("Select Account:")
            yield Select([], id="account_select")
            yield Label("Account Password:")
            yield Input(placeholder="Enter password for selected account", password=True, id="account_password_input")
            yield Button("Login to Account", id="login-to-account-button", variant="success")
            yield Static(id="select-account-status", classes="status-message")

    def on_select_changed(self, event: Select.Changed) -> None:
        self.selected_account_id = str(event.value) # Ensure it's a string
        self.app.log.info(f"Account selected: {self.selected_account_id}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-to-account-button":
            password_input = self.query_one("#account_password_input", Input)
            status_label = self.query_one("#select-account-status", Static)
            account_password = password_input.value

            if not self.selected_account_id:
                status_label.update("[b red]Please select an account.[/b red]")
                return
            if not account_password:
                status_label.update("[b red]Password cannot be empty.[/b red]")
                return
            if not self.app.user_session:
                status_label.update("[b red]Error: No active user session.[/b red]")
                return

            try:
                self.app.log.info(f"User '{self.app.user_session.user_id}' attempting to log into account '{self.selected_account_id}'.")
                login_success = self.app.user_session.login_account(self.selected_account_id, account_password)
                if login_success:
                    self.app.log.info(f"Successfully logged into account '{self.selected_account_id}'.")
                    self.app.push_screen(UserBankAccountScreen(self.selected_account_id))
                    status_label.update("")
                else:
                    self.app.log.warning(f"Failed to log into account '{self.selected_account_id}'. Invalid password or account issue.")
                    status_label.update("[b red]Login failed. Check password or account status (it might need staff approval if new).[/b red]")
            except Exception as e:
                self.app.log.error(f"Error logging into account '{self.selected_account_id}': {e}")
                status_label.update(f"[b red]Error: {e}[/b red]")


class TransactionScreen(Screen):
    """Screen for handling withdrawals and deposits."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    def __init__(self, transaction_type: int, account_id: str, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.transaction_type = transaction_type
        self.account_id = account_id
        self.transaction_name = "Withdraw" if transaction_type == 0 else "Deposit"

    def compose(self) -> ComposeResult:
        yield Header(name=f"{self.transaction_name} Money (Account: {self.account_id})")
        yield Footer()
        with Vertical(id="transaction-form", classes="form-container"):
            yield Label(f"Amount to {self.transaction_name.lower()}:")
            yield Input(placeholder="Enter amount", id="transaction_amount_input", type="number")
            yield Button(f"Confirm {self.transaction_name}", id="confirm-transaction-button", variant="success")
            yield Static(id="transaction-status", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-transaction-button":
            amount_input_widget = self.query_one("#transaction_amount_input", Input)
            status_label = self.query_one("#transaction-status", Static)
            amount_str = amount_input_widget.value
            if not amount_str:
                status_label.update("[b red]Amount cannot be empty.[/b red]")
                return
            try:
                amount = float(amount_str)
                if amount <= 0:
                    status_label.update("[b red]Amount must be positive.[/b red]")
                    return
            except ValueError:
                status_label.update("[b red]Invalid amount entered.[/b red]")
                return
            if not self.app.user_session or not self.app.user_session.current_account:
                status_label.update("[b red]Error: No active bank account session.[/b red]")
                return
            if self.app.user_session.current_account.account_id != self.account_id:
                status_label.update("[b red]Error: Account mismatch.[/b red]")
                return
            try:
                self.app.log.info(f"User '{self.app.user_session.user_id}' attempting to {self.transaction_name.lower()} ${amount:.2f} from account '{self.account_id}'.")
                # The commit_transaction in Accounts.py returns a tuple (bool, Optional[str])
                # or just bool based on the latest version. Assuming it returns just bool for success.
                # Let's adjust based on the actual return type if it causes issues.
                result = self.app.user_session.current_account.commit_transaction(amount, self.transaction_type)
                
                success = False
                error_message = "Transaction failed due to an unknown issue."
                if isinstance(result, tuple):
                    success = result[0]
                    if len(result) > 1 and result[1]: # If there's an error message string
                        error_message = result[1]
                elif isinstance(result, bool):
                    success = result

                if success:
                    status_label.update(f"[b green]{self.transaction_name} of ${amount:.2f} successful![/b green]")
                    self.app.log.info(f"{self.transaction_name} of ${amount:.2f} successful for account '{self.account_id}'.")
                    amount_input_widget.value = "" 
                    self.dismiss(True) # Changed from self.app.post_message(self.PopScreen(result=True))
                else:
                    # Construct a more specific error message if possible
                    if self.transaction_type == 0 and not error_message: # Withdrawal
                         # Check balance if error_message wasn't specific from commit_transaction
                        if hasattr(self.app.user_session.current_account, 'balance') and amount > self.app.user_session.current_account.balance:
                            error_message = "Insufficient funds."
                        else:
                            error_message = "Withdrawal failed. Please check details or try again."
                    elif not error_message: # Deposit or other
                        error_message = f"{self.transaction_name} failed. Please try again."
                    
                    status_label.update(f"[b red]{error_message}[/b red]")
                    self.app.log.warning(f"{self.transaction_name} of ${amount:.2f} failed for account '{self.account_id}'. Message: {error_message}")
            except Exception as e:
                self.app.log.error(f"Error during {self.transaction_name.lower()} for account '{self.account_id}': {e}")
                status_label.update(f"[b red]Error: {e}[/b red]")


class TransferMoneyScreen(Screen):
    """Screen for transferring money to another account."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def __init__(self, account_id: str, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.account_id = account_id

    def compose(self) -> ComposeResult:
        yield Header(name=f"Transfer Money (From Account: {self.account_id})")
        yield Footer()
        with Vertical(id="transfer-money-form", classes="form-container"):
            yield Label("Recipient Account ID:")
            yield Input(placeholder="Enter recipient's account ID", id="recipient_account_id_input")
            yield Label("Amount to Transfer:")
            yield Input(placeholder="Enter amount", id="transfer_amount_input", type="number")
            yield Button("Confirm Transfer", id="confirm-transfer-button", variant="success")
            yield Static(id="transfer-money-status", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-transfer-button":
            recipient_id_input = self.query_one("#recipient_account_id_input", Input)
            amount_input_widget = self.query_one("#transfer_amount_input", Input)
            status_label = self.query_one("#transfer-money-status", Static)
            recipient_account_id = recipient_id_input.value
            amount_str = amount_input_widget.value
            if not recipient_account_id:
                status_label.update("[b red]Recipient Account ID cannot be empty.[/b red]")
                return
            if not amount_str:
                status_label.update("[b red]Amount cannot be empty.[/b red]")
                return
            try:
                amount = float(amount_str)
                if amount <= 0:
                    status_label.update("[b red]Amount must be positive.[/b red]")
                    return
            except ValueError:
                status_label.update("[b red]Invalid amount entered.[/b red]")
                return
            if not self.app.user_session or not self.app.user_session.current_account:
                status_label.update("[b red]Error: No active bank account session.[/b red]")
                return
            if self.app.user_session.current_account.account_id != self.account_id:
                status_label.update("[b red]Error: Source account mismatch.[/b red]")
                return
            try:
                self.app.log.info(f"User '{self.app.user_session.user_id}' attempting to transfer ${amount:.2f} from '{self.account_id}' to '{recipient_account_id}'.")
                success = self.app.user_session.current_account.send_money(recipient_account_id, amount)
                if success:
                    status_label.update(f"[b green]Transfer of ${amount:.2f} to {recipient_account_id} successful![/b green]")
                    self.app.log.info(f"Transfer successful for account '{self.account_id}'.")
                    amount_input_widget.value = ""
                    recipient_id_input.value = ""
                    self.dismiss(True) # Changed from self.app.post_message(self.PopScreen(result=True))
                else:
                    status_label.update("[b red]Transfer failed. Check recipient ID, funds, or recipient account may not exist.[/b red]")
                    self.app.log.warning(f"Transfer of ${amount:.2f} from '{self.account_id}' to '{recipient_account_id}' failed.")
            except Exception as e:
                self.app.log.error(f"Error during transfer from account '{self.account_id}': {e}")
                status_label.update(f"[b red]Error: {e}[/b red]")


class DeleteAccountScreen(Screen):
    """Screen for a user to delete one of their bank accounts."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    accounts_list = reactive([])
    other_user_accounts_list = reactive([]) # For the dropdown of user's other accounts
    selected_account_to_delete = reactive(None)
    transfer_to_own_account = reactive(False) # New reactive var to track transfer choice

    def on_mount(self) -> None:
        if not self.app.user_session:
            self.app.log.warning("DeleteAccountScreen mounted without user session. Popping.")
            self.app.pop_screen()
            return
        
        self.app.user_session.get_accounts() 
        self.accounts_list = self.app.user_session.accounts
        self.app.log.info(f"DeleteAccountScreen: User '{self.app.user_session.user_id}' has accounts: {self.accounts_list}")
        
        account_options = [(str(acc_id), str(acc_id)) for acc_id in self.accounts_list]
        delete_select_widget = self.query_one("#delete_account_select", Select)
        delete_select_widget.set_options(account_options)
        
        # Populate the 'transfer to own account' dropdown
        # Initially, this will be empty until an account to delete is selected
        self.update_transfer_to_own_account_dropdown()

        if account_options:
            delete_select_widget.value = account_options[0][1]
            self.selected_account_to_delete = account_options[0][1]
            self.update_form_state(enabled=True)
            self.update_transfer_to_own_account_dropdown() # Update based on initial selection
        else:
            self.update_form_state(enabled=False)
            self.query_one("#delete-account-status", Static).update("[b yellow]You have no accounts to delete.[/b yellow]")

    def update_form_state(self, enabled: bool) -> None:
        """Enable or disable form elements."""
        self.query_one("#delete_account_password_input", Input).disabled = not enabled
        self.query_one("#transfer_to_own_checkbox", Button).disabled = not enabled # Assuming Checkbox is a Button or similar
        self.query_one("#delete_recipient_account_id_input", Input).disabled = not enabled or self.transfer_to_own_account
        self.query_one("#transfer_to_own_account_select", Select).disabled = not enabled or not self.transfer_to_own_account
        self.query_one("#delete_private_key_path_input", Input).disabled = not enabled
        self.query_one("#confirm-delete-account-button", Button).disabled = not enabled
        if not enabled:
            self.query_one("#delete-account-status", Static).update("[b yellow]You have no accounts to delete.[/b yellow]")
        else:
            self.query_one("#delete-account-status", Static).update("")

    def update_transfer_to_own_account_dropdown(self) -> None:
        """Populates the dropdown for transferring to one of the user's other accounts."""
        transfer_own_select_widget = self.query_one("#transfer_to_own_account_select", Select)
        if self.selected_account_to_delete and self.app.user_session:
            # Filter out the account being deleted from the list of own accounts
            self.other_user_accounts_list = [
                acc_id for acc_id in self.app.user_session.accounts 
                if acc_id != self.selected_account_to_delete
            ]
            own_account_options = [(str(acc_id), str(acc_id)) for acc_id in self.other_user_accounts_list]
            transfer_own_select_widget.set_options(own_account_options)
            if not own_account_options:
                transfer_own_select_widget.set_options([("(No other accounts available)", None)])
                transfer_own_select_widget.disabled = True
            else:
                transfer_own_select_widget.value = own_account_options[0][1] # Select first by default
                transfer_own_select_widget.disabled = not self.transfer_to_own_account # Enable only if checkbox is checked
        else:
            transfer_own_select_widget.set_options([("(Select account to delete first)", None)])
            transfer_own_select_widget.disabled = True

    def compose(self) -> ComposeResult:
        yield Header(name="Delete Bank Account")
        yield Footer()
        with Vertical(id="delete-account-form", classes="form-container"):
            yield Label("Select Account to Delete:")
            yield Select([], id="delete_account_select")
            yield Label("Account Password:")
            yield Input(placeholder="Enter password for the account to delete", password=True, id="delete_account_password_input")
            
            yield Label("Transfer remaining funds to:")
            # Using a Button as a makeshift checkbox for simplicity in Textual if Checkbox widget isn't directly used or for styling
            yield Button("Transfer to one of my other accounts? (Click to toggle)", id="transfer_to_own_checkbox")
            
            yield Label("Select one of your other accounts (if applicable):")
            yield Select([], id="transfer_to_own_account_select", disabled=True) 
            
            yield Label("Or, enter external Recipient Account ID:")
            yield Input(placeholder="Enter external recipient's account ID", id="delete_recipient_account_id_input")
            
            yield Label("Path to your Private Key File:")
            yield Input(placeholder="/path/to/your/private_key.pem", id="delete_private_key_path_input")
            yield Label("[b red]WARNING: This action is irreversible and will transfer all funds.[/b red]")
            yield Button("Confirm Deletion", id="confirm-delete-account-button", variant="error")
            yield Static(id="delete-account-status", classes="status-message")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "delete_account_select":
            self.selected_account_to_delete = str(event.value) if event.value else None
            self.app.log.info(f"Account selected for deletion: {self.selected_account_to_delete}")
            self.update_transfer_to_own_account_dropdown() # Update dependent dropdown
            # Also re-evaluate disabled state of recipient input if checkbox is not checked
            self.query_one("#delete_recipient_account_id_input", Input).disabled = self.transfer_to_own_account

        # No need to handle change for transfer_to_own_account_select here for now,
        # its value will be read directly on submission.

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        status_label = self.query_one("#delete-account-status", Static)

        if event.button.id == "transfer_to_own_checkbox":
            self.transfer_to_own_account = not self.transfer_to_own_account
            self.app.log.info(f"Transfer to own account toggled: {self.transfer_to_own_account}")
            # Enable/disable relevant inputs based on the toggle
            self.query_one("#transfer_to_own_account_select", Select).disabled = not self.transfer_to_own_account
            self.query_one("#delete_recipient_account_id_input", Input).disabled = self.transfer_to_own_account
            if self.transfer_to_own_account:
                self.query_one("#delete_recipient_account_id_input", Input).value = "" # Clear external if own is chosen
                status_label.update("Select one of your other accounts above.")
            else:
                status_label.update("Enter external recipient account ID below.")
            return # Handled toggle, no further action on this button press

        if event.button.id == "confirm-delete-account-button":
            password_input = self.query_one("#delete_account_password_input", Input)
            private_key_path_input = self.query_one("#delete_private_key_path_input", Input)
            
            recipient_account_id = ""
            if self.transfer_to_own_account:
                own_account_select = self.query_one("#transfer_to_own_account_select", Select)
                if own_account_select.value is None or not self.other_user_accounts_list:
                    status_label.update("[b red]Please select one of your other accounts to transfer funds to, or untoggle the option.[/b red]")
                    return
                recipient_account_id = str(own_account_select.value)
            else:
                recipient_id_input_external = self.query_one("#delete_recipient_account_id_input", Input)
                recipient_account_id = recipient_id_input_external.value

            account_to_delete = self.selected_account_to_delete
            password = password_input.value
            private_key_path = private_key_path_input.value

            if not account_to_delete:
                status_label.update("[b red]Please select an account to delete.[/b red]")
                return
            if not password:
                status_label.update("[b red]Account password cannot be empty.[/b red]")
                return
            if not recipient_account_id:
                status_label.update("[b red]Recipient Account ID (either from your accounts or external) cannot be empty.[/b red]")
                return
            if not private_key_path:
                status_label.update("[b red]Private key file path cannot be empty.[/b red]")
                return
            if not self.app.user_session:
                status_label.update("[b red]Error: No active user session.[/b red]")
                return

            try:
                with open(private_key_path, 'r') as pk_file:
                    self.app.log.info(f"User '{self.app.user_session.user_id}' attempting to delete account '{account_to_delete}', transferring funds to '{recipient_account_id}'.")
                    
                    # Confirm transfer if recipient is not one of the user's own accounts
                    # This logic might need adjustment based on how Users.py handles it.
                    # If transfer_to_own_account is true, confirm should likely be false.
                    confirm_transfer = not self.transfer_to_own_account
                    
                    success = self.app.user_session.delete_account(
                        account_to_delete, 
                        password, 
                        recipient_account_id, 
                        pk_file,
                        confirm=confirm_transfer 
                    )
                
                if success:
                    status_label.update(f"[b green]Account '{account_to_delete}' deleted successfully. Funds transferred to '{recipient_account_id}'.[/b green]")
                    self.app.log.info(f"Account '{account_to_delete}' deleted by user '{self.app.user_session.user_id}'.")
                    password_input.value = ""
                    private_key_path_input.value = ""
                    if not self.transfer_to_own_account:
                         self.query_one("#delete_recipient_account_id_input", Input).value = ""
                    self.on_mount() # Refresh account list and form state
                else:
                    status_label.update(f"[b red]Failed to delete account '{account_to_delete}'. Check details, password, key, or recipient account. The private key might be incorrect or the recipient account may not exist.[/b red]")
                    self.app.log.warning(f"Account deletion failed for user '{self.app.user_session.user_id}', account '{account_to_delete}'. Underlying method returned False.")

            except FileNotFoundError:
                self.app.log.error(f"Private key file not found at path: {private_key_path}")
                status_label.update(f"[b red]Error: Private key file not found at '{private_key_path}'.[/b red]")
            except Exception as e:
                self.app.log.error(f"Error during account deletion for user '{self.app.user_session.user_id}', account '{account_to_delete}': {e}")
                status_label.update(f"[b red]Error deleting account: {e}[/b red]")


class UserBankAccountScreen(Screen):
    """Screen for managing a logged-in bank account."""
    BINDINGS = [("escape", "logout_from_account", "Logout from Account")]
    current_account_id = reactive(None)
    current_balance = reactive(0.0)

    def __init__(self, account_id: str, name: str | None = None, id: str | None = None, classes: str | None = None) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.current_account_id = account_id

    def on_mount(self) -> None:
        if not self.app.user_session or not self.app.user_session.current_account:
            self.app.log.warning("UserBankAccountScreen mounted without active bank account session. Popping.")
            self.app.pop_screen()
            return
        if self.app.user_session.current_account.account_id != self.current_account_id:
            self.app.log.error(f"Account ID mismatch: expected {self.current_account_id}, but current_account is {self.app.user_session.current_account.account_id}. Popping.")
            self.app.pop_screen()
            return
        self.app.log.info(f"UserBankAccountScreen mounted for account '{self.current_account_id}'.")
        self.refresh_balance()

    def _update_balance_display(self) -> None:
        balance_label = self.query_one("#account_balance_display", Static)
        balance_label.update(f"Current Balance: [b green]${self.current_balance:.2f}[/b green]")

    def refresh_balance(self) -> None:
        status_label = self.query_one("#bank_account_status", Static)
        if self.app.user_session and self.app.user_session.current_account:
            try:
                self.current_balance = self.app.user_session.current_account.get_balance()
                self._update_balance_display()
                self.app.log.info(f"Balance refreshed for account '{self.current_account_id}': ${self.current_balance:.2f}")
                status_label.update("[b sky_blue2]Balance refreshed.[/b sky_blue2]")
            except Exception as e:
                self.app.log.error(f"Error refreshing balance for account '{self.current_account_id}': {e}")
                status_label.update(f"[b red]Error refreshing balance: {e}[/b red]")
        else:
            status_label.update("[b red]Cannot refresh balance: No active account session.[/b red]")

    def compose(self) -> ComposeResult:
        yield Header(name=f"Account: {self.current_account_id}")
        yield Footer()
        with Vertical(classes="portal-container"):
            yield Static(f"Account ID: {self.current_account_id}", classes="placeholder-text")
            yield Static(f"Current Balance: [b green]${self.current_balance:.2f}[/b green]", id="account_balance_display")
            yield Button("Withdraw Money", id="account_withdraw", variant="primary") 
            yield Button("Deposit Money", id="account_deposit", variant="primary") 
            yield Button("Transfer Money", id="account_transfer", variant="primary") 
            yield Button("Refresh Balance", id="account_refresh_balance", variant="default")
            yield Button("Logout from Account", id="account_logout", variant="error")
            yield Static(id="bank_account_status", classes="status-message") # Added missing status label


    def action_logout_from_account(self) -> None:
        self.app.log.info(f"Logging out from account '{self.current_account_id}' and user session.")
        if self.app.user_session:
            # Clear current account specific session part
            if hasattr(self.app.user_session, 'logout_account'):
                self.app.user_session.logout_account() # This should set current_account to None
                self.app.log.info(f"Called user_session.logout_account() for account '{self.current_account_id}'.")
            else: # Fallback
                self.app.user_session.current_account = None
                self.app.log.info(f"Set user_session.current_account to None for account '{self.current_account_id}'.")
            
            # Clear entire user session
            self.app.log.info(f"Also logging out user '{self.app.user_session.user_id}'.")
            self.app.user_session = None
        else:
            self.app.log.info("action_logout_from_account: No active user session to clear.")

        # Replace the entire screen stack with LoginChoiceScreen
        self.app.switch_screen(LoginChoiceScreen())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        status_label = self.query_one("#bank_account_status", Static)
        status_label.update("") # Clear previous status messages

        self.app.log.info(f"UserBankAccountScreen: Button '{event.button.id}' pressed for account '{self.current_account_id}'.")
        
        if not self.app.user_session or (event.button.id != "account_logout" and not self.app.user_session.current_account):
            if event.button.id != "account_logout": # Logout can proceed to clear session
                 status_label.update("[b red]Error: No active user or bank account session.[/b red]")
                 self.app.log.error(f"Action '{event.button.id}' attempted with no active session.")
                 return

        if event.button.id == "account_logout":
            self.action_logout_from_account()
        elif event.button.id == "account_refresh_balance":
            self.refresh_balance()
            # refresh_balance now updates its own status
        elif event.button.id == "account_withdraw":
            if self.app.user_session and self.app.user_session.current_account:
                self.app.push_screen(TransactionScreen(transaction_type=0, account_id=self.current_account_id))
            else:
                status_label.update("[b red]Error: No active bank account session for withdrawal.[/b red]")
                self.app.log.error("Withdraw attempt with no active bank account session.")
        elif event.button.id == "account_deposit":
            if self.app.user_session and self.app.user_session.current_account:
                self.app.push_screen(TransactionScreen(transaction_type=1, account_id=self.current_account_id))
            else:
                status_label.update("[b red]Error: No active bank account session for deposit.[/b red]")
                self.app.log.error("Deposit attempt with no active bank account session.")
        elif event.button.id == "account_transfer":
            if self.app.user_session and self.app.user_session.current_account:
                self.app.push_screen(TransferMoneyScreen(account_id=self.current_account_id))
            else:
                status_label.update("[b red]Error: No active bank account session for transfer.[/b red]")
                self.app.log.error("Transfer attempt with no active bank account session.")
        # No 'else' needed as all buttons are handled or covered by session check


class UserPortalScreen(Screen):
    """Main screen for logged-in users."""
    BINDINGS = [("escape", "logout_user", "Logout")]

    def compose(self) -> ComposeResult:
        yield Header(name="User Portal")
        yield Footer()
        user_id_display = "N/A"
        if self.app.user_session and hasattr(self.app.user_session, 'user_id'):
            user_id_display = self.app.user_session.user_id
        with Vertical(classes="portal-container"):
            yield Label(f"Welcome, User: {user_id_display}")
            yield Static("Choose an option below:", classes="placeholder-text")
            yield Button("Log in to one of your accounts", id="user_login_account", variant="primary")
            yield Button("Create a new account", id="user_create_account", variant="success") 
            yield Button("Delete an account", id="user_delete_account", variant="warning") # Enabled button, changed variant
            yield Button("Logout", id="user_logout_button", variant="error")
            yield Static(id="user_portal_status", classes="status-message")

    def on_mount(self) -> None:
        if not self.app.user_session:
            self.app.log.warning("UserPortalScreen mounted without active user session. Popping screen.")
            self.app.pop_screen() 
        else:
            self.app.log.info(f"UserPortalScreen mounted for user '{self.app.user_session.user_id}'.")
            # Refresh account count for enabling/disabling delete button logic if needed here
            # For now, the check is done in on_button_pressed

    def action_logout_user(self) -> None:
        if self.app.user_session:
            self.app.log.info(f"User '{self.app.user_session.user_id}' logging out.")
            self.app.user_session = None # Clear user session
        else:
            self.app.log.info("Logout action called with no active user session.")
        
        # Replace the entire screen stack with LoginChoiceScreen
        self.app.switch_screen(LoginChoiceScreen())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        status_label = self.query_one("#user_portal_status", Static)
        self.app.log.info(f"UserPortalScreen: Button '{event.button.id}' pressed by user '{self.app.user_session.user_id if self.app.user_session else 'Unknown'}'.")
        if event.button.id == "user_logout_button":
            self.action_logout_user()
        elif event.button.id == "user_create_account":
            self.app.push_screen(CreateAccountScreen())
            status_label.update("") 
        elif event.button.id == "user_login_account":
            if not self.app.user_session:
                status_label.update("[b red]Error: No active user session.[/b red]")
                return
            # Calling get_accounts() updates self.app.user_session.accounts and returns the count
            num_accounts = self.app.user_session.get_accounts() 
            if num_accounts == 0:
                status_label.update("[b yellow]You have no accounts. Please create one first.[/b yellow]")
                self.app.log.info(f"User '{self.app.user_session.user_id}' tried to log into account, but has none.")
            else:
                self.app.push_screen(SelectAccountScreen())
                status_label.update("")
        elif event.button.id == "user_delete_account":
            if not self.app.user_session:
                status_label.update("[b red]Error: No active user session.[/b red]")
                return
            # Calling get_accounts() updates self.app.user_session.accounts and returns the count
            num_accounts = self.app.user_session.get_accounts()
            if num_accounts == 0:
                status_label.update("[b yellow]You have no accounts to delete.[/b yellow]")
                self.app.log.info(f"User '{self.app.user_session.user_id}' tried to delete an account, but has none.")
            else:
                self.app.push_screen(DeleteAccountScreen())
                status_label.update("")
        else:
            status_label.update(f"[b yellow]Functionality for '{event.button.label}' not yet implemented.[/b yellow]")


class StaffCreateUserScreen(Screen):
    """Screen for staff to create a new user."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(name="Create New User")
        yield Footer()
        with Vertical(id="create-user-form", classes="form-container"):
            yield Label("People ID:")
            yield Input(placeholder="Enter People ID (from Add Person screen)", id="people_id_input")
            yield Label("New User ID:")
            yield Input(placeholder="Enter desired User ID (must be unique)", id="new_user_id_input")
            yield Label("Hashed Password for New User:")
            yield Input(placeholder="Enter SHA-512 hashed password", id="new_user_hashed_password_input")
            yield Button("Create User", id="create_user_button", variant="success")
            yield Static(id="create_user_status", classes="status-message")
            yield Markdown("""**Note:** You can use the 'Calculate SHA-512 Hash' 
            tool from the Staff Portal to generate the hashed password.""")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create_user_button":
            people_id_input = self.query_one("#people_id_input", Input)
            user_id_input = self.query_one("#new_user_id_input", Input)
            hashed_password_input = self.query_one("#new_user_hashed_password_input", Input)
            status_label = self.query_one("#create_user_status", Static)

            people_id = people_id_input.value
            user_id = user_id_input.value
            hashed_password = hashed_password_input.value

            if not people_id or not user_id or not hashed_password:
                status_label.update("[b red]All fields (People ID, User ID, Hashed Password) are required.[/b red]")
                return

            if not self.app.staff_session or not hasattr(self.app.staff_session, 'add_user'):
                status_label.update("[b red]Error: No active staff session or required method unavailable.[/b red]")
                self.app.log.error("Create user attempt with no/invalid staff session.")
                return

            try:
                self.app.log.info(f"Staff '{self.app.staff_session.user_id}' attempting to create user '{user_id}' for People ID '{people_id}'.")
                # add_user in Staffs.py should return a more informative tuple (bool, message_string)
                # For now, we assume it returns True on success, False on failure.
                # We will adapt if the backend method's return is changed.
                
                # The add_user method in Staffs.py was returning a boolean.
                # Let's assume it now might return a tuple (success_bool, message_str) or just bool.
                result = self.app.staff_session.add_user(people_id, user_id, hashed_password)
                
                success = False
                message = "User creation failed. Please check logs or details."

                if isinstance(result, tuple) and len(result) == 2:
                    success, message = result
                elif isinstance(result, bool):
                    success = result
                    if not success:
                        # Attempt to provide a more specific default message based on common errors
                        # This is a guess; the backend should ideally provide the specific reason.
                        # We can refine this if Staffs.py.add_user is updated to return detailed messages.
                        message = f"Failed to create user '{user_id}'. People ID '{people_id}' might not exist, or User ID '{user_id}' might already be taken."

                if success:
                    status_label.update(f"[b green]User '{user_id}' created successfully for People ID '{people_id}'![/b green]")
                    self.app.log.info(f"User '{user_id}' created by staff '{self.app.staff_session.user_id}'.")
                    # Clear fields on success
                    people_id_input.value = ""
                    user_id_input.value = ""
                    hashed_password_input.value = ""
                else:
                    status_label.update(f"[b red]{message}[/b red]")
                    self.app.log.warning(f"Staff '{self.app.staff_session.user_id}' failed to create user '{user_id}': {message}")
            except Exception as e:
                self.app.log.error(f"Error during user creation by '{self.app.staff_session.user_id}': {e}")
                status_label.update(f"[b red]Error creating user: {e}[/b red]")


class StaffChangeApplicationScreen(Screen):
    """Screen for staff to change the status of account applications."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    application_list = reactive([])
    selected_application_id = reactive(None)
    current_status_filter = reactive(2) # Default to Pending

    STATUS_OPTIONS = [
        ("Pending", 2),
        ("Approved", 1),
        ("Rejected", 0),
        ("All", None), # Represent "All" with None for the backend
    ]

    def on_mount(self) -> None:
        if not self.app.staff_session:
            self.app.log.warning("StaffChangeApplicationScreen mounted without staff session. Popping.")
            self.app.pop_screen()
            return
        
        status_select = self.query_one("#application_status_filter_select", Select)
        status_select.set_options(self.STATUS_OPTIONS)
        status_select.value = self.current_status_filter # Set initial value for the Select

        self.load_applications()

    def load_applications(self):
        status_label = self.query_one("#change_application_status", Static)
        app_select_widget = self.query_one("#application_select", Select)
        try:
            self.app.log.info(f"Staff '{self.app.staff_session.user_id}' fetching applications with status filter: {self.current_status_filter}.")
            
            # Use self.current_status_filter when calling get_applications
            raw_applications = self.app.staff_session.get_applications(status=self.current_status_filter)
            self.app.log.info(f"Raw applications received: {raw_applications}")

            if not raw_applications:
                self.application_list = []
                app_select_widget.set_options([("(No applications found for this filter)", None)])
                app_select_widget.disabled = True
                self.query_one("#approve_application_button", Button).disabled = True
                self.query_one("#reject_application_button", Button).disabled = True
                status_label.update("[b yellow]No applications found for the current filter.[/b yellow]")
                self.selected_application_id = None
                return

            # app_data is (ID, User_ID, Account_ID, Hashed Password, Creation Time, Status)
            # We want to display: "User ID: {User_ID}, App ID: {Application_ID}"
            app_options = []
            for app_data in raw_applications:
                if isinstance(app_data, (list, tuple)) and len(app_data) >= 2: # Need at least App ID and User ID
                    # app_data[0] is Application ID, app_data[1] is User_ID
                    display_text = f"User ID: {app_data[1]}, App ID: {app_data[0]}"
                    app_options.append((display_text, str(app_data[0]))) # Value is still App ID
                else: 
                    # Fallback, though ideally all data should match the expected format
                    self.app.log.warning(f"Unexpected application data format: {app_data}")
                    app_options.append((str(app_data[0]), str(app_data[0]))) 
            
            self.application_list = app_options 
            app_select_widget.set_options(self.application_list)
            app_select_widget.disabled = False
            self.query_one("#approve_application_button", Button).disabled = False
            self.query_one("#reject_application_button", Button).disabled = False
            if self.application_list:
                app_select_widget.value = self.application_list[0][1] 
                self.selected_application_id = self.application_list[0][1]
            else: # Should be covered by the "if not raw_applications" block
                self.selected_application_id = None
            status_label.update("")

        except Exception as e:
            self.app.log.error(f"Error fetching applications for staff '{self.app.staff_session.user_id}': {e}")
            status_label.update(f"[b red]Error fetching applications: {e}[/b red]")
            app_select_widget.set_options([("(Error loading applications)", None)])
            app_select_widget.disabled = True
            self.query_one("#approve_application_button", Button).disabled = True
            self.query_one("#reject_application_button", Button).disabled = True
            self.selected_application_id = None

    def compose(self) -> ComposeResult:
        yield Header(name="Change Account Application Status")
        yield Footer()
        with Vertical(id="change-application-form", classes="form-container"):
            yield Label("Filter by Status:")
            yield Select([], id="application_status_filter_select") # New Select for status
            yield Label("Select Application:")
            yield Select([], id="application_select") # Existing Select for applications
            yield Button("Approve Application", id="approve_application_button", variant="success")
            yield Button("Reject Application", id="reject_application_button", variant="error")
            yield Static(id="change_application_status", classes="status-message")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "application_status_filter_select":
            self.current_status_filter = event.value
            self.app.log.info(f"Application status filter changed to: {self.current_status_filter}")
            self.load_applications() # Reload applications with the new filter
        elif event.select.id == "application_select":
            if event.value is not None:
                self.selected_application_id = str(event.value)
                self.app.log.info(f"Application selected for status change: {self.selected_application_id}")
            else:
                self.selected_application_id = None

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        status_label = self.query_one("#change_application_status", Static)
        if not self.selected_application_id:
            status_label.update("[b red]Please select an application first.[/b red]")
            return
        if not self.app.staff_session:
            status_label.update("[b red]Error: No active staff session.[/b red]")
            return

        action_name = ""
        accept_action = False # For change_application backend call

        if event.button.id == "approve_application_button":
            accept_action = True
            action_name = "approve"
        elif event.button.id == "reject_application_button":
            accept_action = False
            action_name = "reject"
        else:
            return 

        try:
            self.app.log.info(f"Staff '{self.app.staff_session.user_id}' attempting to {action_name} application '{self.selected_application_id}'.")
            success = self.app.staff_session.change_application(self.selected_application_id, accept_action)
            if success:
                status_label.update(f"[b green]Application '{self.selected_application_id}' status changed to '{action_name}d' successfully![/b green]")
                self.app.log.info(f"Application '{self.selected_application_id}' {action_name}d by staff '{self.app.staff_session.user_id}'.")
                self.load_applications() # Refresh the list
            else:
                status_label.update(f"[b red]Failed to {action_name} application '{self.selected_application_id}'. It might have been processed already or an error occurred.[/b red]")
                self.app.log.warning(f"Staff '{self.app.staff_session.user_id}' failed to {action_name} application '{self.selected_application_id}'.")
        except Exception as e:
            self.app.log.error(f"Error changing application status for '{self.selected_application_id}' by staff '{self.app.staff_session.user_id}': {e}")
            status_label.update(f"[b red]Error: {e}[/b red]")


class StaffAddStaffScreen(Screen):
    """Screen for Managers/Admins to add new staff members."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    staff_type_options = reactive([])

    def on_mount(self) -> None:
        if not self.app.staff_session or not hasattr(self.app.staff_session, 'get_type'):
            self.app.log.warning("StaffAddStaffScreen mounted without staff session or get_type. Popping.")
            self.app.pop_screen()
            return
        
        current_staff_type = self.app.staff_session.get_type()
        self.app.log.info(f"StaffAddStaffScreen mounted by staff type: {current_staff_type}")

        options = []
        if current_staff_type >= 1: # Manager or Admin
            options.append(("Staff (0)", 0))
        if current_staff_type == 2: # Admin only
            options.append(("Manager (1)", 1))
        
        self.staff_type_options = options
        select_widget = self.query_one("#new_staff_type_select", Select)
        select_widget.set_options(self.staff_type_options)
        if not self.staff_type_options:
            self.query_one("#add_staff_button", Button).disabled = True
            self.query_one("#add_staff_status", Static).update("[b red]You are not authorized to add any staff types.[/b red]")
        else:
            select_widget.value = self.staff_type_options[0][1] # Default to the first available option


    def compose(self) -> ComposeResult:
        yield Header(name="Add New Staff Member")
        yield Footer()
        with Vertical(id="add-staff-form", classes="form-container"):
            yield Label("People ID:")
            yield Input(placeholder="Enter People ID (e.g., from national ID)", id="new_staff_people_id_input")
            yield Label("New Staff ID:")
            yield Input(placeholder="Enter desired Staff ID", id="new_staff_id_input")
            yield Label("Hashed Password for New Staff:")
            yield Input(placeholder="Enter pre-hashed password", id="new_staff_hashed_password_input")
            yield Label("Staff Type:")
            yield Select([], id="new_staff_type_select")
            yield Button("Add Staff Member", id="add_staff_button", variant="success")
            yield Static(id="add_staff_status", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_staff_button":
            people_id_input = self.query_one("#new_staff_people_id_input", Input)
            staff_id_input = self.query_one("#new_staff_id_input", Input)
            hashed_password_input = self.query_one("#new_staff_hashed_password_input", Input)
            staff_type_select = self.query_one("#new_staff_type_select", Select)
            status_label = self.query_one("#add_staff_status", Static)

            people_id = people_id_input.value
            staff_id = staff_id_input.value
            hashed_password = hashed_password_input.value
            staff_type = staff_type_select.value

            if not people_id or not staff_id or not hashed_password:
                status_label.update("[b red]All fields (People ID, Staff ID, Hashed Password) are required.[/b red]")
                return
            if staff_type is None: # Should not happen if options are set and one is selected
                status_label.update("[b red]Staff type must be selected.[/b red]")
                return

            if not self.app.staff_session or not hasattr(self.app.staff_session, 'add_staff'):
                status_label.update("[b red]Error: No active staff session or add_staff method unavailable.[/b red]")
                self.app.log.error("Add staff attempt with no/invalid staff session.")
                return

            try:
                self.app.log.info(f"Staff '{self.app.staff_session.user_id}' attempting to add staff '{staff_id}' of type '{staff_type}'.")
                # The add_staff method in Manager/Admin expects staff_type as an integer.
                success = self.app.staff_session.add_staff(people_id, staff_id, hashed_password, int(staff_type))
                
                if success:
                    status_label.update(f"[b green]Staff member '{staff_id}' added successfully![/b green]")
                    self.app.log.info(f"Staff '{staff_id}' added by '{self.app.staff_session.user_id}'.")
                    people_id_input.value = ""
                    staff_id_input.value = ""
                    hashed_password_input.value = ""
                else:
                    # The backend method prints reasons, TUI can give a general message.
                    status_label.update(f"[b red]Failed to add staff '{staff_id}'. Possible reasons: People ID not found, Staff ID taken, or authorization issue.[/b red]")
                    self.app.log.warning(f"Staff '{self.app.staff_session.user_id}' failed to add staff '{staff_id}'. Backend returned false.")
            except Exception as e:
                self.app.log.error(f"Error during staff addition by '{self.app.staff_session.user_id}': {e}")
                status_label.update(f"[b red]Error adding staff: {e}[/b red]")


class StaffRemoveStaffScreen(Screen):
    """Screen for Admins to remove existing staff members."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    # No on_mount needed to fetch data, just a form.

    def compose(self) -> ComposeResult:
        yield Header(name="Remove Staff Member")
        yield Footer()
        with Vertical(id="remove-staff-form", classes="form-container"):
            yield Label("Staff ID to Remove:")
            yield Input(placeholder="Enter Staff ID of the member to remove", id="remove_staff_id_input")
            yield Label("[b red]WARNING: This action is irreversible.[/b red]")
            yield Button("Confirm Removal", id="confirm_remove_staff_button", variant="error")
            yield Static(id="remove_staff_status", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_remove_staff_button":
            staff_id_to_remove_input = self.query_one("#remove_staff_id_input", Input)
            status_label = self.query_one("#remove_staff_status", Static)

            staff_id_to_remove = staff_id_to_remove_input.value

            if not staff_id_to_remove:
                status_label.update("[b red]Staff ID to remove cannot be empty.[/b red]")
                return

            if not self.app.staff_session or not hasattr(self.app.staff_session, 'remove_staff'):
                status_label.update("[b red]Error: No active staff session or remove_staff method unavailable (Only Admins can perform this).[/b red]")
                self.app.log.error("Remove staff attempt with no/invalid staff session for this action.")
                return
            
            if self.app.staff_session.user_id == staff_id_to_remove:
                status_label.update("[b red]You cannot remove yourself.[/b red]")
                return

            try:
                self.app.log.info(f"Admin '{self.app.staff_session.user_id}' attempting to remove staff '{staff_id_to_remove}'.")
                success = self.app.staff_session.remove_staff(staff_id_to_remove)
                
                if success:
                    status_label.update(f"[b green]Staff member '{staff_id_to_remove}' removed successfully![/b green]")
                    self.app.log.info(f"Staff '{staff_id_to_remove}' removed by Admin '{self.app.staff_session.user_id}'.")
                    staff_id_to_remove_input.value = ""
                else:
                    # Backend method prints reasons, TUI gives general message.
                    status_label.update(f"[b red]Failed to remove staff '{staff_id_to_remove}'. Possible reasons: Staff ID not found, or authorization issue (e.g., trying to remove a higher-ranking staff).[/b red]")
                    self.app.log.warning(f"Admin '{self.app.staff_session.user_id}' failed to remove staff '{staff_id_to_remove}'. Backend returned false.")
            except Exception as e:
                self.app.log.error(f"Error during staff removal by Admin '{self.app.staff_session.user_id}': {e}")
                status_label.update(f"[b red]Error removing staff: {e}[/b red]")


class CalculateSHA512HashScreen(Screen):
    """Screen to calculate SHA-512 hash of a given text."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(name="Calculate SHA-512 Hash")
        yield Footer()
        with Vertical(id="calculate-hash-form", classes="form-container"):
            yield Label("Text to Hash:")
            yield Input(placeholder="Enter text here", id="text_to_hash_input")
            yield Button("Calculate Hash", id="calculate_hash_button", variant="primary")
            yield Static("Hash will appear here...", id="hash_result_display", classes="status-message")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "calculate_hash_button":
            text_input_widget = self.query_one("#text_to_hash_input", Input)
            result_display_widget = self.query_one("#hash_result_display", Static)
            
            text_to_hash = text_input_widget.value
            if not text_to_hash:
                result_display_widget.update("[b red]Please enter text to hash.[/b red]")
                return

            try:
                hasher = hashlib.sha512()
                hasher.update(text_to_hash.encode('utf-8'))
                hex_hash = hasher.hexdigest()
                result_display_widget.update(f"[b green]SHA-512 Hash:[/b green]\n{hex_hash}")
                self.app.log.info(f"SHA-512 hash calculated for input: '{text_to_hash[:20]}...'")
            except Exception as e:
                result_display_widget.update(f"[b red]Error calculating hash: {e}[/b red]")
                self.app.log.error(f"Error calculating SHA-512 hash: {e}")


class StaffAddPersonScreen(Screen):
    """Screen for staff to add a new person to the People table."""
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    generated_person_id = reactive(None) # To store the generated ID

    def compose(self) -> ComposeResult:
        yield Header(name="Add New Person to System")
        yield Footer()
        with Vertical(id="add-person-form", classes="form-container"):
            yield Label("Enter Person's Full Name:")
            yield Input(placeholder="E.g., John Doe", id="person_name_input")
            yield Button("Add Person", id="add-person-button", variant="success")
            # Button to copy ID, initially hidden and disabled
            yield Button("Copy ID to Clipboard", id="copy_person_id_button", variant="default", classes="hidden", disabled=True)
            yield Static(id="add-person-status", classes="status-message")
            yield Markdown("""
                ### Notes:
                *   Ensure the name is unique.
                *   A new **People ID** and RSA key pair will be generated.
                *   The private key will be saved to `__KEYS__/person_nameprivate_key.pem`.
                *   The **People ID** will be displayed upon successful creation.
            """)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        name_input = self.query_one("#person_name_input", Input)
        status_label = self.query_one("#add-person-status", Static)
        copy_button = self.query_one("#copy_person_id_button", Button)

        if event.button.id == "add-person-button":
            person_name = name_input.value
            self.generated_person_id = None # Reset generated ID
            copy_button.add_class("hidden")
            copy_button.disabled = True

            if not person_name:
                status_label.update("[b red]Person name cannot be empty.[/b red]")
                return

            if not self.app.staff_session:
                status_label.update("[b red]Error: No active staff session.[/b red]")
                self.app.log.error("StaffAddPersonScreen: add_person called without staff_session.")
                return

            try:
                self.app.log.info(f"Staff '{self.app.staff_session.user_id}' attempting to add person: {person_name}")
                success, result_message = self.app.staff_session.add_person(person_name)
                if success:
                    self.generated_person_id = result_message 
                    status_label.update(f"[b green]Person '{person_name}' added successfully!\nYour new People ID is: {self.generated_person_id}[/b green]")
                    self.app.log.info(f"Person '{person_name}' added with People ID: {self.generated_person_id}")
                    name_input.value = "" 
                    copy_button.remove_class("hidden") # Show copy button
                    copy_button.disabled = False      # Enable copy button
                else:
                    status_label.update(f"[b red]Error adding person: {result_message}[/b red]")
                    self.app.log.error(f"Failed to add person '{person_name}': {result_message}")
            except Exception as e:
                status_label.update(f"[b red]An unexpected error occurred: {e}[/b red]")
                self.app.log.exception(f"Unexpected error in StaffAddPersonScreen for {person_name}:")

        elif event.button.id == "copy_person_id_button":
            if self.generated_person_id:
                try:
                    pyperclip.copy(self.generated_person_id)
                    status_label.update(f"[b blue]People ID '{self.generated_person_id}' copied to clipboard![/b blue]")
                    self.app.log.info(f"Copied People ID {self.generated_person_id} to clipboard.")
                except pyperclip.PyperclipException as e:
                    status_label.update(f"[b red]Error copying to clipboard: {e}. Please ensure you have a copy/paste mechanism installed (e.g., xclip or xsel on Linux).[/b red]")
                    self.app.log.error(f"Clipboard error: {e}")
            else:
                status_label.update("[b yellow]No People ID to copy.[/b yellow]")


class StaffPortalScreen(Screen):
    """Main screen for logged-in staff."""
    BINDINGS = [("escape", "logout_staff", "Logout")]

    def compose(self) -> ComposeResult:
        yield Header(name="Staff Portal")
        yield Footer()
        staff_id_display = "N/A"
        staff_type_display = "N/A"
        is_manager_or_admin = False
        is_admin = False

        if self.app.staff_session:
            if hasattr(self.app.staff_session, 'user_id'): 
                staff_id_display = self.app.staff_session.user_id
            if hasattr(self.app.staff_session, 'get_type'):
                staff_type_val = self.app.staff_session.get_type()
                type_map = {0: "Staff", 1: "Manager", 2: "Admin"}
                staff_type_display = type_map.get(staff_type_val, "Unknown")
                if staff_type_val >= 1: is_manager_or_admin = True
                if staff_type_val == 2: is_admin = True
        
        with Vertical(classes="portal-container"):
            yield Label(f"Welcome, Staff: {staff_id_display} (Type: {staff_type_display})")
            yield Static("Staff functionalities will be listed here based on role.", classes="placeholder-text")
            yield Button("Add a Person to System", id="staff_add_person", variant="default") # New Button
            yield Button("Create a user", id="staff_create_user", variant="success")
            yield Button("Change an application", id="staff_change_application", variant="primary") # Enabled, changed variant
            if is_manager_or_admin:
                yield Button("Add a staff", id="staff_add_staff", variant="success") 
                if is_admin:
                    yield Button("Remove a staff", id="staff_remove_staff", variant="warning") # Enabled, changed variant
            yield Button("Calculate SHA-512 Hash", id="staff_calculate_hash", variant="default") # Added new button
            yield Button("Logout", id="staff_logout_button", variant="error")
            yield Static(id="staff_portal_status", classes="status-message")

    def on_mount(self) -> None:
        if not self.app.staff_session:
            self.app.log.warning("StaffPortalScreen mounted without active staff session. Popping screen.")
            self.app.pop_screen()
        else:
            self.app.log.info(f"StaffPortalScreen mounted for staff '{self.app.staff_session.user_id}'.")

    def action_logout_staff(self) -> None:
        if self.app.staff_session:
            self.app.log.info(f"Staff '{self.app.staff_session.user_id}' logging out.")
        else:
            self.app.log.info("Logout action called with no active staff session.")
        self.app.staff_session = None
        self.app.pop_screen()
        self.app.push_screen(LoginChoiceScreen())

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        status_label = self.query_one("#staff_portal_status", Static)
        self.app.log.info(f"StaffPortalScreen: Button '{event.button.id}' pressed by staff '{self.app.staff_session.user_id if self.app.staff_session else 'Unknown'}'.")
        if event.button.id == "staff_logout_button":
            self.action_logout_staff()
        elif event.button.id == "staff_add_person": # New Handler
            self.app.push_screen(StaffAddPersonScreen())
            status_label.update("")
        elif event.button.id == "staff_create_user":
            self.app.push_screen(StaffCreateUserScreen())
            status_label.update("")
        elif event.button.id == "staff_change_application":
            # status_label.update("[b yellow]Functionality 'Change an application' not yet implemented.[/b yellow]")
            if not self.app.staff_session:
                status_label.update("[b red]Error: No active staff session.[/b red]")
                return
            self.app.push_screen(StaffChangeApplicationScreen())
            status_label.update("")
        elif event.button.id == "staff_add_staff":
            # status_label.update("[b yellow]Functionality 'Add a staff' not yet implemented.[/b yellow]")
            if not self.app.staff_session or not hasattr(self.app.staff_session, 'get_type') or self.app.staff_session.get_type() < 1: # Must be Manager or Admin
                status_label.update("[b red]Error: You do not have permission to add staff.[/b red]")
                self.app.log.warning(f"Staff '{self.app.staff_session.user_id if self.app.staff_session else 'Unknown'}' (type {self.app.staff_session.get_type() if self.app.staff_session else 'N/A'}) tried to access add_staff screen without permission.")
                return
            self.app.push_screen(StaffAddStaffScreen())
            status_label.update("")
        elif event.button.id == "staff_remove_staff":
            # status_label.update("[b yellow]Functionality 'Remove a staff' not yet implemented.[/b yellow]")
            if not self.app.staff_session or not hasattr(self.app.staff_session, 'get_type') or self.app.staff_session.get_type() != 2: # Must be Admin
                status_label.update("[b red]Error: You do not have permission to remove staff.[/b red]")
                self.app.log.warning(f"Staff '{self.app.staff_session.user_id if self.app.staff_session else 'Unknown'}' (type {self.app.staff_session.get_type() if self.app.staff_session else 'N/A'}) tried to access remove_staff screen without Admin permission.")
                return
            self.app.push_screen(StaffRemoveStaffScreen())
            status_label.update("")
        elif event.button.id == "staff_calculate_hash": # Added handler for the new button
            self.app.push_screen(CalculateSHA512HashScreen())
            status_label.update("")
        else:
            status_label.update(f"[b yellow]Functionality for '{event.button.label}' not yet implemented.[/b yellow]")


class BankAppTUI(App):
    """Main TUI Application for Bankify."""
    TITLE = "Bankify"
    CSS_PATH = "tui_app.css"
    BINDINGS = [("f12", "toggle_devtools", "Toggle DevTools")]
    user_session: User | None = None
    staff_session: Staff | Manager | Admin | None = None

    def on_mount(self) -> None:
        self.push_screen(LoginChoiceScreen())

    async def on_key(self, event: events.Key) -> None:
        """Handle global key presses for navigation."""
        
        focused_widget = self.focused

        if event.key == "enter":
            if isinstance(focused_widget, Input):
                # For Input fields, make Enter behave like Tab
                event.prevent_default()
                self.action_focus_next()
            # For other widgets (like Buttons, Selects), Enter should perform its default action,
            # so we don't interfere here.
            
        elif event.key == "down":
            # Move focus to the next widget
            event.prevent_default()
            self.action_focus_next()
            
        elif event.key == "up":
            # Move focus to the previous widget
            event.prevent_default()
            self.action_focus_previous()

if __name__ == "__main__":
    app = BankAppTUI()
    app.run()
