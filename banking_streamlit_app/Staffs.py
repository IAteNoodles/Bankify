# Staffs.py

class Staff:
    def __init__(self, staff_id, password):
        self.staff_id = staff_id
        self.password = password
        self.type = 0  # Default type for Staff

    def get_type(self):
        return self.type

    def add_user(self, people_id, user_id, hashed_passwd):
        # Logic to add a user
        pass

    def change_application(self, application_id, accept):
        # Logic to change an application status
        pass

class Manager(Staff):
    def __init__(self, staff_id, password):
        super().__init__(staff_id, password)
        self.type = 1  # Type for Manager

    def add_staff(self, people_id, staff_id, hashed_passwd, staff_type):
        # Logic to add a staff member
        pass

class Admin(Manager):
    def __init__(self, staff_id, password):
        super().__init__(staff_id, password)
        self.type = 2  # Type for Admin

    def remove_staff(self, staff_id):
        # Logic to remove a staff member
        pass