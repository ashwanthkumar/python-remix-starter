# API Deployment Guide

## Overview
This document outlines the process for deploying our API infrastructure to production. Please follow these steps carefully to ensure a successful deployment.

## Pre-requisites

### 1. Infrastructure Setup
Before beginning the deployment, you must provision the required infrastructure:

1. Create an EC2 Instance or Setup a Server on Hetzner as required

### 2. Network Configuration
After infrastructure is provisioned, complete these networking steps:

1. If the Elastic IP (EIP) has changed:
   - Update the IP address in `fn.py` configuration file
   - Update DNS records in Namecheap control panel
   - Note: DNS automation is currently manual due to Namecheap API limitations

### 3. Service Deployment
Deploy required services by running the following Fabric scripts from the repository root's virtual environment (`venv`):

1. Deploy reverse proxy:
```bash
python caddy.py
```

2. Deploy database:
```bash
python postgres.py
```

### 4. API Deployment
Deploy the API to the appropriate environment:

1. For staging deployment:
```bash
python stag.py
```

2. For production deployment:
```bash
python prod.py
```

**Important:** Scripts must be run in the order shown above to ensure proper service initialization.

## PostgreSQL Setup Details

### 1. Database Storage
The PostgreSQL database is configured with the following storage paths:
- Main DB data: `/data/postgres_db_data`
- Backup location: `/data/pg_backups`

### 2. Database Configuration
The database runs as a Docker container using:
- PostgreSQL version 16
- Systemd service for automated management
- Container persistence across system reboots

### 3. Backup Configuration
Automated backups are configured with:
- Daily backups at midnight (00:00)
- Backup script location: `/data/pg_backups/postgres.backup.sh`
- Automated backup via cron job
