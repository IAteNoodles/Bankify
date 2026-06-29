import streamlit as st
import pages

def main():
    st.title("Banking Application")
    st.sidebar.title("Navigation")
    
    options = ["User Portal", "Staff Portal"]
    choice = st.sidebar.selectbox("Select Portal", options)

    if choice == "User Portal":
        import pages.UserPortal as user_portal
        user_portal.run()
    elif choice == "Staff Portal":
        import pages.StaffPortal as staff_portal
        staff_portal.run()

if __name__ == "__main__":
    main()