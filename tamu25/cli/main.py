from __future__ import annotations

import json
import logging
import os
import platform
from pathlib import Path

import fire
from google.cloud import storage

from tamu25 import get_version
from tamu25.evaluate import full_evaluation
from tamu25.validate import validate_submission

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CLI:
    """TAMU-25 Datathon CLI — validate and evaluate team submissions."""

    # -------- Primary Commands --------
    def validate(
        self,
        submission: str,
        products: str,
        queries_synth: str,
        team: str,
        queries_real: str = None,
        out: str = "validation_report.json",
    ) -> None:
        """
        Validate a team submission JSON file.
        Example:
          tamu25 validate \\
            --submission teams/team_alpha/submission.json \\
            --products data/products.json \\
            --queries_real data/queries_real.json \\
            --queries_synth data/queries_synth.json \\
            --team team_alpha \\
            --out validation_report.json
        
        For synthetic-only validation:
          tamu25 validate \\
            --submission teams/team_alpha/submission.json \\
            --products data/products.json \\
            --queries_synth data/queries_synth.json \\
            --team team_alpha \\
            --out validation_report.json
        """
        queries_real_path = Path(queries_real) if queries_real is not None else None

        report = validate_submission(
            submission_path=Path(submission),
            products_path=Path(products),
            queries_real_path=queries_real_path,
            queries_synth_path=Path(queries_synth),
            team=team,
        )
        Path(out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        status = report.get("status", "failed")
        headline = ":white_check_mark: Validation passed" if status == "passed" else ":x: Validation failed"

        if status == "passed":
            logger.info(f"{headline} for team {team}")
            logger.info(json.dumps(report, indent=2))
        else:
            logger.error(f"{headline} for team {team}")
            logger.error(json.dumps(report, indent=2))
            raise SystemExit(1)

    def evaluate(
        self,
        submission: str,
        labels_synth: str,
        team: str,
        labels_real: str = None,
        out: str = "score_report.json",
    ) -> None:
        """
        Evaluate a validated team submission against golden sets.
        Example:
          tamu25 eval \\
            --submission teams/team_alpha/submission.json \\
            --labels_real data/labels_real.json \\
            --labels_synth data/labels_synth.json \\
            --team team_alpha \\
            --out score_report.json
        
        For synthetic-only evaluation:
          tamu25 eval \\
            --submission teams/team_alpha/submission.json \\
            --labels_synth data/labels_synth.json \\
            --team team_alpha \\
            --out score_report.json
        """
        labels_real_path = Path(labels_real) if labels_real is not None else None

        report = full_evaluation(
            submission_path=Path(submission),
            labels_real_path=labels_real_path,
            labels_synth_path=Path(labels_synth),
            team=team,
        )
        Path(out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        logger.info(f":checkered_flag: Evaluation completed for team {team}")
        logger.info(json.dumps(report, indent=2))

    # -------- Utility Commands --------
    def version(self) -> str:
        """Print the package version."""
        v = get_version()
        logger.info(v)
        return v

    def info(self) -> dict:
        """Print environment and tool metadata (useful for debugging CI/local runs)."""
        info = {
            "tamu25_version": get_version(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cwd": str(Path.cwd()),
            "env": {
                "TEAM_NAME": os.environ.get("TEAM_NAME"),
                "TEAM_DIR": os.environ.get("TEAM_DIR"),
                "SUBMISSION_FILE": os.environ.get("SUBMISSION_FILE"),
                "CI": os.environ.get("CI"),
                "CI_PIPELINE_ID": os.environ.get("CI_PIPELINE_ID"),
            },
        }
        logger.info(json.dumps(info, indent=2))
        return info

    def download_gcs_file(
        self,
        bucket_name: str,
        source_blob_name: str,
        destination_file_name: str,
        credentials_path: str,
    ) -> None:
        """
        Downloads a file from Google Cloud Storage using a service account key file.

        Args:
            bucket_name (str): The name of the GCS bucket.
            source_blob_name (str): The name of the file in the GCS bucket.
            destination_file_name (str): The local path to save the downloaded file.
            credentials_path (str): Path to the service account JSON key file.
        
        Example:
            tamu25 download_gcs_file \\
            --bucket_name my-bucket \\
            --source_blob_name data/labels_synth.json \\
            --destination_file_name ./labels_synth.json \\
            --credentials_path ./service-account-key.json
        """
        try:
            # Initialize the GCS client with the credentials file
            try:
                logger.info(f"Initializing GCS client with credentials from {credentials_path}")
                storage_client = storage.Client()
                logger.info(f"Successfully initialized GCS client with credentials from {credentials_path}")
            except Exception as e:
                logger.error(f"Failed to initialize GCS client: {e}")
                raise

            # Get the bucket
            try:
                logger.info(f"Accessing bucket: {bucket_name}")
                bucket = storage_client.bucket(bucket_name)
            except Exception as e:
                logger.error(f"Failed to access bucket {bucket_name}: {e}")
                raise

            # Get the blob (file) from the bucket
            try:
                blob = bucket.blob(source_blob_name)
                if not blob.exists():
                    raise FileNotFoundError(f"File {source_blob_name} does not exist in bucket {bucket_name}")
                logger.info(f"Found file {source_blob_name} in bucket")
            except Exception as e:
                logger.error(f"Failed to access file {source_blob_name}: {e}")
                raise

            # Resolve the full destination path
            destination_path = Path(destination_file_name).resolve()
            logger.info(f"Downloading to: {destination_path}")

            # Create parent directories if they don't exist
            destination_path.parent.mkdir(parents=True, exist_ok=True)

            # Download the blob to the local file
            try:
                blob.download_to_filename(str(destination_path))
                logger.info(f"Successfully downloaded {source_blob_name} to {destination_path}")
            except Exception as e:
                logger.error(f"Failed to download file: {e}")
                raise

            print(f"File {source_blob_name} downloaded to {destination_file_name}.")
        except Exception as e:
            print(f"An error occurred: {e}")


def main() -> None:
    fire.Fire(CLI)


if __name__ == "__main__":
    main()
