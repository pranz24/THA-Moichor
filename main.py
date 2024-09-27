import os
import sys
import json
import time
import logging
import pydicom
import requests
import argparse
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load the .anv file
load_dotenv()
LOG_LEVEL = os.getenv('LOG_LEVEL')
METADATA_URL = os.getenv('MD_URL')
METADATA_KEY = os.getenv('MD_KEY')
UPLOAD_URL = os.getenv('U_URL')
UPLOAD_KEY = os.getenv('U_KEY')
ANALYTICS_URL = os.getenv('A_URL')
ANALYTICS_KEY = os.getenv('A_KEY')

"""
Update tags in all dicom images with fetched metadata.
Get Image tags -> Update tags if needed -> overwrite the existing image with updated tags

Tag References:
https://dicom.innolitics.com/ciods
https://www.dicomlibrary.com/dicom/dicom-tags/
"""
def update_image_tags(img, metadata):
    logger.debug(f"update image tag -> Image - {img}, Metadata - {metadata}")
    ds = pydicom.filereader.dcmread(img)

    # Update the tags if needed
    if ds.PatientName != metadata["patient-name"]:
        ds.PatientName = metadata["patient-name"]

    if ds.PatientSpeciesDescription != metadata["request_species"]:
        ds.PatientSpeciesDescription = metadata["request_species"]

    if ds.BarcodeValue != metadata["test_type"]:
        ds.BarcodeValue = metadata["test_type"]

    if ds.InstitutionName != metadata["clinic-name"]:
        ds.InstitutionName = metadata["clinic-name"]

    if ds.PatientID != metadata["patient_id"]:
        ds.PatientID = metadata["patient_id"]

    # Save the changes made to the DICOM file
    ds.save_as(img)
    logger.info(f"Tags verified and updated successfully for {img}")


"""
Make API requests using exponential backoff.
This makes a request retry up upto a certain number at exponential interval of time.

https://stackoverflow.com/questions/69855084/retry-with-python-requests-when-status-code-200
https://medium.com/@roopa.kushtagi/decoding-exponential-backoff-a-blueprint-for-robust-communication-de21459aa98f
"""
def make_api_request(max_retry, api_type, url, data, headers, backoff_in_seconds=3):
    attempts = 1
    while True:
        try:
            if (api_type == "get"):
                r = requests.get(url, data=data, headers=headers)
            elif (api_type == "post"):
                r = requests.post(url, data=data, headers=headers)
            return r
        except Exception as err:
            logger.warning(err)
            if attempts > max_retry:
                logger.error("Maximum number of attempts exceeded, aborting.")
                return False

            sleep = backoff_in_seconds * 2 ** (attempts - 1)
            logger.info(f"Retrying request (attempt #{attempts}) in {sleep} seconds...")
            time.sleep(sleep)
            attempts += 1


"""
Fetch metadata from the given API endpoint
Configure the API request -> Make API request -> return API response
"""
def fetch_metadata(sample_id, priority, max_retry):
    url = METADATA_URL

    payload = {
            "sample_id": sample_id,
            "priority": priority
            }

    headers = {
        "content-type": "application/json",
        "x-api-key": METADATA_KEY
        }

    response = make_api_request(
            max_retry=max_retry,
            api_type="get",
            url=url,
            data=json.dumps(payload),
            headers=headers
            )

    if not response:
        return False
    elif (response.status_code == requests.codes.ok):
        logger.info(f"Metadata API -> Received Status Code: {response.status_code}")
        logger.debug(f"Metedata API -> Received Payload: {response.json()}")
        return response.json()
    else:
        logger.error(f"Metadata API -> Received Status Code: {response.status_code}")
        return False


"""
Upload all images to given API endpoint.
Verify tags before uploading.
Check dicom images in directory -> Configure API request
-> Update image tags -> upload image
"""
def upload_imgs(filepath, metadata, max_retry):
    # Find all dicom files in the directory
    get_imgs = list(Path(filepath).rglob("*.[dD][cC][mM]"))

    # Verify if there are more than one file in the directory
    if (len(get_imgs) == 0):
        logger.error("No DICOM file in the path provided.")
        return False

    logger.debug(f"List of imgs found: {get_imgs}")

    # Setup API request parameters
    url = UPLOAD_URL

    headers = {
            "content-type": "application/binary",
            "Authorization": UPLOAD_KEY
            }

    for img in get_imgs:
        update_image_tags(img, metadata)

        data = open(img, 'rb').read()

        logger.debug(f"Image Upload API -> Uploading {img}")

        response = make_api_request(
                max_retry=max_retry,
                api_type="post",
                url=url,
                data=data,
                headers=headers
                )

        if not response:
            return False
        elif (response.status_code == requests.codes.ok):
            logger.info(f"Image Upload API -> Received Status Code: {response.status_code} - Image: {img}")
            logger.debug(f"Image Upload API -> Received Payload: {response.json()}")
        else:
            logger.error(f"Image Uplaod API -> Received Status Code: {response.status_code}")
            return False

    logger.info("Successfully uploaded all images")
    return True


"""
Trigger Analytics using the given API endpoint.
Configure the API request -> Make API request -> return API response
"""
def trigger_analytics(sample_id, request_type, max_retry):
    url = ANALYTICS_URL

    payload = {
            "sample_id": sample_id,
            "request_type": request_type
            }

    headers = {
        "content-type": "application/json",
        "x-api-key": ANALYTICS_KEY
        }

    response = make_api_request(
            max_retry=max_retry,
            api_type="get",
            url=url,
            data=json.dumps(payload),
            headers=headers
            )

    if not response:
        return False
    elif (response.status_code == requests.codes.ok):
        logger.info(f"Analytics API -> Received Status Code: {response.status_code}")
        logger.debug(f"Analytics API -> Received Payload: {response.json()}")
        return response.json()
    else:
        logger.error(f"Analytics API -> Received Status Code: {response.status_code}")
        return False


if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description='Moichor Image Upload Script Args')
    parser.add_argument('--sample_id', type=str, default="ref0000022tes-cbc",
                        help='Sample ID (default: ref0000022tes-cbc)')
    parser.add_argument('--max_retry', type=int, default=3,
                        help='Number of attempts before declaring failure')
    parser.add_argument('--attempt_number', type=int, default=1,
                        help='Workaround for "Already Stored" response - PatientID tag (default: False)')
    parser.add_argument('--directory', type=str, default="./data/",
                        help='Path to the directory where dicom images are stored')
    parser.add_argument('--console_logs', type=bool, default=False,
                        help='Print logs in terminal/stdout (default: False)')
    args = parser.parse_args()

    # Setup log handler - Add stdout if enabled
    if args.console_logs:
        log_handler = [
                logging.FileHandler(f"moichor-{args.sample_id}-{args.attempt_number}.log", mode="w"),
                logging.StreamHandler(sys.stdout)
                ]
    else:
        log_handler = [
                logging.FileHandler(f"moichor-{args.sample_id}-{args.attempt_number}.log", mode="w")
                ]

    # Configure Logs
    log_level = logging.getLevelName(LOG_LEVEL)
    logging.basicConfig(
                    format='%(asctime)s | [%(levelname)s] | %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=log_level,
                    handlers=log_handler
                    )

    logger = logging.getLogger()

    # Fetch Metadata
    logger.info("Fetching Metadata...")
    md = fetch_metadata(args.sample_id, 2, args.max_retry)
    if not md:
        logger.error("Exiting -> Unable to fetch metadata")
        sys.exit(1)

    # PatientID tag: <sample-ID>-<attempt-number>.
    # https://stackoverflow.com/questions/339007/how-do-i-pad-a-string-with-zeros
    md["patient_id"] = args.sample_id + "-" + str(args.attempt_number).zfill(3)

    # Upload Images to endpoint
    logger.info("Upload images to endpoint...")
    if not (upload_imgs(args.directory, md, args.max_retry)):
        logger.error("Exiting -> Unable to upload images")
        sys.exit(1)

    # Trigger Analytics
    logger.info("Trigger Analytics...")
    analysis = trigger_analytics(args.sample_id, md["test_type"], args.max_retry)
    if not analysis:
        logger.error("Exiting -> Unable to trigger analytics")
        sys.exit(1)

    logger.info(analysis)
