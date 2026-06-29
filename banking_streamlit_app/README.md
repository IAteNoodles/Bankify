# Banking Streamlit Application

This project is a Streamlit-based frontend for a banking application originally implemented as a command-line interface (CLI). The application allows users and staff to interact with banking functionalities through a web interface.

## Project Structure

- **app.py**: The main entry point for the Streamlit application, setting up the layout and navigation for user and staff portals.
- **pages/**: Contains separate pages for user and staff interactions.
  - **01_User_Portal.py**: Streamlit interface for users to log in, create accounts, delete accounts, and manage banking activities.
  - **02_Staff_Portal.py**: Streamlit interface for staff to create users, change applications, and manage staff accounts.
- **CLI.py**: The original command-line interface code for the banking application.
- **CheckSQL.py**: Contains the SQL injection check function for validating user input.
- **Users.py**: Defines the User class for managing user-related operations.
- **Staffs.py**: Defines the Staff, Manager, and Admin classes for managing staff-related operations.
- **Help.py**: Contains help functions for user guidance.
- **requirements.txt**: Lists the dependencies required for the Streamlit application.

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd banking_streamlit_app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit application:
   ```
   streamlit run app.py
   ```

## Usage Guidelines

- Navigate to the user portal to log in or create a new account.
- Staff members can access the staff portal to manage user accounts and applications.
- Follow the prompts in each portal to perform banking operations.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.