# Moichor Assignment
This repository contains a Python script designed to handle DICOM images by fetching metadata, updating tags in the images, uploading them to an API endpoint, and triggering analytics on the uploaded images. The script employs robust error handling and logging mechanisms, including exponential backoff for retrying API requests.

### Features

    - Fetch metadata from a configurable API endpoint.
    - Verify and update DICOM image tags with metadata.
    - Upload DICOM images to a given API.
    - Trigger analytics after successful uploads.
    - Exponential backoff and retry mechanism for handling API failures.
    - Extensive logging for troubleshooting and monitoring.

### Installation

1. Clone the repository:
```
git clone <repository-url>
cd <repository-directory>
```

2. Install the required Python packages using `requirements.txt`:
```
pip install -r requirements.txt
```

3. Set the required environment variables:
Example (Linux/macOS):
```
export MD_URL="https://example.com/metadata"
export MD_KEY="your_metadata_api_key"
export U_URL="https://example.com/upload"
export U_KEY="your_upload_api_key"
export A_URL="https://example.com/analytics"
export A_KEY="your_analytics_api_key"
```

Example (Windows):
```
set MD_URL="https://example.com/metadata"
set MD_KEY="your_metadata_api_key"
set U_URL="https://example.com/upload"
set U_KEY="your_upload_api_key"
set A_URL="https://example.com/analytics"
set A_KEY="your_analytics_api_key"
```

### Usage

To run the script, use the following command. Make sure the DICOM images you want to process are stored in the specified directory.
```
python main.py --sample_id <SAMPLE_ID> --backoff_attempts <RETRY_COUNT> --attempt_number <ATTEMPT_NO> --directory <DICOM_DIRECTORY> --console_logs <CONSOLE_LOGS>
```

### Logging

Logs are stored in `moichor.log` by default. You can enable console logging with the ```--console_logs True``` argument to display logs on the terminal.

## Resources Used
1. [Reading & Editing DICOM Metadata with Python](https://medium.com/@ashkanpakzad/reading-editing-dicom-metadata-w-python-8204223a59f6)
2. [RESTful API Testing with PyTest: A Complete Guide](https://laerciosantanna.medium.com/mastering-restful-api-testing-with-pytest-56d22460a9c4)
