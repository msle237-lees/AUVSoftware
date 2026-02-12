# AUVSoftware
My version of the KSU AUV team software


# Getting Started
1. Clone the repository:
   ```
    git clone https://github.com/msle237-lees/AUVSoftware.git
    cd AUVSoftware
    python3 -m venv venv
    source venv/bin/activate
   ```
2. Set up the environment variables:
   - Copy the `.env.example` file to `.env`:
     ```
     cp .env.example .env
     ```
   - Edit the `.env` file to include your database credentials and other necessary configurations.
3. Build and run the Docker containers:
    ```
    docker-compose up --d
    ```
4. Initialize the database:
    ```
    pip install -e .
    auv db init
    ```