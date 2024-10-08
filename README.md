# Moichor Assignment
Python script designed to handle DICOM images by fetching metadata, updating tags in the images, uploading them to an API endpoint, and triggering analytics on the uploaded images.


### Features
* Fetch metadata from a configurable API endpoint.
* Verify and update DICOM image tags with metadata.
* Upload DICOM images to a given API.
* Trigger analytics after successful uploads.
* Exponential backoff and retry mechanism for handling API failures.
* Logging for troubleshooting and monitoring.

### Future Considerations
* **Log Submission on Failure**
* **Atomic Upload**
* **Concurrent DICOM Image Upload** 
* **Unit Tests**

### Installation

1. Clone the repository:
```
git clone https://github.com/pranz24/THA-Moichor.git
cd THA-Moichor
```

2. Install the required Python packages using `requirements.txt`:
```
pip install -r requirements.txt
```

3. Set the required environment variables:

| Variable     |                     Description                        |
| ------------ | ------------------------------------------------------ |
| `LOG_LEVEL`  | Specifies the logging level (e.g., DEBUG, INFO, ERROR) |
| `MD_URL`     |              The URL for the Metadata API              |
| `MD_KEY`     |        The API key for authenticating Metadata API     |
| `U_URL`      |              The URL for the Upload API                |
| `U_KEY`      |        The API key for authenticating Upload API       |
| `A_URL`      |              The URL for the Analytics API             |
| `A_KEY`      |       The API key for authenticating Analytics API     |


Create a `.env` file:
```
LOG_LEVEL="INFO"
MD_URL="https://example.com/metadata"
MD_KEY="your_metadata_api_key"
U_URL="https://example.com/upload"
U_KEY="your_upload_api_key"
A_URL="https://example.com/analytics"
A_KEY="your_analytics_api_key"

```


Or example (Linux/macOS):
```
export LOG_LEVEL="INFO"
export MD_URL="https://example.com/metadata"
.
.
```

Or Example (Windows):
```
set MD_URL="https://example.com/metadata"
set MD_KEY="your_metadata_api_key"
.
.
```


### Usage

To run the script, use the following command. Make sure the DICOM images you want to process are stored in the specified directory.
```
python main.py --sample_id <SAMPLE_ID> --max_retry <RETRY_COUNT> --attempt_number <ATTEMPT_NO> --directory <DICOM_DIRECTORY> --console_logs <CONSOLE_LOGS>
```

|     Argument       | Type |  Default Value    |                                      Description                                        |
| ------------------ | ---- | ----------------- | --------------------------------------------------------------------------------------- |
|`--sample_id`       | str  | ref0000022tes-cbc |                Sample ID used to fetch metadata and update DICOM tags                   |
|`--max_retry`       | int  |         2         |              Number of retries before declaring failure when calling APIs               |
|`--attempt_number`	 | int  |         1         |    Custom tag used for PatientID field in DICOM images: <sample_id>-<attempt_number>    |
|`--directory`       | str  |     ./data/       | Path to the directory containing DICOM images. (Using absolute path is a good practice) |
|`--console_logs`    | bool |       False       |       Set to True to print logs to the console in addition to writing to log file       |


### Logging

Logs are stored in `moichor-<SAMPLE_ID>-<ATTEMPT_NO>.log` by default. You can enable console logging with the ```--console_logs True``` argument to display logs on the terminal.


![Screenshot_20240926_234357](https://github.com/user-attachments/assets/d0a3073d-8670-4478-bbac-824db8436ca8)


