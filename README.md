# Banking_API
A Banking Management System written in python.

# Software used
1. Python 3.10.2 (A high-level easy to use scripting language)
2. 15.1 Distrib 10.6.5-MariaDB (An open-source fork of MySQL with additional features)
3. Visual Studio Code (A proprietary text editor by Microsoft) #Check VSCodium
4. Neofetch (An open-source text editor, fork of VIM)
5. DBeaver 21.3.3.202201242151 (Free and open-source multi-platform database tool)
6. Git (Git is a free and open source distributed version control system)
7. fish - the friendly interactive shell (An open-source shell with smart and user-friendly command line shell for macOS, Linux with autocompletion, and many more useful features)
8. MyCLI (An open-source Terminal Client for MySQL with AutoCompletion and Syntax Highlighting)

# Services used
1. Github
2. Tabnine Autocomplete
3. Github Copilot

# Modules used
1. hashlib for sha3_512 (Used to store passwords)
2. mariadb (A connector for mariadb written in C)
3. pycryptodome for Public and Private key generation.

# Working
This project is basically a bunch of APIs linked with one another to make a BARE-BONE Banking Management System.
The APIs are:
1. People.py: For inserting People into the database.
2. Staffs.py: Contains the APIs needed for Auth and managing the database.
3. Accounts.py: Contains the APIs for changing the state of an account.
4. Users.py: Contains the APIs for the user to interact with his/her account.

CLI.py is the interface which binds all the other APIs into a working program.

# Requirements
1. Python 3.6 (mariadb module doesn't support any lower version of python)
2. Mariadb (RDBMS used instead of MySQL)

# Hardware used during production:
Many different systems were used in the production, but most of the code was written on my machine with the following specs.

  1. OS: Arch Linux x86_64   
  2. Kernel: 5.16.7-arch1-1 
  3. Shell: fish 3.3.1 
  4. CPU: Intel Pentium N3540 (4) @ 2.665GHz 
  5. GPU: Intel Atom Processor Z36xxx/Z37xxx Series Graphics & Display 
  6. Memory: 3811MiB

NOTE: These specs are not necessary for the working for the APIs.

# How to use.
1. Install Python 
2. Install Mariadb
3. Install the required modules using requirements.txt
   `python3 -m pip -r requirements.txt`
4. Clone the repository and cd into it.
5. Run the `Start.py` script to initialize the database and create dummy tables.
6. Test the project by running the script `test.py`
7. Relaunch `Start.py` after running `test.py` as the script will truncate all the existing tables.
8. Run `python3 CLI.py` in the terminal.

# Note

Details of the dummy users are stored in config/people_date.txt

# Contribution
I am really grateful to everyone who has contributed in any of the above specified projects, without any one of them this entire project would be much harder to made and test.
The list of sites I visited during the making will be References.md 

