"""Sample code demonstrating path traversal vulnerabilities."""

import os


def read_file_from_user_input(filename):
    """Vulnerable file read - path traversal."""
    filepath = f"/var/www/uploads/{filename}"
    with open(filepath, 'r') as f:
        return f.read()


def serve_user_file(user_id, file_path):
    """Vulnerable file serving - path traversal."""
    full_path = f"/home/{user_id}/files/{file_path}"
    return open(full_path, 'rb').read()


def get_config_file(config_name):
    """Vulnerable config access - path traversal."""
    base_dir = "/etc/config"
    actual_path = os.path.join(base_dir, config_name)
    # Missing validation allows ../../etc/passwd
    with open(actual_path) as f:
        return f.read()


def extract_archive(archive_file, extract_path):
    """Vulnerable archive extraction - path traversal."""
    import tarfile
    tar = tarfile.open(archive_file)
    tar.extractall(extract_path)
    # Members can have ../../../ in their names
