"""Main entry point for the Multi-Catalog System."""

import os
import subprocess


def main():
    """Main function to run the Multi-Catalog System."""
    # Get the absolute path to the Streamlit app
    script_path = os.path.join(os.path.dirname(__file__), "ui", "streamlit_app.py")

    # Run the Streamlit app using subprocess
    subprocess.run(["streamlit", "run", script_path])


if __name__ == "__main__":
    main()