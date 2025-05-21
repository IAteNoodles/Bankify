#!/usr/bin/env python
# bank_tui_enhanced.py
import asyncio

from textual.app import App, ComposeResult
from textual.screen import Screen, ModalScreen
from textual.containers import Container, Vertical, Horizontal, VerticalScroll, ScrollableContainer
from textual.widgets import (
    Header, Footer, Button, Static, Input, Label, Markdown, OptionList, DataTable,
    Placeholder, RadioSet, RadioButton, Pretty
)
from textual.widget import Widget
from textual.reactive import reactive
from textual.binding import Binding
from textual.message import Message

# --- Real Module Imports (Ensure these files/modules are in your PYTHONPATH) ---
try:
    from CheckSQL import sql_injection_check as check
except ImportError:
    print("Critical Error: CheckSQL module not found. Please ensure CheckSQL.py is available.")
    def check(value: str) -> str: # Fallback stub if not found, app will likely fail later
        print(f"[WARN] CheckSQL STUB USED: Checking '{value}'")
        return value.strip() if value else ""

try:
    from Users import User # Assuming Account class is part of/managed by User class
except ImportError:
    print("Critical Error: Users module or User class not found.")
    # Define a User placeholder to allow app to load, but it will fail on use
    class User:
        def __init__(self, *args, **kwargs): raise NotImplementedError("User class from Users module is missing.")

try:
    from Staffs import Staff, Manager, Admin
except ImportError:
    print("Critical Error: Staffs module or Staff classes not found.")
    class Staff:
         def __init__(self, *args, **kwargs): raise NotImplementedError("Staff class from Staffs module is missing.")
    class Manager(Staff):
         def __init__(self, *args, **kwargs): raise NotImplementedError("Manager class from Staffs module is missing.")
    class Admin(Manager):
         def __init__(self, *args, **kwargs): raise NotImplementedError("Admin class from Staffs module is missing.")

try:
    from Help import get_help
except ImportError:
    print("Warning: Help module not found. Help functionality will be basic.")
    def get_help(return_text: bool = False): # Fallback stub
        msg = "Help module not found. This is placeholder help."
        return msg if return_text else print(msg)

try:
    import mariadb
except ImportError:
    print("Critical Error: mariadb module not found. Staff functionality will fail. (pip install mariadb)")
    # Define a mariadb placeholder
    class MariaDBMissing:
        def connect(self, *args, **kwargs): raise NotImplementedError("mariadb module is missing.")
        class Error(Exception): pass # For type hinting
    mariadb = MariaDBMissing()
# --- End of Real Module Imports ---


# --- TUI Helper Screens & Modals ---

class ModalMessageScreen(ModalScreen):
    """Screen for showing a message and then returning."""
    def __init__(self, message: str, title: str = "Notification", name: str | None = None, id: str | None = None, classes: str | None = None):
        super().__init__(name, id, classes)
        self.message = message
        self.title = title

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.title, classes="modal-title"),
            Static(self.message, classes="modal-message"),
            Button("OK", variant="primary", id="ok_button", classes="modal-button"),
            classes="modal-container"
        )
    async def on_mount(self) -> None:
        self.query_one("#ok_button",Button).focus()
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok_button":
            self.dismiss()

class PromptScreen(ModalScreen[str | None]):
    """A modal screen to prompt for a single line of text."""
    def __init__(self, prompt_message: str, initial_value: str = "", is_password: bool = False, title:str="Input Required") -> None:
        super().__init__()
        self.prompt_message = prompt_message
        self.initial_value = initial_value
        self.is_password = is_password
        self.title = title

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.title, classes="modal-title"),
            Label(self.prompt_message),
            Input(value=self.initial_value, password=self.is_password, id="prompt_input"),
            Horizontal(
                Button("Submit", variant="primary", id="submit_button"),
                Button("Cancel", id="cancel_button"),
                classes="prompt-buttons"
            ),
            classes="modal-container"
        )
        
    async def on_mount(self) -> None:
        self.query_one("#prompt_input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_button":
            input_widget = self.query_one("#prompt_input", Input)
            self.dismiss(input_widget.value)
        elif event.button.id == "cancel_button":
            self.dismiss(None)

class YesNoPromptScreen(ModalScreen[bool | None]):
    """A modal screen for a Yes/No confirmation."""
    DEFAULT_CSS = """
    YesNoPromptScreen {
        align: center middle;
    }
    YesNoPromptScreen > Vertical {
        background: $panel;
        width: auto;
        max-width: 50;
        height: auto;
        padding: 1 2;
        border: thick $primary-background-lighten-2;
    }
    YesNoPromptScreen Label { margin-bottom: 1; }
    YesNoPromptScreen Horizontal { align: center_horizontal; width: 100%; margin-top: 1;}
    YesNoPromptScreen Button { margin: 0 1; }
    """
    def __init__(self, prompt_message: str, title: str="Confirmation") -> None:
        super().__init__()
        self.prompt_message = prompt_message
        self.title = title

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label(self.title, classes="modal-title"),
            Label(self.prompt_message),
            Horizontal(
                Button("Yes", variant="success", id="yes_button"),
                Button("No", variant="error", id="no_button"),
            )
        )
    async def on_mount(self) -> None:
        self.query_one("#yes_button", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes_button":
            self.dismiss(True)
        elif event.button.id == "no_button":
            self.dismiss(False)

class TransferMoneyModal(ModalScreen[dict | None]):
    """Modal for transferring money, takes account ID and amount."""
    def __init__(self) -> None:
        super().__init__()

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-container", id="transfer_money_dialog"):
            yield Label("Transfer Money", classes="modal-title")
            yield Label("Target Account ID:")
            yield Input(placeholder="Enter target account ID", id="target_account_id")
            yield Label("Amount to Transfer:")
            yield Input(placeholder="Enter amount", id="transfer_amount")
            with Horizontal(classes="prompt-buttons"):
                yield Button("Transfer", variant="primary", id="submit_transfer")
                yield Button("Cancel", id="cancel_transfer")
    
    async def on_mount(self) -> None:
        self.query_one("#target_account_id", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_transfer":
            target_id = self.query_one("#target_account_id", Input).value
            amount_str = self.query_one("#transfer_amount", Input).value
            if not target_id or not amount_str:
                self.app.notify("Both fields are required.", title="Input Error", severity="warning")
                return
            try:
                amount = int(check(amount_str)) # check amount
                target_id_checked = check(target_id) # check target_id
                self.dismiss({"target_account_id": target_id_checked, "amount": amount})
            except ValueError:
                self.app.notify("Invalid amount. Please enter a number.", title="Input Error", severity="error")
        elif event.button.id == "cancel_transfer":
            self.dismiss(None)

# --- Main Application Screens ---
class MainMenuScreen(Screen):
    TITLE = "Bank API"
    BINDINGS = [Binding("escape", "quit", "Exit App", show=True, priority=True)]


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="main-menu-container"):
            yield Static("Welcome to the Bank API", classes="welcome-text")
            yield Static("Select an option:", classes="instruction-text")
            yield Button("Help", id="help", variant="default", classes="menu-button")
            yield Button("Login", id="login", variant="primary", classes="menu-button")
            yield Button("Exit Application", id="exit_app", variant="error", classes="menu-button")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "help":
            try:
                # Assuming get_help can return markdown or plain text
                help_text = get_help(return_text=True)
                self.app.push_screen(MarkdownScreen(markdown_content=help_text, title="Help Information"))
            except Exception as e:
                self.app.notify(f"Could not load help: {e}", severity="warning")
        elif event.button.id == "login":
            self.app.push_screen(LoginTypeScreen())
        elif event.button.id == "exit_app":
            self.app.exit()

class MarkdownScreen(Screen):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back", show=True)]
    def __init__(self, markdown_content: str, title: str = "Details", **kwargs):
        super().__init__(**kwargs)
        self.markdown_content = markdown_content
        self._title = title
        
    @property
    def TITLE(self):
        return self._title

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(id="markdown_container"): # Changed to ScrollableContainer
            yield Markdown(self.markdown_content)
        yield Footer()

class LoginTypeScreen(Screen):
    TITLE = "Select Login Type"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="login-type-container"):
            yield Static("Please select your login type:", classes="question-text")
            yield Button("User Login", id="user_login", variant="success", classes="menu-button")
            yield Button("Staff Login", id="staff_login", variant="warning", classes="menu-button")
            yield Button("Back to Main Menu", id="back", variant="default", classes="menu-button")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "user_login":
            self.app.push_screen(UserLoginScreen())
        elif event.button.id == "staff_login":
            self.app.push_screen(StaffLoginScreen())
        elif event.button.id == "back":
            self.app.pop_screen()

class UserLoginScreen(Screen):
    TITLE = "User Login"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="login-form-container"):
            yield Label("Enter your User ID:")
            yield Input(placeholder="User ID", id="user_id")
            yield Label("Enter your password:")
            yield Input(placeholder="Password", password=True, id="password")
            with Horizontal(classes="form-buttons"):
                yield Button("Login", variant="primary", id="login_button")
                yield Button("Cancel", id="cancel_button")
        yield Footer()
        
    async def on_mount(self):
        self.query_one("#user_id", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login_button":
            user_id_input = self.query_one("#user_id", Input)
            password_input = self.query_one("#password", Input)
            self.app.notify(password_input.value)
            user_id = check(user_id_input.value) # From original script
            password = check(password_input.value) # From original script

            if not user_id or not password:
                self.app.notify("User ID and Password cannot be empty.", title="Input Error", severity="error")
                return

            try:
                # Original: current_login_object=User(user_id, password)
                current_login_object = User(user_id, password) 
                self.app.current_login_object = current_login_object
                self.app.notify(f"Welcome {user_id}!", title="Login Step", severity="info")
                self.app.push_screen(UserPortalScreen())
            except Exception as e: # Catch potential errors from User constructor (e.g., user not found, bad pass)
                self.app.notify(f"User login failed: {str(e)}", title="Error", severity="error")
        elif event.button.id == "cancel_button":
            self.app.pop_screen()

class StaffLoginScreen(Screen):
    TITLE = "Staff Login"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="login-form-container"):
            yield Static("This is the staff login page", classes="info-text") # Original
            yield Label("Enter your Staff ID:")
            yield Input(placeholder="Staff ID", id="staff_id")
            yield Label("Enter your password:")
            yield Input(placeholder="Password", password=True, id="password")
            with Horizontal(classes="form-buttons"):
                yield Button("Login", variant="primary", id="login_button")
                yield Button("Cancel", id="cancel_button")
        yield Footer()
        
    async def on_mount(self):
        self.query_one("#staff_id", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login_button":
            staff_id_input = self.query_one("#staff_id", Input)
            password_input = self.query_one("#password", Input)

            staff_id = check(staff_id_input.value) # Original
            password = check(password_input.value) # Original

            if not staff_id or not password:
                self.app.notify("Staff ID and Password cannot be empty.", title="Input Error", severity="error")
                return

            if not self.app.setup_staff_db_connection():
                # Notification is handled by setup_staff_db_connection
                return

            db_cursor = self.app.db_cursor
            try:
                # Original: connection.execute("SELECT Type FROM Staff WHERE ID = '%s'" % staff_id)
                # Parameterized query is safer, but sticking to original pattern using checked input
                # The `check` function MUST be robust if used this way. Ideally, use parameterized queries.
                db_cursor.execute(f"SELECT Type FROM Staff WHERE ID = '{staff_id}'")
                result = db_cursor.fetchone()

                if not result:
                    self.app.notify("Invalid staff ID or staff not found.", title="Login Error", severity="error")
                    self.app.close_staff_db_connection()
                    return

                staff_type = result[0]
                current_login_object = None
                # Original: if staff_type == 0: current_login_object = Staff(staff_id, password) ...
                if staff_type == 0: current_login_object = Staff(staff_id, password)
                elif staff_type == 1: current_login_object = Manager(staff_id, password)
                elif staff_type == 2: current_login_object = Admin(staff_id, password)
                else:
                    self.app.notify(f"Invalid staff type '{staff_type}' found in database.", title="Configuration Error", severity="error")
                    self.app.close_staff_db_connection()
                    return # Original: return "Exiting..."
                
                self.app.current_login_object = current_login_object
                self.app.notify(f"Staff {staff_id} (Type: {current_login_object.get_type()}) logged in.", title="Login Successful", severity="info")
                self.app.push_screen(StaffPortalScreen())
                # DB connection remains open for staff portal

            except mariadb.Error as e:
                self.app.notify(f"Database error during staff login: {e}", title="DB Error", severity="error")
                self.app.close_staff_db_connection()
            except Exception as e: # Other errors from Staff constructors etc.
                self.app.notify(f"Staff login procedure failed: {str(e)}", title="Error", severity="error")
                self.app.close_staff_db_connection()

        elif event.button.id == "cancel_button":
            self.app.close_staff_db_connection() 
            self.app.pop_screen()

# --- User Portal Screens ---
class UserPortalScreen(Screen):
    user_obj: User | None = reactive(None) # Type hint for clarity
    BINDINGS = [Binding("escape", "request_logout_user", "Log Out", show=True)]


    async def on_mount(self) -> None:
        self.user_obj = self.app.current_login_object
        if not isinstance(self.user_obj, User): # Ensure it's a User object
            self.app.notify("Error: User session data invalid. Returning to login.", title="Session Error", severity="error")
            # Pop all screens until main menu or login type
            await self.app.pop_screen_until_one_of([LoginTypeScreen, MainMenuScreen])
            return
        
        # Original: print("Welcome to the User Portal")
        # Original: print("Your the following user:" + current_login_object.user_id)
        welcome_static = self.query_one("#welcome_message", Static)
        welcome_static.update(f"Welcome to the User Portal, {self.user_obj.user_id}!")
        self.query_one("#user_id_display", Static).update(f"Logged in as: {self.user_obj.user_id}")


    @property
    def TITLE(self):
        return f"User Portal: {self.user_obj.user_id if self.user_obj else 'N/A'}"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(classes="portal-container"):
            yield Static(id="welcome_message")
            yield Static(id="user_id_display", classes="sub-header")
            yield Static("Options available to you are:", classes="options-header")
            # Original menu options:
            yield Button("Log in to one of your accounts", id="login_account", classes="portal-button")
            yield Button("Create a new account", id="create_account", classes="portal-button")
            yield Button("Delete an account", id="delete_account", classes="portal-button")
            yield Button("Log Out User", id="logout_user_btn", variant="error", classes="portal-button")
        yield Footer()
    
    async def action_request_logout_user(self):
        """Called by escape binding."""
        self.logout_user()

    def logout_user(self):
        self.app.notify("Logging out from User Portal...", title="Logout", severity="info")
        self.app.current_login_object = None 
        self.app.pop_screen() # Back to LoginTypeScreen or MainMenuScreen

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.user_obj: return

        if event.button.id == "login_account":
            # Original: if current_login_object.get_accounts() == 0:
            if self.user_obj.get_accounts() == 0: # Assuming get_accounts() returns count or list
                self.app.notify("You have no accounts. Please create one first.", title="No Accounts", severity="warning")
            else:
                self.app.push_screen(UserAccountListLoginScreen())
        elif event.button.id == "create_account":
            # Original: current_login_object.create_account(check("Password: "))
            def handle_password_for_new_account(password: str | None):
                if password is not None:
                    checked_password = check(password)
                    if not checked_password:
                        self.app.notify("Password cannot be empty for new account.", title="Input Error", severity="warning")
                        return
                    try:
                        self.user_obj.create_account(checked_password)
                        self.app.notify("Account creation process initiated/completed.", title="Account Creation", severity="info")
                        # Add refresh logic if accounts list needs updating on this screen, though usually one navigates away
                    except Exception as e:
                        self.app.notify(f"Error creating account: {str(e)}", title="Error", severity="error")
            
            self.app.push_screen(PromptScreen("Enter Password for the new account:", is_password=True, title="Create Account"), handle_password_for_new_account)

        elif event.button.id == "delete_account":
            # Original: if current_login_object.get_accounts() == 0:
            if self.user_obj.get_accounts() == 0:
                self.app.notify("You have no accounts to delete.", title="No Accounts", severity="warning")
                return # Original: return "You have no accounts associated with you."
            
            # Original: if relative_account > len(accounts) or index-1 < 2:
            # This check implied you need at least 2 accounts for the operation to be valid.
            if len(self.user_obj.accounts) < 2: # Assuming user_obj.accounts is the list of account_ids
                 self.app.notify("Account deletion requires you to have at least two accounts.", title="Operation Denied", severity="warning")
                 return # Original: return "User didn't have enough accounts."
            self.app.push_screen(UserDeleteAccountListScreen())

        elif event.button.id == "logout_user_btn":
            self.logout_user()

class UserAccountListLoginScreen(Screen):
    TITLE = "Log In to Account"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    user_obj: User | None = reactive(None)
    selected_account_id_from_list = reactive(None) # Store the account_id string

    async def on_mount(self):
        self.user_obj = self.app.current_login_object
        if not isinstance(self.user_obj, User) or self.user_obj.get_accounts() == 0:
            self.app.notify("No accounts available or user session error.", severity="warning")
            self.app.pop_screen()
            return
        
        # Original: print("Accounts related to this user are:")
        self.query_one("#account_list_info", Static).update("Select an account to log into:")
        
        # Original: for account in current_login_object.accounts: print(index, ": " + account)
        options = []
        # Assuming self.user_obj.accounts is a list of account_id strings
        for i, acc_id_str in enumerate(self.user_obj.accounts): 
             options.append(OptionList.Option(f"{i+1}: {acc_id_str}", id=acc_id_str)) # id is crucial
        
        option_list_widget = self.query_one("#account_options", OptionList)
        option_list_widget.clear_options()
        option_list_widget.add_options(options)
        if options:
             option_list_widget.focus()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="form-container"):
            yield Static(id="account_list_info")
            yield OptionList(id="account_options") # For selecting account by number
            # Original: relative_account = int(check("Enter the account number to login: "))
            # Handled by OptionList selection now.
            with Horizontal(classes="form-buttons"):
                yield Button("Login to Selected", id="login_selected", variant="primary")
                yield Button("Cancel", id="cancel_op")
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        # event.option.id is the account_id string we stored
        self.selected_account_id_from_list = str(event.option.id) 

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "login_selected":
            if not self.selected_account_id_from_list:
                self.app.notify("Please select an account from the list.", severity="warning")
                return

            account_to_login = self.selected_account_id_from_list

            # Original: password = check("Enter the password to login: ")
            def process_account_login(password_attempt: str | None):
                if password_attempt is None: return # User cancelled prompt

                checked_password = check(password_attempt)
                self.app.notify("Logging in to account...", title="Processing", severity="info")
                
                # Original: current_login_object.login_account(current_login_object.accounts[relative_account-1],password)
                if self.user_obj.login_account(account_to_login, checked_password):
                    # Original: print("Logged in to account: ", account) (account was bugged here, used last from loop)
                    self.app.notify(f"Successfully logged in to account: {account_to_login}", title="Account Login Success", severity="info")
                    self.app.push_screen(UserAccountActionsScreen())
                else:
                    # Original: return "Please make sure that you have an account..."
                    self.app.notify("Account login failed. Check password or account status (e.g., verification).", title="Login Failed", severity="error", timeout=7)
            
            self.app.push_screen(PromptScreen(f"Enter password for account {account_to_login}:", is_password=True, title="Account Password"), process_account_login)

        elif event.button.id == "cancel_op":
            self.app.pop_screen()

class UserAccountActionsScreen(Screen):
    BINDINGS = [Binding("escape", "request_logout_account", "Log Out of Account", show=True)]
    user_obj: User | None = reactive(None)
    
    @property
    def TITLE(self):
        if self.user_obj and self.user_obj.current_account:
            return f"Account Actions: {self.user_obj.current_account.account_id}"
        return "Account Actions"

    async def on_mount(self):
        self.user_obj = self.app.current_login_object
        if not isinstance(self.user_obj, User) or not self.user_obj.current_account:
            self.app.notify("Error: No active account session. Returning.", title="Session Error", severity="error")
            await self.app.pop_screen_until_one_of([UserPortalScreen, LoginTypeScreen])
            return
        self.update_balance_display()

    def update_balance_display(self):
        if self.user_obj and self.user_obj.current_account:
            # Original: print("Your balance is: " + str(current_login_object.current_account.balance))
            # Assuming current_account.get_balance() refreshes and returns the balance
            balance = self.user_obj.current_account.get_balance() 
            self.query_one("#balance_info", Static).update(f"Current Balance: {balance}")

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(classes="portal-container"):
            yield Static(id="balance_info", classes="sub-header")
            yield Static("Account Options:", classes="options-header")
            # Original menu for account actions:
            yield Button("Withdraw Money", id="withdraw", classes="portal-button")
            yield Button("Deposit Money", id="deposit", classes="portal-button")
            yield Button("Fetch/Refresh Balance", id="fetch_balance", classes="portal-button")
            yield Button("Transfer Money", id="transfer", classes="portal-button")
            yield Button("Log Out of This Account", id="logout_account_btn", variant="warning", classes="portal-button")
        yield Footer()
    
    async def action_request_logout_account(self):
        self.logout_account()

    def logout_account(self):
        if self.user_obj:
            self.user_obj.logout_account() # Original call
        self.app.notify("Logged out of current account.", title="Account Logout", severity="info")
        self.app.pop_screen() # Back to UserPortalScreen

    async def on_button_pressed(self, event: Button.Pressed):
        if not self.user_obj or not self.user_obj.current_account: return

        action_id = event.button.id
        current_acc = self.user_obj.current_account # Alias for brevity

        if action_id == "withdraw":
            # Original: amount = int(check("Enter the amount to withdraw: "))
            # Original: current_login_object.current_account.commit_transaction(amount,0)
            def do_withdraw(amount_str: str | None):
                if amount_str is None: return
                try:
                    amount = int(check(amount_str))
                    if current_acc.commit_transaction(amount, 0): # 0 for withdraw
                        self.app.notify(f"Withdrawal of {amount} processed.", title="Withdrawal Success", severity="info")
                    else:
                        self.app.notify(f"Withdrawal of {amount} failed (e.g. insufficient funds).", title="Withdrawal Failed", severity="warning")
                except ValueError: self.app.notify("Invalid amount. Must be a number.", title="Input Error", severity="error")
                except Exception as e: self.app.notify(f"Withdrawal error: {str(e)}", title="Transaction Error", severity="error")
                self.update_balance_display()
            self.app.push_screen(PromptScreen("Enter amount to withdraw:", title="Withdraw"), do_withdraw)

        elif action_id == "deposit":
            # Original: amount = int(check("Enter the amount to deposit: "))
            # Original: current_login_object.current_account.commit_transaction(amount,1)
            def do_deposit(amount_str: str | None):
                if amount_str is None: return
                try:
                    amount = int(check(amount_str))
                    if current_acc.commit_transaction(amount, 1): # 1 for deposit
                         self.app.notify(f"Deposit of {amount} processed.", title="Deposit Success", severity="info")
                    else: self.app.notify(f"Deposit of {amount} failed.", title="Deposit Failed", severity="warning")
                except ValueError: self.app.notify("Invalid amount. Must be a number.", title="Input Error", severity="error")
                except Exception as e: self.app.notify(f"Deposit error: {str(e)}", title="Transaction Error", severity="error")
                self.update_balance_display()
            self.app.push_screen(PromptScreen("Enter amount to deposit:", title="Deposit"), do_deposit)

        elif action_id == "fetch_balance":
            # Original: current_login_object.current_account.get_balance() (which likely prints)
            self.update_balance_display() # This calls get_balance() internally
            self.app.notify("Balance refreshed.", title="Balance Update", severity="info")
        
        elif action_id == "transfer":
            # Original: transfering_account_id = check("Enter the account id to transfer to: ")
            # Original: amount = int(check("Enter the amount to transfer: "))
            # Original: current_login_object.current_account.send_money(transfering_account_id,amount)
            def do_transfer(transfer_data: dict | None):
                if transfer_data is None: return
                target_account_id = transfer_data["target_account_id"]
                amount = transfer_data["amount"]
                try:
                    if current_acc.send_money(target_account_id, amount):
                        self.app.notify(f"Successfully transferred {amount} to {target_account_id}.", title="Transfer Success", severity="info")
                    else:
                        self.app.notify(f"Failed to transfer {amount} to {target_account_id} (e.g., insufficient funds or invalid target).", title="Transfer Failed", severity="warning")
                except Exception as e:
                    self.app.notify(f"Transfer error: {str(e)}", title="Transaction Error", severity="error")
                self.update_balance_display()
            self.app.push_screen(TransferMoneyModal(), do_transfer)

        elif action_id == "logout_account_btn":
            self.logout_account()

# --- User Delete Account Screens ---
class UserDeleteAccountListScreen(Screen):
    TITLE = "Delete Account - Select Account"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    user_obj: User | None = reactive(None)
    selected_account_to_delete_id = reactive(None)

    async def on_mount(self):
        self.user_obj = self.app.current_login_object
        # Checks for 0 or <2 accounts are done before navigating here (in UserPortalScreen)
        if not isinstance(self.user_obj, User) or len(self.user_obj.accounts) < 2:
            self.app.notify("Account deletion prerequisite not met.", severity="error")
            await self.app.pop_screen_until_one_of([UserPortalScreen])
            return
        
        self.query_one("#delete_info", Static).update("Select an account to PERMANENTLY DELETE:")
        options = [OptionList.Option(f"{i+1}: {acc_id}", id=acc_id) for i, acc_id in enumerate(self.user_obj.accounts)]
        
        option_list_widget = self.query_one("#delete_account_options", OptionList)
        option_list_widget.clear_options()
        option_list_widget.add_options(options)
        if options:
            option_list_widget.focus()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="form-container"):
            yield Static(id="delete_info", classes="warning-text") # Make it stand out
            yield OptionList(id="delete_account_options")
            with Horizontal(classes="form-buttons"):
                yield Button("Proceed with Selected Account", id="proceed_delete", variant="error")
                yield Button("Cancel Deletion", id="cancel_delete_op")
        yield Footer()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        self.selected_account_to_delete_id = str(event.option.id)

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "proceed_delete":
            if not self.selected_account_to_delete_id:
                self.app.notify("Please select an account to delete.", severity="warning")
                return
            
            # Pass selected account ID to the next screen for confirmation and details
            self.app.temp_vars['account_to_delete_id'] = self.selected_account_to_delete_id
            self.app.push_screen(UserDeleteAccountDetailsScreen())

        elif event.button.id == "cancel_delete_op":
            self.app.pop_screen()

class UserDeleteAccountDetailsScreen(Screen):
    TITLE = "Confirm Account Deletion Details"
    BINDINGS = [Binding("escape", "custom_pop", "Cancel")]
    
    user_obj: User | None = reactive(None)
    account_to_delete_id: str | None = reactive(None)
    
    # Store other potential fund transfer accounts
    other_accounts: list = reactive(list)
    selected_fund_transfer_target_id: str | None = reactive(None)

    async def on_mount(self):
        self.user_obj = self.app.current_login_object
        self.account_to_delete_id = self.app.temp_vars.get('account_to_delete_id')

        if not isinstance(self.user_obj, User) or not self.account_to_delete_id:
            self.app.notify("Error in deletion process. Account not specified.", severity="error")
            await self.app.pop_screen_until_one_of([UserPortalScreen])
            return
        
        self.query_one("#confirm_delete_label", Label).update(
            f"WARNING: You are about to delete account: {self.account_to_delete_id}."
        )
        # Original: print("ALL YOUR FUNDS WILL BE TRANSFERED TO THE FIRST ACCOUNT ASSOCIATED WITH YOU.")
        # Determine default and other accounts for fund transfer
        self.other_accounts = [acc for acc in self.user_obj.accounts if acc != self.account_to_delete_id]
        if not self.other_accounts:
            # This case should ideally be prevented by the "at least 2 accounts" rule earlier
            self.app.notify("Error: No other account available for fund transfer. Deletion cannot proceed.", severity="error")
            self.query_one("#proceed_final_delete", Button).disabled = True
            self.query_one("#fund_transfer_radioset", RadioSet).disabled = True
            return

        # Set default transfer target (mimicking original's logic for "first account")
        # Original: account_id = accounts[1] if relative_account == 1 else accounts[0]
        # This logic is tricky to map directly. Simplified: transfer to the first *other* account.
        self.selected_fund_transfer_target_id = self.other_accounts[0]
        
        self.query_one("#fund_transfer_info", Static).update(
            f"Funds from {self.account_to_delete_id} will be transferred. Default target: {self.selected_fund_transfer_target_id}."
        )
        
        # Populate RadioSet for changing fund transfer account
        radio_set = self.query_one("#fund_transfer_radioset", RadioSet)
        radio_buttons = []
        for acc_id_str in self.other_accounts:
            radio_buttons.append(RadioButton(acc_id_str, id=acc_id_str))
        radio_set.mount(*radio_buttons)
        # Pre-select the default target
        if self.selected_fund_transfer_target_id in [rb.id for rb in radio_buttons if rb.id]:
            radio_set.pressed_button_id = self.selected_fund_transfer_target_id

        self.query_one("#confirm_q_label", Label).update(
            f"Are you absolutely sure you want to PERMANENTLY delete account {self.account_to_delete_id}?"
        )
        self.query_one("#password_for_delete", Input).focus()

    async def action_custom_pop(self):
        self.app.notify("Account deletion cancelled.", severity="info")
        self.app.pop_screen()


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(classes="form-container"):
            yield Label(id="confirm_delete_label", classes="warning-text")
            yield Label("Enter password for the account to be deleted:", classes="mt-1")
            yield Input(placeholder="Password", password=True, id="password_for_delete")
            
            yield Static(id="fund_transfer_info", classes="mt-1 info-text")
            yield Label("Change fund transfer target account? (Optional)", classes="mt-1")
            yield RadioSet(id="fund_transfer_radioset") # RadioButtons added in on_mount

            yield Label("Path to your private key file (for security verification):", classes="mt-1")
            yield Input(placeholder="/path/to/your/private_key.pem", id="private_key_path")
            
            yield Label(id="confirm_q_label", classes="mt-2 warning-text")
            yield Button("Yes, PERMANENTLY DELETE This Account", id="proceed_final_delete", variant="error", classes="mt-1")
            yield Button("Cancel Deletion Process", id="cancel_final_delete", variant="primary", classes="mt-1")
        yield Footer()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.pressed_button:
            self.selected_fund_transfer_target_id = str(event.radio_set.pressed_button.id)
            self.query_one("#fund_transfer_info", Static).update(
                f"Funds from {self.account_to_delete_id} will be transferred to: {self.selected_fund_transfer_target_id}."
            )

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "cancel_final_delete":
            await self.action_custom_pop()
            return

        if event.button.id == "proceed_final_delete":
            password_attempt = check(self.query_one("#password_for_delete", Input).value)
            private_key_path_str = self.query_one("#private_key_path", Input).value # Original does not use check() here

            if not password_attempt:
                self.app.notify("Password for the account to be deleted is required.", severity="error")
                return
            if not private_key_path_str:
                self.app.notify("Path to private key file is required.", severity="error")
                return
            if not self.selected_fund_transfer_target_id:
                self.app.notify("A fund transfer target account must be selected.", severity="error")
                return

            # Confirmation prompt - already implicitly done by pressing the big red button
            # Original: choice=check("THIS WILL YOUR ACCOUNT, ARE YOU SURE... (y?)")
            # Here, the button press itself is the strong confirmation. Can add another YesNo if desired.
            
            # Original: private_key=open(input("Path to private key: "))
            private_key_file_handle = None
            try:
                private_key_file_handle = open(private_key_path_str, 'rb') # Open in binary read mode as is common for keys
            except IOError as e:
                self.app.notify(f"Error opening private key file: {e}", title="File Error", severity="error")
                return
            
            try:
                self.app.notify(f"Attempting to delete account {self.account_to_delete_id} and transfer funds to {self.selected_fund_transfer_target_id}...", severity="info")
                # Original: current_login_object.delete_account(accounts[relative_account-1], password, account_id, private_key)
                success = self.user_obj.delete_account(
                    self.account_to_delete_id,
                    password_attempt,
                    self.selected_fund_transfer_target_id,
                    private_key_file_handle # Pass the open file handle
                )
                if success:
                    self.app.notify(f"Account {self.account_to_delete_id} deleted successfully.", title="Deletion Complete", severity="info")
                    self.app.temp_vars.pop('account_to_delete_id', None) # Clean up temp var
                    # Pop back to user portal, which should refresh or handle the change
                    await self.app.pop_screen_until_one_of([UserPortalScreen])
                    # Potentially trigger a refresh on UserPortalScreen if it displays account list
                else:
                    self.app.notify(f"Failed to delete account {self.account_to_delete_id}. Check password or other conditions.", title="Deletion Failed", severity="error")
            except Exception as e:
                self.app.notify(f"An unexpected error occurred during account deletion: {str(e)}", title="Critical Error", severity="error")
            finally:
                if private_key_file_handle:
                    private_key_file_handle.close()

# --- Staff Portal Screens ---
class StaffPortalScreen(Screen):
    staff_obj: Staff | Manager | Admin | None = reactive(None)
    BINDINGS = [Binding("escape", "request_logout_staff", "Log Out", show=True)]

    @property
    def TITLE(self):
        if self.staff_obj:
            return f"Staff Portal: {self.staff_obj.staff_id} ({self.staff_obj.get_type()})" # Original uses get_type()
        return "Staff Portal"

    async def on_mount(self):
        self.staff_obj = self.app.current_login_object
        if not (isinstance(self.staff_obj, Staff) or isinstance(self.staff_obj, Manager) or isinstance(self.staff_obj, Admin)):
            self.app.notify("Error: Staff session data invalid. Returning.", title="Session Error", severity="error")
            await self.app.pop_screen_until_one_of([LoginTypeScreen, MainMenuScreen])
            return
        
        # Original: print("Welcome to the Staff Portal")
        # Original: print("Your the following staff:" + current_login_object.user_id + "of type:" + str(current_login_object.get_type()))
        self.query_one("#staff_welcome", Static).update(
            f"Welcome to the Staff Portal, {self.staff_obj.user_id}!\nType: {self.staff_obj.get_type()}"
        )
        self.update_options_display()

    def update_options_display(self):
        container = self.query_one("#staff_options_container", Vertical)
        # Clear previous buttons to prevent duplication if this method is called multiple times
        for widget in container.children:
            widget.remove()

        # Original: options.append("1. Create a user"), options.append("2. Change an application")
        container.mount(Button("Create a User", id="create_user", classes="portal-button"))
        container.mount(Button("Change an Account Application", id="change_application", classes="portal-button"))

        # Original: if current_login_object.type >=1: options.append("3. Add a staff")
        if self.staff_obj.type >= 1: # Manager or Admin
            container.mount(Button("Add a Staff Member", id="add_staff", classes="portal-button"))
            # Original: if current_login_object.type==2: options.append("4. Remove a staff")
            if self.staff_obj.type == 2: # Admin only
                container.mount(Button("Remove a Staff Member", id="remove_staff", classes="portal-button"))
        
        container.mount(Button("Log Out Staff", id="logout_staff_btn", variant="error", classes="portal-button mt-2"))

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with VerticalScroll(classes="portal-container"):
            yield Static(id="staff_welcome", classes="sub-header")
            yield Static("Staff Options:", classes="options-header mt-1")
            yield Vertical(id="staff_options_container")
        yield Footer()

    async def action_request_logout_staff(self):
        self.logout_staff()

    def logout_staff(self):
        self.app.notify("Logging out from Staff Portal...", title="Logout", severity="info")
        self.app.close_staff_db_connection()
        self.app.current_login_object = None
        self.app.pop_screen()

    async def on_button_pressed(self, event: Button.Pressed):
        action = event.button.id
        if action == "logout_staff_btn":
            self.logout_staff()
        elif action == "create_user":
            # Original: people_id, user_id, hashed_passwd inputs then add_user()
            self.app.push_screen(StaffCreateUserScreen())
        elif action == "change_application":
            self.app.push_screen(StaffApplicationOptionsScreen())
        elif action == "add_staff":
            # Original: people_id, staff_id, hashed_passwd, staff_type inputs then add_staff()
            self.app.push_screen(StaffAddStaffScreen())
        elif action == "remove_staff":
            # Original: staff_id input then remove_staff()
            self.app.push_screen(StaffRemoveStaffScreen())


class StaffCreateUserScreen(Screen): # Placeholder - implement inputs and call
    TITLE = "Staff - Create User"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="form-container"):
            yield Label("Create New User Account", classes="sub-header")
            yield Label("People ID (e.g., National ID):") # Varchar(64)
            yield Input(id="people_id", placeholder="People ID")
            yield Label("Desired User ID:") # Varchar(36)
            yield Input(id="user_id", placeholder="User ID for login")
            yield Label("Hashed Password:") # Varchar(128)
            yield Input(id="hashed_passwd", placeholder="Pre-hashed password string")
            with Horizontal(classes="form-buttons"):
                yield Button("Create User", id="submit_create_user", variant="primary")
                yield Button("Cancel", id="cancel_create_user")
        yield Footer()

    async def on_mount(self):
        self.query_one("#people_id", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "submit_create_user":
            people_id = check(self.query_one("#people_id").value)
            user_id = check(self.query_one("#user_id").value)
            hashed_passwd = check(self.query_one("#hashed_passwd").value) # Passwords should ideally not be "checked" this way if it alters them

            if not all([people_id, user_id, hashed_passwd]):
                self.app.notify("All fields are required.", severity="warning")
                return

            staff_obj = self.app.current_login_object
            if staff_obj and hasattr(staff_obj, "add_user"):
                try:
                    staff_obj.add_user(people_id, user_id, hashed_passwd)
                    self.app.notify(f"User {user_id} creation process initiated.", severity="info")
                    self.app.pop_screen()
                except Exception as e:
                    self.app.notify(f"Failed to create user: {e}", severity="error")
            else:
                self.app.notify("Error: Staff object not found or lacks add_user method.", severity="error")

        elif event.button.id == "cancel_create_user":
            self.app.pop_screen()

class StaffApplicationOptionsScreen(Screen):
    TITLE = "Staff - Account Applications"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="form-container"):
            yield Label("Manage Account Applications", classes="sub-header")
            yield Static("Do you want to list all open applications or enter an ID directly?")
            yield Button("List All Open Applications", id="list_apps", classes="menu-button")
            yield Button("Enter Application ID Directly", id="enter_id", classes="menu-button")
            yield Button("Back to Staff Portal", id="back_staff_portal",variant="default", classes="menu-button")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "list_apps":
            self.app.push_screen(StaffListApplicationsScreen())
        elif event.button.id == "enter_id":
            # This will skip listing and go straight to prompting for ID and action
            self.app.push_screen(StaffChangeApplicationScreen(list_applications_first=False))
        elif event.button.id == "back_staff_portal":
            self.app.pop_screen()


class StaffListApplicationsScreen(Screen):
    TITLE = "Staff - Open Account Applications"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="table-container"): # Use a specific class for tables
            yield Label("Current Open Account Applications", classes="sub-header")
            yield DataTable(id="applications_table")
            yield Horizontal(
                Button("Process Selected/Entered Application ID", id="process_app", variant="primary"),
                Button("Back", id="back_options"),
                classes="form-buttons mt-1"
            )
        yield Footer()

    async def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Index", "Application ID", "User ID", "Creation Time")
        table.cursor_type = "row"

        if not self.app.db_cursor:
            self.app.notify("Database connection not available.", severity="error")
            if not self.app.setup_staff_db_connection(): # Attempt to reconnect
                 self.app.pop_screen()
                 return
        
        db_cursor = self.app.db_cursor
        try:
            # Original: connection.execute("SELECT `ID`, `User_ID`, `CreationTime` FROM Account_Application")
            db_cursor.execute("SELECT `ID`, `User_ID`, `CreationTime` FROM Account_Application")
            applications = db_cursor.fetchall()

            if not applications:
                # Original: print("There are no applications opened at present.")
                table.add_row(" ", "No open applications found.", " ", " ") # Show in table
                self.query_one("#process_app", Button).disabled = True
            else:
                for i, app_data in enumerate(applications):
                    table.add_row(str(i+1), *app_data) # app_data should be (ID, User_ID, CreationTime)
        except mariadb.Error as e:
            self.app.notify(f"Error fetching applications: {e}", severity="error")
            table.add_row("Error fetching data.")
            self.query_one("#process_app", Button).disabled = True
        except Exception as e:
            self.app.notify(f"Unexpected error: {e}", severity="error")
            self.query_one("#process_app", Button).disabled = True


    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "process_app":
            # User can visually select, but still needs to enter ID or select from a list then type.
            # This button will take them to the screen where they enter the ID.
            self.app.push_screen(StaffChangeApplicationScreen(list_applications_first=True))
        elif event.button.id == "back_options":
            self.app.pop_screen()
            
class StaffChangeApplicationScreen(Screen):
    TITLE = "Staff - Change Application Status"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def __init__(self, list_applications_first: bool = True, selected_app_id: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.list_applications_first = list_applications_first
        self.selected_app_id_from_list = selected_app_id # If coming from a selection

    async def on_mount(self):
        app_id_input = self.query_one("#application_id_input", Input)
        if self.selected_app_id_from_list:
            app_id_input.value = self.selected_app_id_from_list
        app_id_input.focus()
        
        if not self.list_applications_first: # If user chose to enter ID directly
            self.query_one("#info_text", Static).update("Enter the Application ID to process.")
        else: # If user came from listing applications
            self.query_one("#info_text", Static).update("Enter Application ID from the list (or any known ID).")


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="form-container"):
            yield Static(id="info_text")
            yield Label("Application ID to Process:")
            yield Input(id="application_id_input", placeholder="Enter Application ID")
            yield Label("Action for this Application:")
            yield RadioSet(
                RadioButton("Accept Application", id="accept_app", value=True), # value=True is important
                RadioButton("Reject Application", id="reject_app", value=False),
                id="app_action_radioset"
            )
            with Horizontal(classes="form-buttons mt-1"):
                yield Button("Submit Action", id="submit_app_action", variant="primary")
                yield Button("Cancel", id="cancel_app_action")
        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "submit_app_action":
            app_id = check(self.query_one("#application_id_input", Input).value)
            action_radioset = self.query_one("#app_action_radioset", RadioSet)
            
            if not app_id:
                self.app.notify("Application ID is required.", severity="warning")
                return
            if action_radioset.pressed_button is None : # Check if any radio button is selected
                 self.app.notify("Please select an action (Accept or Reject).", severity="warning")
                 return

            accept_status = action_radioset.pressed_button.value # True for accept, False for reject

            staff_obj = self.app.current_login_object
            if staff_obj and hasattr(staff_obj, "change_application"):
                try:
                    # Original: current_login_object.change_application(application_id, accept)
                    staff_obj.change_application(app_id, accept_status)
                    action_str = "accepted" if accept_status else "rejected"
                    self.app.notify(f"Application {app_id} has been {action_str}.", severity="info")
                    self.app.pop_screen() # Back to options or list
                    if self.list_applications_first: # If came from list, pop again to refresh list view potentially
                        self.app.pop_screen() 
                except Exception as e:
                    self.app.notify(f"Failed to change application {app_id}: {e}", severity="error")
            else:
                self.app.notify("Error: Staff object not found or action unavailable.", severity="error")

        elif event.button.id == "cancel_app_action":
            self.app.pop_screen()

class StaffAddStaffScreen(Screen): # Placeholder - implement fully
    TITLE = "Manager/Admin - Add Staff"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    # Based on original: people_id, staff_id, hashed_passwd, staff_type
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="form-container"):
            yield Label("Add New Staff Member", classes="sub-header")
            yield Label("People ID:")
            yield Input(id="people_id", placeholder="Unique People ID")
            yield Label("New Staff ID (for login):")
            yield Input(id="staff_id", placeholder="Login ID for new staff")
            yield Label("Hashed Password for New Staff:")
            yield Input(id="hashed_passwd", placeholder="Pre-hashed password")
            yield Label("Staff Type (0: Staff, 1: Manager):") # Admin cannot create another Admin via this in original stub
            yield Input(id="staff_type", placeholder="0 or 1", type="integer")
            with Horizontal(classes="form-buttons mt-1"):
                yield Button("Add Staff Member", id="submit_add_staff", variant="primary")
                yield Button("Cancel", id="cancel_add_staff")
        yield Footer()
    
    async def on_mount(self):
        self.query_one("#people_id", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "submit_add_staff":
            people_id = check(self.query_one("#people_id").value)
            staff_id_new = check(self.query_one("#staff_id").value) # Renamed to avoid conflict
            hashed_passwd = check(self.query_one("#hashed_passwd").value)
            staff_type_str = check(self.query_one("#staff_type").value)

            if not all([people_id, staff_id_new, hashed_passwd, staff_type_str]):
                self.app.notify("All fields are required.", severity="warning")
                return
            
            try:
                staff_type = int(staff_type_str)
                if staff_type not in [0, 1]: # Managers can only create Staff or other Managers (not Admins)
                    # Admins can also create managers or staff via this
                    current_staff_type = self.app.current_login_object.type
                    if staff_type >= current_staff_type and current_staff_type < 2 : # Manager trying to create same or higher, or non-admin creating admin
                        self.app.notify("Invalid staff type or insufficient permissions for creation.", severity="error")
                        return
                    if staff_type > 1 and current_staff_type !=2 : # Non-admin trying to create admin (type 2)
                        self.app.notify("Only Admins can create other Admins (Type 2). You can create Type 0 (Staff) or Type 1 (Manager).", severity="error")
                        return


            except ValueError:
                self.app.notify("Staff type must be a number (0 or 1).", severity="error")
                return

            manager_obj = self.app.current_login_object # Should be Manager or Admin
            if manager_obj and hasattr(manager_obj, "add_staff"):
                try:
                    # Original: current_login_object.add_staff(people_id, staff_id, hashed_passwd, staff_type)
                    success = manager_obj.add_staff(people_id, staff_id_new, hashed_passwd, staff_type)
                    if success:
                        self.app.notify(f"Staff member {staff_id_new} (Type: {staff_type}) added.", severity="info")
                        self.app.pop_screen()
                    else:
                        self.app.notify(f"Failed to add staff {staff_id_new}. Permission issue or invalid type.", severity="error")
                except Exception as e:
                    self.app.notify(f"Error adding staff: {e}", severity="error")
            else:
                self.app.notify("Error: Current staff object cannot perform this action.", severity="error")
        
        elif event.button.id == "cancel_add_staff":
            self.app.pop_screen()


class StaffRemoveStaffScreen(Screen): # Placeholder - implement fully
    TITLE = "Admin - Remove Staff"
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]
    # Based on original: staff_id
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="form-container"):
            yield Label("Remove Staff Member", classes="sub-header warning-text")
            yield Label("Staff ID to Remove:")
            yield Input(id="staff_id_remove", placeholder="Enter Staff ID")
            with Horizontal(classes="form-buttons mt-1"):
                yield Button("Remove This Staff Member", id="submit_remove_staff", variant="error")
                yield Button("Cancel", id="cancel_remove_staff")
        yield Footer()

    async def on_mount(self):
        self.query_one("#staff_id_remove", Input).focus()

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "submit_remove_staff":
            staff_id_to_remove = check(self.query_one("#staff_id_remove").value)
            if not staff_id_to_remove:
                self.app.notify("Staff ID to remove is required.", severity="warning")
                return

            admin_obj = self.app.current_login_object # Should be Admin
            if admin_obj and hasattr(admin_obj, "remove_staff"):
                if admin_obj.staff_id == staff_id_to_remove: # Prevent self-removal
                    self.app.notify("Cannot remove yourself.", severity="error")
                    return
                try:
                    # Original: current_login_object.remove_staff(staff_id)
                    success = admin_obj.remove_staff(staff_id_to_remove)
                    if success:
                        self.app.notify(f"Staff member {staff_id_to_remove} removed.", severity="info")
                        self.app.pop_screen()
                    else:
                        self.app.notify(f"Failed to remove staff {staff_id_to_remove} (e.g. not found, or protected).", severity="error")
                except Exception as e:
                    self.app.notify(f"Error removing staff: {e}", severity="error")
            else:
                self.app.notify("Error: Current staff object cannot perform this action.", severity="error")

        elif event.button.id == "cancel_remove_staff":
            self.app.pop_screen()

# --- Main App Class ---
class BankTUI(App):
    CSS_PATH = "bank_tui.tcss"
    SCREENS = {
        "main_menu": MainMenuScreen,
        "markdown_view": MarkdownScreen,
        "login_type": LoginTypeScreen,
        "user_login": UserLoginScreen,
        "staff_login": StaffLoginScreen,
        "user_portal": UserPortalScreen,
        "user_account_list_login": UserAccountListLoginScreen,
        "user_account_actions": UserAccountActionsScreen,
        "user_delete_account_list": UserDeleteAccountListScreen,
        "user_delete_account_details": UserDeleteAccountDetailsScreen,
        "staff_portal": StaffPortalScreen,
        "staff_create_user": StaffCreateUserScreen,
        "staff_app_options": StaffApplicationOptionsScreen,
        "staff_list_apps": StaffListApplicationsScreen,
        "staff_change_app": StaffChangeApplicationScreen,
        "staff_add_staff": StaffAddStaffScreen,
        "staff_remove_staff": StaffRemoveStaffScreen,
    }
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit App", show=True, priority=True),
    ]

    title = "Bank TUI Deluxe"

    def __init__(self):
        super().__init__()
        self.current_login_object: User | Staff | Manager | Admin | None = None
        self.db_connection = None
        self.db_cursor = None
        self.temp_vars = {} # For small, temporary data between closely related screen transitions

    def on_mount(self) -> None:
        self.push_screen(MainMenuScreen())

    def setup_staff_db_connection(self) -> bool:
        if self.db_connection and self.db_cursor: # Already connected
            return True
        try:
            # Ensure mariadb is not the placeholder if import failed
            if not hasattr(mariadb, "connect") or isinstance(mariadb, type) and mariadb.__name__ == "MariaDBMissing":
                 raise ImportError("MariaDB module is not correctly loaded.")

            self.db_connection = mariadb.connect(user="Staff", passwd="Staff@Bank", database="Banking")
            self.db_cursor = self.db_connection.cursor()
            self.notify("Staff database connection established.", severity="info", timeout=2)
            return True
        except ImportError as e: # Catch the specific ImportError for MariaDB
            self.notify(f"MariaDB module error: {e}. Staff functions disabled.", title="Critical DB Error", severity="error", timeout=10)
            return False
        except mariadb.Error as e:
            self.notify(f"Database connection error: {e}", title="DB Connection Error", severity="error", timeout=7)
            self.db_connection = None
            self.db_cursor = None
            return False
        except Exception as e: # Catch any other unexpected errors during connection
            self.notify(f"Unexpected error connecting to DB: {e}", title="DB Error", severity="error", timeout=7)
            self.db_connection = None
            self.db_cursor = None
            return False


    def close_staff_db_connection(self):
        if self.db_cursor:
            try: self.db_cursor.close()
            except: pass # Ignore errors on close
            self.db_cursor = None
        if self.db_connection:
            try: self.db_connection.close()
            except: pass # Ignore errors on close
            self.db_connection = None
        self.notify("Staff database connection closed.", severity="info", timeout=2)

    async def pop_screen_until_one_of(self, screen_classes: list[type[Screen]]):
        """Pops screens until one of the specified screen classes is at the top, or only one screen remains."""
        while len(self.screen_stack) > 1:
            top_screen_type = type(self.screen_stack[-1])
            if top_screen_type in screen_classes:
                break
            await self.pop_screen()


if __name__ == "__main__":
    css_content = """
    /* General Styling */
    Screen {
        align: center middle;
        background: $panel-darken-1;
        overflow: auto; /* Ensure screens can scroll if content exceeds viewport */
    }

    Header, Footer {
        background: $primary-background-darken-2;
        color: $text;
    }

    /* Containers for Forms and Portals */
    .main-menu-container, .login-type-container, .login-form-container, 
    .portal-container, .form-container, .table-container {
        width: auto;
        max-width: 70; /* Increased max-width for better readability */
        padding: 1 2;
        margin: 1 0;
        border: tall $primary-background-lighten-1;
        background: $panel;
        /* Adding overflow for individual containers if their content is too large */
        overflow: auto; 
        height: auto; /* Adjust height based on content */
        max-height: 90%; /* Prevent individual containers from taking full screen height */

    }
    ScrollableContainer {
        background: $surface;
    }

    /* Text Styling */
    .welcome-text { text-align: center; margin-bottom: 1; text-style: bold; }
    .instruction-text, .info-text, .question-text, .options-header, .sub-header { 
        margin-bottom: 1; 
        color: $text-muted; /* Softer color for instructions */
    }
    .sub-header { text-style: bold; color: $text; }
    .warning-text { color: $error; text-style: bold; }
    Label { margin-bottom: 0; margin-top: 1; } /* Compact labels */

    /* Buttons */
    Button { width: 100%; margin-top:1; } /* Default full-width buttons with some top margin */
    Button.menu-button, Button.portal-button { margin-bottom: 1; } /* Spacing for list-like buttons */
    .form-buttons { width: 100%; align-horizontal: right; padding-top: 1; }
    .form-buttons Button { width: auto; margin-left: 1; } /* Smaller buttons in form footers */
    .mt-1 {margin-top: 1;}
    .mt-2 {margin-top: 2;}

    /* Inputs and Selects */
    Input, OptionList, DataTable, RadioSet { margin-bottom: 1; }
    Input { border: round $primary; }
    Input:focus { border: round $secondary; }
    OptionList, RadioSet { border: round $surface; padding: 1; max-height: 15; }


    /* Modal Styling */
    ModalScreen { align: center middle; background: $primary-background 50%; } /* Semi-transparent */
    .modal-container {
        width: auto; max-width: 60; padding: 2; border: wide $accent; background: $panel-darken-2;
    }
    .modal-title { text-style: bold; text-align: center; margin-bottom:1; width: 100%;}
    .modal-message { margin: 1 0; }
    .prompt-buttons { width: 100%; align-horizontal: center; padding-top: 1; }
    .prompt-buttons Button { margin: 0 1; }

    /* Markdown View */
    #markdown_container { padding: 1; background: $surface; border: round $primary-lighten-2; }
    Markdown { width: 100%; }
    Pretty { background: $surface; padding: 1; border: round $primary; margin-top:1;}
    """
    try:
        with open("bank_tui.tcss", "w") as f: # Overwrite with new default if needed
            f.write(css_content)
    except IOError:
        print("Warning: Could not write bank_tui.tcss file.")

    app = BankTUI()
    app.run()