# A module that would take a string and ask the user to input as per the string using input()
# and return the result if and only if the string doesn't contain any possible SQL injection code in it.

# The module will throw PossibleSQLInjectionException if the string contains any possible SQL injection code.
# The module will return the string if the string doesn't contain any possible SQL injection code.


# A list containing all SQL Keywords.
from unittest import main


SQL_KEYWORDS = ["'", ";", "--", "\\", "\"", "`", "=", ">", "<", "*", "&", "|", "!", "~", "^", "(", ")", ",", ".", ":", "?","SELECT","INSERT","UPDATE","DELETE","CREATE","DROP","ALTER","TRUNCATE","GRANT","REVOKE","LOCK","UNLOCK","EXPLAIN","DESCRIBE","DESC","HELP","USE","SHOW","BEGIN","COMMIT","ROLLBACK","BACKUP","RESTORE","CACHE","CHECK","ANALYZE","OPTIMIZE","REPAIR","BACKUP","PURGE","IMPORT","EXPORT","LOAD","COPY","INTO","FROM","IN","SET","VALUES","AND","OR","NOT","LIKE","BETWEEN"]

# Creating the PossibleSQLInjectionException class.

class PossibleSQLInjectionException(Exception):
    
    """
    
    The exception that is thrown when the string contains any possible SQL injection code.

    """
    def __init__(self, message):
        super(PossibleSQLInjectionException, self).__init__(message)
    pass
def sql_injection_check(string):
    main_string = input(string)
    temp_string = main_string.upper()
    # If the string contains any of the SQL injection code, throw an exception.
    for i in SQL_KEYWORDS:
        if i in temp_string:
            raise PossibleSQLInjectionException("The string contains possible SQL injection code.")
    # No SQL injection code found, return the string.
    return main_string



