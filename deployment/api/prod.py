# Check README on how to execute this file
import pathlib

from fn import (
    ensure_venv_and_install_deps,
    get_connection,
    run_command_in_venv,
    run_remote,
    sync_directory,
)
import fn

api_root = pathlib.Path(__file__).parents[2].resolve()
# Remote destination
remote_destination = "/data/api/prod"
deploy_user = fn.remote_username

with get_connection() as conn:
    conn = get_connection()
    run_remote(conn, f"mkdir -p {remote_destination}", use_sudo=True)
    run_remote(
        conn,
        f"chown -R {deploy_user}:{deploy_user} {remote_destination}",
        use_sudo=True,
    )
    print(f"API Root: {api_root}")
    sync_directory(api_root, remote_destination)
    print(f"Copied folder: {api_root} to {remote_destination}")

    ensure_venv_and_install_deps(conn, remote_destination)

    run_command_in_venv(
        conn,
        remote_destination,
        "SQLALCHEMY_DATABASE_URI=postgresql://pgusername:pg-password-to-update@127.0.0.1/pg_db_prod_name flask db upgrade",
        remote_destination,
    )
    run_remote(
        conn,
        f"cp {remote_destination}/deployment/api/production.systemctl.service /etc/systemd/system/api_prod.service",
        use_sudo=True,
    )
    run_remote(conn, "systemctl enable api_prod", use_sudo=True)
    run_remote(conn, "systemctl daemon-reload", use_sudo=True)
    run_remote(conn, "systemctl restart api_prod", use_sudo=True)
    # Check logs on remote machine using: journalctl -xeu api_prod.service
