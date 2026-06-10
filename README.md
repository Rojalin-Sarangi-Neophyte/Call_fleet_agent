# ACME Logistics AI Agent

This project contains the codebase for the ACME Logistics AI Agent, comprising both the backend server and frontend web interface.

## Project Structure

*   `acme_logistics_backend/`: The backend server handling AI agent logic and data management.
*   `acme_logistics_frontend/`: The frontend user interface for interacting with the AI agent.

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js (optional, for serving frontend if needed, but simple HTTP server is sufficient)
- API Keys for the required services (Bolna, OpenAI, Gemini)

### Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd acme_logistics_backend
    ```
2.  Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment variables:
    *   Rename `.env` to `.env` if not already named.
    *   Edit the `.env` file and replace the placeholder values (`your_bolna_api_key_here`, etc.) with your actual API keys.
4.  Start the backend server:
    ```bash
    python main.py
    ```

### Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd acme_logistics_frontend
    ```
2.  Serve the frontend files. You can use a simple HTTP server like Python's built-in server:
    ```bash
    python -m http.server 8080
    ```
3.  Open your browser and navigate to `http://localhost:8080` (or whichever port you specified).

## Important Note on Security
**Do not** commit your `.env` file or any hardcoded API keys to a public GitHub repository. Ensure `.env` is added to your `.gitignore` file.
