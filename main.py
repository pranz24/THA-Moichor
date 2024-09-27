import os
import sys
import json
import logging
import pydicom
import requests
import argparse
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load the .anv file
load_dotenv()

METADATA_URL = os.getenv('MD_URL')
METADATA_KEY = os.getenv('MD_KEY')
UPLOAD_URL = os.getenv('U_URL')
UPLOAD_KEY = os.getenv('U_KEY')
ANALYTICS_URL = os.getenv('A_URL')
ANALYTICS_KEY = os.getenv('A_KEY')


"""
Verify if the tags exists and the values are correct.
"""
def verify_tags(img, metadata):
    ds = pydicom.filereader.dcmread(img)
    try:
        assert(ds.PatientName == metadata["patient-name"])  # Patient's Name
        assert(ds.PatientSpeciesDescription == metadata['request_species'])  # Patient Species Description
        assert(ds.BarcodeValue == metadata['test_type'])   # Barcode Value
        assert(ds.InstitutionName == metadata['clinic-name'])  # Institution Name
        assert(ds.PatientID == metadata['patient_id'])
        return True
    except AssertionError as err:
        logger.error(f"Tag mismatch: {err}")
        #logger.error(traceback.format_exc())
        return False


"""
Exponential Backoff. This makes a request retry up to attempts set above with exponential backoff.
https://stackoverflow.com/questions/69855084/retry-with-python-requests-when-status-code-200
https://medium.com/@roopa.kushtagi/decoding-exponential-backoff-a-blueprint-for-robust-communication-de21459aa98f
"""
def make_api_request(max_retry, api_type, url, data, headers, backoff_in_seconds=2):
    attempts = 1
    while True:
        try:
            if (api_type == "get"):
                r = requests.get(url, data=data, headers=headers)
            elif (api_type == "post"):
                r = requests.post(url, data=data, headers=headers)
            r.status_code == requests.codes.ok
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
"""
def fetch_metadata(sample_id, priority, max_retry):
    url = METADATA_URL

    payload = {"sample_id": sample_id, "priority": priority}

    headers = {
        "content-type": "application/json", 
        "x-api-key": METADATA_KEY
        }
    
    
    response = make_api_request(max_retry=max_retry, api_type="get", url=url, data=json.dumps(payload), headers=headers)
    
    if (response == False):
        return False
    elif (response.status_code == requests.codes.ok):
        logger.info(f"Metadata API -> Received Status Code: {response.status_code}")
        logger.debug(f"Metedata API -> Received Payload: {response.json()}")
        return response.json()
    else:
        logger.error(f"Metadata API -> Received Status Code: {response.status_code}")
        return False



"""
Update tags in all dicom images with fetched metadata.
Read image in directory -> Update tags -> overwrite the existing image with updated tags

Tag References:
https://dicom.innolitics.com/ciods
https://www.dicomlibrary.com/dicom/dicom-tags/
"""
def update_image_tags(filepath, metadata):
    # Find all dicom files in the directory
    get_imgs = list(Path(filepath).rglob("*.[dD][cC][mM]"))
    
    # Verify if there are more than one file in the directory
    if (len(get_imgs) == 0):
        log.error("No DICOM file in the path provided.")
        return False

    logger.debug(f"List of imgs found: {get_imgs}")
    
    # Update images one by one
    for img in get_imgs:
        # Read all tags for image
        ds = pydicom.filereader.dcmread(img)
        
        ds.PatientName = metadata["patient-name"]  # Patient's Name
        ds.PatientSpeciesDescription = metadata['request_species']  # Patient Species Description
        ds.BarcodeValue = metadata['test_type']   # Barcode Value
        ds.InstitutionName = metadata['clinic-name']  # Institution Name
        ds.PatientID = metadata['patient_id']  # Patient ID
        
        # overrite the dcm file with updated tags
        ds.save_as(img)
        logger.debug(f"Image updated - {img}")

    logger.info("Successfully updated all images")
    return True



"""
Upload all images to given API endpoint.
Verify tags before uploading.
"""
def upload_imgs(filepath, metadata, max_retry):
    # Find all dicom files in the directory
    get_imgs = list(Path(filepath).rglob("*.[dD][cC][mM]"))
    
    # Verify if there are more than one file in the directory
    if (len(get_imgs) == 0):
        log.error("No DICOM file in the path provided.")
        return False
    
    logger.debug(f"List of imgs found: {get_imgs}")
    
    # Setup API request parameters
    url = UPLOAD_URL
    
    headers = {
            "content-type": "application/binary",
            "Authorization": UPLOAD_KEY
            }
    
    for img in get_imgs:
        if (verify_tags(img, metadata) == False):
            return False
        
        data = open(img, 'rb').read()

        logger.info(f"Image Upload API -> Uploading {img}")
        

        response = make_api_request(max_retry=max_retry, api_type="post", url=url, data=data, headers=headers)
    
        if (response == False):
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
"""
def trigger_analytics(sample_id, request_type, max_retry):
    url = ANALYTICS_URL

    payload = {"sample_id": sample_id, "request_type": request_type}

    headers = {
        "content-type": "application/json", 
        "x-api-key": ANALYTICS_KEY
        }

    response = make_api_request(max_retry=max_retry, api_type="get", url=url, data=json.dumps(payload), headers=headers)
    
    if (response == False):
        return False
    elif (response.status_code == requests.codes.ok):
        logger.info(f"Analytics API -> Received Status Code: {response.status_code}")
        logger.debug(f"Analytics API -> Received Payload: {response.json()}")
        return response.json()
    else:
        logger.error(f"Analytics API -> Received Status Code: {response.status_code}")
        return False



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Moichor Image Upload Script Args')
    parser.add_argument('--sample_id', type=str, default="ref0000022tes-cbc",
                        help='Sample ID (default: ref0000022tes-cbc)')
    parser.add_argument('--log_level', type=int, default=2,
                        help='Number of attempts before declaring failure')
    parser.add_argument('--attempt_number', type=str, default="001",
                        help='Workaround for "Already Stored" response - PatientID tag [0010, 0020] to: <sample-id>-<attempt-number> (default: False)')
    parser.add_argument('--directory', type=str, default="./data/",
                        help='Path to the directory where dicom images are stored')
    parser.add_argument('--console_logs', type=bool, default=False,
                        help='Print logs in terminal/stdout (default: False)')
    args = parser.parse_args()
    

    # Configure logs - write all logs to moichor.log
    logging.basicConfig(filename='moichor.log',
                    filemode='w',
                    format='%(asctime)s | [%(levelname)s] | %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S',
                    level=logging.INFO)
    
    # Enable stdout for logs
    if args.console_logs == True:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        # set a format which is the same as log file
        formatter = logging.Formatter('%(asctime)s | [%(levelname)s] | %(message)s')
        console.setFormatter(formatter)
        logging.getLogger("").addHandler(console)
    
    logger = logging.getLogger()


    # Fetch Metadata
    logger.info("Fetching Metadata...")
    md = fetch_metadata(args.sample_id, 2, args.backoff_attempts)
    if (md == False):
        logger.error("Exiting -> Unable to fetch metadata")
        sys.exit(1)
    # PatientID tag [0010, 0020] to: <sample-ID>-<attempt-number>.
    md["patient_id"] = args.sample_id + "-" + str(args.attempt_number)


    # Update Images with metadata tags
    logger.info("Updating DICOM with metadata...")
    if (update_image_tags(args.directory, md) == False):
        logger.error("Exiting -> Unable to update image tags")
        sys.exit(1)
 
    # Upload Images to endpoint
    logger.info("Upload images to endpoint...")
    if (upload_imgs(args.directory, md, args.backoff_attempts) == False):
        logger.error("Exiting -> Unable to upload images")
        sys.exit(1)

    # Trigger Analytics
    logger.info("Trigger Analytics...")
    analysis = trigger_analytics(args.sample_id, md["test_type"], args.backoff_attempts)
    logger.info(analysis)

