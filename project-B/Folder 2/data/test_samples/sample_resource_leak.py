"""Sample code demonstrating resource leak vulnerabilities."""

def read_file_without_close(filename):
    """Resource leak - file not closed."""
    f = open(filename)
    content = f.read()
    return content
    # File handle never closed


def database_query_no_cleanup(connection_string):
    """Resource leak - database connection not closed."""
    import sqlite3
    conn = sqlite3.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()
    # Connection never closed


def socket_connection(host, port):
    """Resource leak - socket not closed."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    data = sock.recv(1024)
    return data
    # Socket never closed


def temporary_file_leak(data):
    """Resource leak - temporary file not deleted."""
    import tempfile
    temp = tempfile.NamedTemporaryFile()
    temp.write(data)
    return temp.name
    # Temporary file never deleted


def context_manager_not_used(filename):
    """Resource leak - not using context manager."""
    f = open(filename)
    lines = f.readlines()
    # File should be used with 'with' statement
    return lines
