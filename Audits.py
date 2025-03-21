# A Class which deals managing the the audit logs of the bank.

import mariadb

connector = mariadb.connect(user="Audit", passwd="Audit@Bank", database="Banking")
connection = connector.cursor()

def add_audit_log(action: str, user: str, timestamp: str):
    """
    Adds a new audit log to the Audit table.
    
    Args:
        action(str): The action that was performed.
        user(str): The user who performed the action.
        timestamp(str): The timestamp of the action.
    
    Returns:
        None
    """
    print("Adding %s to Audit table..." % action)
    connection.execute("INSERT INTO Audit (`Action`,`User`, `Timestamp`) VALUES ('%s','%s', '%s')" % (action,user, timestamp))
    connector.commit()
    print("Sucessfully added record to Audit table.")

def get_audit_logs(**kwargs) -> list:
    """
    Retrieves audit logs from the Audit table.
    
    Args:
        **kwargs: The search parameters.
        
    Returns:
        list: A list of audit logs.
    """
    print("Retrieving audit logs...")
    query = "SELECT * FROM Audit WHERE "
    for key, value in kwargs.items():
        query += key + " = " + value + " AND "
    
    query = query[:-5]
    connection.execute(query)
    result = connection.fetchall()
    print("Sucessfully retrieved audit logs.")
    return result

def export_audit_logs(path: str, format="csv", **kwargs):
    """
    Exports audit logs to a file.
    
    Args:
        path(str): The path to the file.
        format(str): The format of the file.
        **kwargs: The search parameters.
    
    Returns:
        None
    """
    print("Exporting audit logs...")
    logs = get_audit_logs(**kwargs)
    if format == "csv":
        file = open(path,"w")
        for log in logs:
            file.write(",".join(log) + "\n")
        file.close()
    elif format == "json":
        import json
        file = open(path,"w")
        json.dump(logs,file)
        file.close()
    print("Sucessfully exported audit logs.")