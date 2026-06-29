import streamlit as st
from CheckSQL import sql_injection_check as check
from Staffs import Staff, Manager, Admin
import mariadb

def staff_login():
    staff_id = st.text_input("Enter your staff ID:")
    password = st.text_input("Enter your password:", type='password')
    if st.button("Login"):
        connector = mariadb.connect(
            user="Staff", passwd="Staff@Bank", database="Banking")
        connection = connector.cursor()
        connection.execute("SELECT Type FROM Staff WHERE ID = '%s'" % staff_id)
        staff_type = connection.fetchone()
        
        if staff_type is None:
            st.error("Invalid staff ID.")
            return None
        
        staff_type = staff_type[0]
        if staff_type == 0:
            return Staff(staff_id, password)
        elif staff_type == 1:
            return Manager(staff_id, password)
        elif staff_type == 2:
            return Admin(staff_id, password)
        else:
            st.error("Invalid staff type.")
            return None

def staff_portal():
    st.title("Staff Portal")
    current_login_object = staff_login()
    
    if current_login_object:
        st.success(f"Welcome {current_login_object.user_id} of type {current_login_object.get_type()}")
        
        options = ["Create a user", "Change an application"]
        if current_login_object.type >= 1:
            options.append("Add a staff")
            if current_login_object.type == 2:
                options.append("Remove a staff")
        
        choice = st.selectbox("Select an option:", options)
        
        if choice == "Create a user":
            people_id = st.text_input("Enter the people ID:")
            user_id = st.text_input("Enter the user ID:")
            hashed_passwd = st.text_input("Enter the hashed password:")
            if st.button("Create User"):
                current_login_object.add_user(people_id, user_id, hashed_passwd)
                st.success("User created successfully.")
        
        elif choice == "Change an application":
            application_id = st.text_input("Enter the application ID:")
            accept = st.radio("Do you want to accept this application?", ("Yes", "No"))
            if st.button("Change Application"):
                current_login_object.change_application(application_id, accept == "Yes")
                st.success("Application status updated.")
        
        elif choice == "Add a staff":
            people_id = st.text_input("Enter the people ID for new staff:")
            staff_id = st.text_input("Enter the staff ID:")
            hashed_passwd = st.text_input("Enter the hashed password:")
            staff_type = st.selectbox("Select staff type:", [0, 1, 2])
            if st.button("Add Staff"):
                current_login_object.add_staff(people_id, staff_id, hashed_passwd, staff_type)
                st.success("Staff added successfully.")
        
        elif choice == "Remove a staff":
            staff_id = st.text_input("Enter the staff ID to remove:")
            if st.button("Remove Staff"):
                current_login_object.remove_staff(staff_id)
                st.success("Staff removed successfully.")

def run():
    st.title("Staff Portal")
    st.write("Welcome to the staff portal!")

if __name__ == "__main__":
    staff_portal()