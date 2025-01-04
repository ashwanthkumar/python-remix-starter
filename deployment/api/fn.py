import hashlib
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, Tuple

from fabric import Connection
from invoke.exceptions import UnexpectedExit
from paramiko.ssh_exception import SSHException
from pathspec import PathSpec
from pathspec.patterns.gitwildmatch import GitWildMatchPattern

# Maximum number of concurrent operations
MAX_CONCURRENT_OPS = 5

# Maximum number of connections in the pool
MAX_CONNECTIONS = 3

# Semaphore to limit concurrent operations
semaphore = threading.Semaphore(MAX_CONCURRENT_OPS)
# Connection pool
connection_pool = []
connection_lock = threading.Lock()
ssh_key_path = "../ec2-ssh-key"
remote_ip = "52.66.108.117"  # Elastic IP
remote_username = "ubuntu"


def get_connection():
    with connection_lock:
        if not connection_pool:
            conn = Connection(
                remote_ip,
                user=remote_username,
                connect_kwargs={
                    "key_filename": os.path.expanduser(ssh_key_path),
                },
            )
            return conn
        return connection_pool.pop()


def release_connection(conn):
    with connection_lock:
        if len(connection_pool) < MAX_CONNECTIONS:
            connection_pool.append(conn)
        else:
            conn.close()


def load_gitignore(directory):
    gitignore_path = os.path.join(directory, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            return PathSpec.from_lines(GitWildMatchPattern, f)
    return PathSpec([])


def get_file_hash(filepath):
    """Calculate MD5 hash of file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def _get_remote_stats(
    conn: Connection, remote_path: str, use_sudo: bool = False
) -> Optional[Tuple[int, datetime]]:
    """Get size and mtime of remote file."""
    cmd = f'stat -c "%s %Y" {remote_path}'
    run_func = conn.sudo if use_sudo else conn.run

    result = run_func(cmd, warn=True, hide=True)
    if result.failed:
        return None

    size, mtime_stamp = map(int, result.stdout.strip().split())
    return size, datetime.fromtimestamp(mtime_stamp)


def _get_remote_hash(conn: Connection, remote_path: str, use_sudo: bool = False) -> str:
    """Get MD5 hash of remote file."""
    cmd = f"md5sum {remote_path}"
    run_func = conn.sudo if use_sudo else conn.run
    return run_func(cmd, hide=True).stdout.split()[0]


def _sync_file_impl(
    conn: Connection, local_path: str, remote_path: str, use_sudo: bool = False
) -> bool:
    """
    Implementation of file synchronization logic.
    Returns True if file was updated, False if unchanged.
    """
    try:
        # Get local file stats
        local_stat = os.stat(local_path)
        local_size = local_stat.st_size
        local_mtime = datetime.fromtimestamp(local_stat.st_mtime)

        # Check remote file
        remote_stats = _get_remote_stats(conn, remote_path, use_sudo)
        if remote_stats is None:
            print(f"Copying new file: {local_path}")
            if use_sudo:
                # Create a temporary file and move it with sudo
                temp_path = f"/tmp/{os.path.basename(remote_path)}.tmp"
                conn.put(local_path, remote=temp_path)
                conn.sudo(f"mv {temp_path} {remote_path}")
            else:
                conn.put(local_path, remote=remote_path)
            return True

        remote_size, remote_mtime = remote_stats

        # Compare size and modification time
        if local_size != remote_size or local_mtime > remote_mtime:
            # If size or mtime is different, compare hashes
            local_hash = get_file_hash(local_path)
            remote_hash = _get_remote_hash(conn, remote_path, use_sudo)

            if local_hash != remote_hash:
                print(f"Updating file: {local_path}")
                if use_sudo:
                    # Create a temporary file and move it with sudo
                    temp_path = f"/tmp/{os.path.basename(remote_path)}.tmp"
                    conn.put(local_path, remote=temp_path)
                    conn.sudo(f"mv {temp_path} {remote_path}")
                else:
                    conn.put(local_path, remote=remote_path)
                return True
            else:
                print(f"File unchanged (hash match): {local_path}")
                return False
        else:
            print(f"File unchanged: {local_path}")
            return False

    except SSHException as e:
        print(f"SSH error for {local_path}: {str(e)}. Retrying...")
        time.sleep(1)
        return _sync_file_impl(conn, local_path, remote_path, use_sudo)


def sync_file(local_path: str, remote_path: str) -> bool:
    """Sync a single file if it has changed."""
    with semaphore:
        conn = get_connection()
        try:
            return _sync_file_impl(conn, local_path, remote_path, use_sudo=False)
        finally:
            release_connection(conn)


def sync_file_as_root(local_path: str, remote_path: str) -> bool:
    """Sync a single file if it has changed, using sudo for remote operations."""
    with semaphore:
        conn = get_connection()
        try:
            return _sync_file_impl(conn, local_path, remote_path, use_sudo=True)
        finally:
            release_connection(conn)


def sync_directory(local_dir, remote_dir):
    """Recursively sync a directory."""
    gitignore = load_gitignore(local_dir)
    tasks = []

    for root, dirs, files in os.walk(local_dir):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not gitignore.match_file(os.path.join(root, d))]

        relative_root = os.path.relpath(root, local_dir)
        remote_root = os.path.join(remote_dir, relative_root)

        # Create remote directory
        conn = get_connection()
        try:
            conn.run(f"mkdir -p {remote_root}")
        finally:
            release_connection(conn)

        # Prepare sync tasks for non-ignored files
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            if not gitignore.match_file(relative_path):
                remote_path = os.path.join(remote_root, file)
                tasks.append((local_path, remote_path))
            else:
                print(f"Ignored: {local_path}")

    # Execute sync tasks in parallel
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_OPS) as executor:
        futures = [
            executor.submit(sync_file, local_path, remote_path)
            for local_path, remote_path in tasks
        ]
        for future in as_completed(futures):
            future.result()  # This will raise any exceptions that occurred during execution


def ensure_venv_and_install_deps(conn, remote_destination):
    # Check if Python 3.11 is available
    result = conn.run("which python3.11", warn=True, hide=True)
    if result.failed:
        # Install required Python packages
        print("Installing Python dependencies...")
        conn.sudo("apt-get update", hide=True)
        conn.sudo(
            "apt-get install -y python3.11 python3.11-venv python3.11-dev python3-pip",
            hide=True,
        )

    venv_path = os.path.join(remote_destination, "venv")
    result = conn.run(
        f'if [ -d "{venv_path}/bin" ]; then echo "exists"; else echo "not exists"; fi',
        hide=True,
    )

    if result.stdout.strip() == "not exists":
        print("Creating virtual environment...")
        conn.run(f"python3.11 -m venv {venv_path}")
    else:
        print("Virtual environment already exists.")

    conn.run(f"{venv_path}/bin/pip install -r {remote_destination}/requirements.txt")


def run_command_in_venv(conn, remote_destination, command, working_dir=None):
    venv_path = os.path.join(remote_destination, "venv", "bin", "activate")
    full_command = f"source {venv_path} && {command}"
    if working_dir:
        conn.run(f"cd {working_dir} && {full_command}")
    else:
        return run_remote(conn, full_command)


def run_remote(conn, command, use_sudo=False):
    run_func = conn.sudo if use_sudo else conn.run
    result = run_func(command, hide=True)
    if result.failed:
        print(f"Command failed: {command}")
    return result.stdout.strip()


def ensure_caddy_installed() -> bool:
    """
    Check if Caddy is installed on Ubuntu and install it if not present.

    Args:
        connection: Fabric Connection object

    Returns:
        bool: True if Caddy was already installed or successfully installed,
              False if installation failed
    """
    with get_connection() as connection:
        try:
            # Use sudo to check if Caddy is installed
            connection.sudo("which caddy", hide=True)
            print("Caddy is already installed")
            return True
        except UnexpectedExit:
            print("Caddy not found. Installing...")
            try:
                # Run all commands with sudo
                connection.sudo(
                    "apt install -y debian-keyring debian-archive-keyring apt-transport-https curl",
                    hide=True,
                )
                connection.sudo(
                    'curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/gpg.key" | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg',
                    hide=True,
                )
                connection.sudo(
                    'curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt" | tee /etc/apt/sources.list.d/caddy-stable.list',
                    hide=True,
                )
                connection.sudo("apt update", hide=True)
                connection.sudo("apt install -y caddy", hide=True)

                print("Successfully installed Caddy")
                return True

            except Exception as e:
                print(f"Failed to install Caddy: {str(e)}")
                return False


def install_aws_cli():
    """
    Install AWS CLI v2 on the remote server if it doesn't exist or upgrade if necessary
    """
    print("Checking AWS CLI installation...")

    with get_connection() as conn:
        # Check if AWS CLI is installed and get its version
        result = conn.sudo("which aws && aws --version", warn=True)

        if result.ok:
            # AWS CLI exists, check if it's v2
            if "aws-cli/2" in result.stdout:
                print("AWS CLI v2 is already installed.")
                return
            else:
                print("AWS CLI v1 found. Upgrading to v2...")
                # Remove AWS CLI v1 if installed via pip
                conn.run("pip uninstall -y awscli", warn=True)
        else:
            print("AWS CLI not found. Installing v2...")

        # Install unzip if not present
        # Install required packages with proper sudo
        conn.sudo("apt-get update")
        conn.sudo("apt-get install -y unzip curl")

        # Clean up any previous installation attempts
        conn.run("rm -rf aws awscliv2.zip", warn=True)

        # Download AWS CLI v2
        conn.run(
            'curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"'
        )

        # Unzip and install AWS CLI
        conn.run("unzip -o awscliv2.zip")

        # Install/Update AWS CLI v2
        # Using --update flag to handle both fresh install and upgrade cases
        conn.sudo("./aws/install --update")

        # Clean up downloaded files
        conn.run("rm -rf aws awscliv2.zip")

        # Verify installation
        result = conn.run("aws --version")
        if "aws-cli/2" not in result.stdout:
            raise Exception("AWS CLI v2 installation failed!")

        print("AWS CLI v2 installation verified successfully!")
