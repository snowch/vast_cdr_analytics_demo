# Telco Analytics Demo - Step-by-Step Guide

This document provides a step-by-step guide on how to run the entire application, from setting up the environment to deploying and monitoring the services on Docker Swarm.

## Step 0: Prerequisites

Before you begin, ensure you have the following installed and configured on your machine(s):

-   **VAST Data 5.3+ Cluster:** You need a cluster running 5.3 or later.
-   **Docker & Docker Engine:** You need a modern version of Docker installed. The `docker-compose` command should also be available.
-   **Python:** You need Python (3.9 - 3.12) and pip installed on your main machine to run the one-off database initialization script.
-   **Project Files:** You must have the complete project structure and all the files from the previous response.
-   **VAST Cluster Access:** You must have network access to your VAST Cluster and the necessary credentials (Endpoint, Access Key, Secret Key).

## Step 1: Configure Your Environment

The `.env` file is the central place for all your credentials.

1.  Navigate to the project root directory:

    ```bash
    cd telco-analytics-demo
    ```
2.  Open the `.env` file with a text editor.
3.  Fill in the placeholder values with your actual VAST cluster details:

    ```bash
    # .env
    # --- External VAST Service Configuration ---

    # Your external VAST Kafka broker URL
    KAFKA_BROKER_URL=your-cluster-kafka-broker.com:9092

    # Your VAST Database endpoint and S3-style credentials
    VASTDB_ENDPOINT=http://vip-pool.your-cluster.lab
    VASTDB_ACCESS_KEY=YOUR_AWS_ACCESS_KEY_ID
    VASTDB_SECRET_KEY=YOUR_AWS_SECRET_ACCESS_KEY

    VASTDB_BUCKET=YOUR_VASTDB_BUCKET
    VASTDB_SCHEMA=YOUR_VASTDB_SCHEMA
    ```

## Step 2: Initialize the VAST Database Schema

This one-time step creates the necessary tables (subscribers, cdrs, etc.) in your VAST DB instance.

1.  Navigate to the script directory:

    ```bash
    cd vast-db-init
    ```
2.  Create a Python virtual environment and install dependencies:

    ```bash
    # Create and activate a virtual environment (optional but recommended)
    python3 -m venv venv
    source venv/bin/activate

    # Install required packages
    pip install python-dotenv vastdb pyarrow
    ```
3.  Run the setup script:

    ```bash
    python3 setup_vast_tables.py
    ```

    You should see output confirming that it's connecting to VAST and creating the tables. Once this is done, you can deactivate the virtual environment (`deactivate`) and return to the project root directory (`cd ..`).

## Step 3: Initialize the Docker Swarm Cluster

This command turns your Docker host into a Docker Swarm manager, allowing it to deploy and orchestrate services. You only need to do this once.

## Step 3.5: Build the Docker Images

Before deploying the application stack, you need to build the Docker images for the `telco-generator` and `vast-db-connector` services.

1.  Navigate to the project root directory:

    ```bash
    cd telco-analytics-demo
    ```

2.  Build the Docker images:

    ```bash
    docker build -t telco-generator:latest telco-generator
    docker build -t vast-db-connector:latest vast-db-connector
    ```

1.  From your primary machine (the "manager node"), run:

    ```bash
    docker swarm init
    ```

    Docker will print a message confirming the swarm is active and will provide a `docker swarm join` command with a token.
2.  For this demo, running on a single machine is perfectly fine. You can ignore the join token.
3.  If you wanted to create a multi-node cluster, you would run the provided join command on your other machines to have them join the swarm as "worker nodes".

## Step 5: Build and Deploy the Application Stack

Now you will deploy the `telco-generator` and `vast-db-connector` services to your Docker Swarm cluster.

1.  Make sure you are in the project's root directory (`telco-analytics-demo`).
2.  Deploy the stack using the `docker-stack.yml` file:

    ```bash
    docker stack deploy -c docker-stack.yml telco_demo
    ```

    *   `-c docker-stack.yml`: Specifies the compose file to use.
    *   `telco_demo`: This is the name you are giving your stack. All services will be prefixed with this name.

    Docker will start pulling the necessary base images, building your service images (`telco-generator:latest`, `vast-db-connector:latest`), and deploying the replicas. This may take a few minutes on the first run.

## Step 6: Monitor and Verify the Application

Your application is now running. Here are the commands to see what's happening.

1.  List all running services in your stack:

    ```bash
    docker service ls
    ```

    You should see `telco_demo_telco-generator` and `telco_demo_vast-db-connector` with their replica counts (e.g., `4/4` and `2/2`).
2.  Check the status of the individual generator containers:

    ```bash
    docker service ps telco_demo_telco-generator
    ```

    This shows you each replica, its ID, which node it's on, and its current state.
3.  View the logs to see the data generation in real-time: This is the most important step for verification.

    ```bash
    # View the logs for the generator service
    docker service logs -f telco_demo_telco-generator

    # View the logs for the VAST DB connector service
    docker service logs -f telco_demo_vast-db-connector
    ```

    *   The `-f` flag "follows" the log output.
    *   You should see logs from the generator like `[Partition 1] Starting up...`, `EXECUTING SCENARIO`, and the running simulation time.
    *   You should see logs from the connector like `Preparing batch...` and `Successfully inserted batch....`

## Step 7: Scaling the Simulation

To increase the data volume, you can scale the number of generator replicas on the fly.

1.  Update the `docker-stack.yml` file: Change the `replicas: 4` and `TOTAL_PARTITIONS=4` values to your new desired number, for example, `8`.
2.  Scale the service by re-deploying the stack: Docker Swarm is smart enough to only apply the changes.

    ```bash
    # Scale the generator service to 8 replicas
    docker stack deploy -c docker-stack.yml telco_demo
    ```

    Docker will automatically start 4 new generator containers. The new containers will be assigned partition IDs 5, 6, 7, and 8 and will start simulating their subset of subscribers, increasing the overall data volume.

## Step 8: Tearing Down the Stack

When you are finished with the demo, you can remove all the running services with a single command.

1.  Remove the entire application stack:

    ```bash
    docker stack rm telco_demo
    ```
2.  (Optional) Leave the swarm: If you want to turn your Docker host back into a standalone node, run:

    ```bash
    docker swarm leave --force
