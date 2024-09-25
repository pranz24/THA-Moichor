import os
import json
import logging
import pydicom
import requests
import traceback
from pathlib import Path

METADATA_URL = os.getenv('MD_URL')
METADATA_KEY = os.getenv('MD_KEY')
UPLOAD_URL = os.getenv('U_URL')
UPLOAD_KEY = os.getenv('U_KEY')
ANALYTICS_URL = os.getenv('A_URL')
ANALYTICS_API_KEY = os.getenv('A_KEY')


def fetch_metadata(sample_id, priority):
    url = METADATA_URL

    payload = {"sample_id": sample_id, "priority": priority}

    headers = {
        "content-type": "application/json", 
        "x-api-key": METADATA_KEY
        }
    try:
        r = requests.get(url, data=json.dumps(payload), headers=headers)
        assert r.status_code == 200 
        logger.info(f"Metedata API -> Received Payload: {r.json()}")
        data = r.json()
    except Exception as e:
        logger.error(traceback.format_exc())
        data = {}
    return data



def update_imgs(filepath, metadata):
    get_imgs = list(Path(filepath).rglob("*.[dD][cC][mM]"))
    logger.info(f"List of imgs found: {get_imgs}")
    for img in get_imgs:
        # Read all tags for image
        ds = pydicom.filereader.dcmread(img)
        # https://www.dicomlibrary.com/dicom/dicom-tags/
        ds[0x10,0x10].value = metadata['patient-name']  # (0010,0010) Patient's Name
        ds.add_new([0x10,0x2201], 'LO',  metadata['request_species'])  # (0010,2201) Patient Species Description
        ds[0x2200,0x5].value = metadata['test_type']  # (2200, 0005) Barcode Value
        ds[0x8,0x80].value = metadata['clinic-name']  # (0008, 0080) Institution Name
        ## write the dcm file to new directory
        ds.save_as(img)
        logger.info(f"Image saved: updated {img}")



def upload_imgs(filepath):
    pass



def trigger_analytics(sample_id, request_type):
    url = ANALYTICS_URL

    payload = {"sample_id": sample_id, "request_type": priority}

    headers = {
        "content-type": "application/json", 
        "x-api-key": ANALYTICS_KEY
        }
    try:
        r = requests.get(url, data=json.dumps(payload), headers=headers)
        assert r.status_code == 200 
        logger.info(f"Analytics API -> Received Payload: {r.json()}")
        data = r.json()
    except Exception as e:
        logger.error(traceback.format_exc())
        data = {}
    return data




if __name__ == "__main__":
    logging.basicConfig(filename='moichor.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d | [%(levelname)s] | %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
    logger = logging.getLogger()

    logger.info("Fetching Metadata...")
    md = fetch_metadata("ref0000022tes-cbc", 2)

    logger.info("Updating DICOM with metadata...")
    update_imgs('./data/', md)

