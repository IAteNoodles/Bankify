import streamlit as st
from Users import User
from CheckSQL import sql_injection_check as check

def user_portal():
    st.title("User Portal")
    
    user_id = st.text_input("Enter your User ID:")
    password = st.text_input("Enter your Password:", type='password')
    
    if st.button("Login"):
        if user_id and password:
            current_user = User(user_id, password)
            if current_user.login():
                st.success(f"Welcome, {current_user.user_id}!")
                manage_accounts(current_user)
            else:
                st.error("Invalid credentials. Please try again.")
        else:
            st.warning("Please enter both User ID and Password.")

def manage_accounts(current_user):
    st.subheader("Manage Your Accounts")
    accounts = current_user.get_accounts()
    
    if accounts:
        selected_account = st.selectbox("Select an account to manage:", accounts)
        
        if st.button("View Balance"):
            balance = current_user.get_balance(selected_account)
            st.write(f"Your balance is: {balance}")
        
        if st.button("Withdraw"):
            amount = st.number_input("Enter amount to withdraw:", min_value=0)
            if st.button("Confirm Withdrawal"):
                current_user.withdraw(selected_account, amount)
                st.success("Withdrawal successful!")
        
        if st.button("Deposit"):
            amount = st.number_input("Enter amount to deposit:", min_value=0)
            if st.button("Confirm Deposit"):
                current_user.deposit(selected_account, amount)
                st.success("Deposit successful!")
        
        if st.button("Transfer"):
            transfer_account = st.text_input("Enter account ID to transfer to:")
            amount = st.number_input("Enter amount to transfer:", min_value=0)
            if st.button("Confirm Transfer"):
                current_user.transfer(selected_account, transfer_account, amount)
                st.success("Transfer successful!")
    else:
        st.warning("You have no accounts associated with you.")

def run():
    st.title("User Portal")
    st.write("Welcome to the user portal!")

if __name__ == "__main__":
    user_portal()