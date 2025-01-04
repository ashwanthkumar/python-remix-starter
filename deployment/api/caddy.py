# Check README on how to execute this file
import pathlib

from fn import ensure_caddy_installed, get_connection, run_remote, sync_file_as_root
from invoke import UnexpectedExit

deploy_root = pathlib.Path(__file__).parent.resolve()

with get_connection() as conn:
    try:
        ensure_caddy_installed()

        syncd = sync_file_as_root(f"{deploy_root}/Caddyfile", "/etc/caddy/Caddyfile")
        if syncd:
            run_remote(conn, "systemctl reload caddy", use_sudo=True)

    except UnexpectedExit as e:
        print(f"An error occurred: {e}")
