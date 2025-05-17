"""
Data Handler for SDL2 Canvas Integration.
"""
import os
import json
import logging
import pandas as pd
from typing import Dict, Any, Optional, Union, List
import requests
from src.utils.config import SDL2_API_BASE_URL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("data_handler")


class DataHandler:
    """Handler for data operations between Canvas and SDL2."""

    def __init__(self, base_url: str = SDL2_API_BASE_URL):
        """
        Initialize the data handler.

        Args:
            base_url: Base URL for the SDL2 API
        """
        self.base_url = base_url

    def upload_csv(self, csv_file: str) -> str:
        """
        Upload a CSV file to SDL2.

        Args:
            csv_file: Path to the CSV file

        Returns:
            ID of the uploaded CSV
        """
        endpoint = f"{self.base_url}/upload/"

        try:
            with open(csv_file, 'rb') as f:
                files = {'file': (os.path.basename(csv_file), f, 'text/csv')}
                response = requests.post(endpoint, files=files)
                response.raise_for_status()
                result = response.json()
                logger.info(f"Uploaded CSV file {csv_file}, got ID: {result['id']}")
                return result['id']
        except Exception as e:
            logger.error(f"Error uploading CSV file: {str(e)}")
            raise

    def download_csv(self, csv_id: str, output_file: str) -> None:
        """
        Download a CSV file from SDL2.

        Args:
            csv_id: ID of the CSV to download
            output_file: Path to save the CSV file
        """
        endpoint = f"{self.base_url}/csv/{csv_id}"

        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            csv_data = response.json()

            # Write the CSV content to the output file
            with open(output_file, 'w') as f:
                f.write(csv_data['content'])

            logger.info(f"Downloaded CSV {csv_id} to {output_file}")
        except Exception as e:
            logger.error(f"Error downloading CSV file: {str(e)}")
            raise

    def csv_to_dataframe(self, csv_id: str) -> pd.DataFrame:
        """
        Get a CSV from SDL2 and convert it to a pandas DataFrame.

        Args:
            csv_id: ID of the CSV to convert

        Returns:
            Pandas DataFrame
        """
        endpoint = f"{self.base_url}/csv/{csv_id}"

        try:
            response = requests.get(endpoint)
            response.raise_for_status()
            csv_data = response.json()

            # Convert CSV content to DataFrame
            import io
            df = pd.read_csv(io.StringIO(csv_data['content']))

            logger.info(f"Converted CSV {csv_id} to DataFrame with shape {df.shape}")
            return df
        except Exception as e:
            logger.error(f"Error converting CSV to DataFrame: {str(e)}")
            raise

    def dataframe_to_csv(self, df: pd.DataFrame, output_file: str) -> None:
        """
        Convert a pandas DataFrame to a CSV file.

        Args:
            df: Pandas DataFrame
            output_file: Path to save the CSV file
        """
        try:
            df.to_csv(output_file, index=False)
            logger.info(f"Saved DataFrame to CSV file {output_file}")
        except Exception as e:
            logger.error(f"Error saving DataFrame to CSV: {str(e)}")
            raise

    def extract_csv_content(self, task_result: Dict[str, Any]) -> Optional[str]:
        """
        Extract CSV content from a task result.

        Args:
            task_result: Task result data

        Returns:
            CSV content or None if not found
        """
        if task_result.get("output") and task_result["output"].get("content"):
            return task_result["output"]["content"]
        return None

    def save_csv_content(self, content: str, output_file: str) -> None:
        """
        Save CSV content to a file.

        Args:
            content: CSV content
            output_file: Path to save the CSV file
        """
        try:
            with open(output_file, 'w') as f:
                f.write(content)
            logger.info(f"Saved CSV content to {output_file}")
        except Exception as e:
            logger.error(f"Error saving CSV content: {str(e)}")
            raise
