# Check README on how to execute this file
import pathlib

from fn import get_connection, install_aws_cli, run_remote, sync_file, sync_file_as_root
from invoke import UnexpectedExit

deploy_root = pathlib.Path(__file__).parent.resolve()

with get_connection() as conn:
    try:
        install_aws_cli()
        run_remote(conn, "mkdir -p /data/postgres_db_data", use_sudo=True)
        run_remote(conn, "mkdir -p /data/pg_backups", use_sudo=True)
        run_remote(conn, "chown -R ubuntu:ubuntu /data/pg_backups", use_sudo=True)
        run_remote(conn, "docker pull postgres:16")
        syncd = sync_file_as_root(
            f"{deploy_root}/postgres.systemctl.service",
            "/etc/systemd/system/postgres.service",
        )
        if syncd:
            run_remote(conn, "systemctl enable postgres", use_sudo=True)
            run_remote(conn, "systemctl daemon-reload", use_sudo=True)
            run_remote(conn, "systemctl restart postgres", use_sudo=True)

        # Setup the postgres backup script
        sync_file(
            f"{deploy_root}/postgres.backup.sh",
            "/data/pg_backups/postgres.backup.sh"
        )
        run_remote(conn, "chmod +x /data/pg_backups/postgres.backup.sh")

        # First, remove any existing backup cron jobs to avoid duplicates
        run_remote(conn, 'crontab -l | grep -v "postgres.backup.sh" | crontab -')

        # Add new cron job
        cron_cmd = '(crontab -l 2>/dev/null; echo "0 0 * * * /data/pg_backups/postgres.backup.sh") | crontab -'
        run_remote(conn, cron_cmd)

        # Verify crontab setup
        print("Verifying crontab setup:")
        run_remote(conn, "crontab -l")
    except UnexpectedExit as e:
        print(f"An error occurred: {e}")
