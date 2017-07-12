# OpenTierion

Open Source implementation of the [Tierion](https://tierion.com/) platform, mimicking the REST API provided by 

## Getting started
This library is implemented in Python3 and relies on third party libraries for the REST Server as well as the blockchain integration. 
In order to run the server, the following steps are required:
1. Clone the repository
2. Install dependencies `pip install -r requirements.txt`
3. Configure the blockchain integration
   1. Modify main.py (will likely change soon)
4. Run the server `python main.py`

## API Spec and example use
All the functionality is exposed via a REST API that is designed to be an exact copy of the API specified by [Tierion](https://tierion.com/), for more complete examples on how to use the API please refer to their API docs.
Every Request must include the two custom headers `X-Username: <email>` and `X-Api-Token: <api_token>`. The API token can be retrieved via the user API.

### User management
The server exposes rest endpoints to manage user accounts, the supported operations are as follows:
* **Create User:** `POST` - `http://127.0.0.1:5000/api/v1/accounts`
    
    Payload:
    ```json
    {
     "name": "adam",
     "email": "adam@bdam.net",
     "full_name": "adam bdam",
     "secret": "supersecret"
    }
    ```
    Example: 
    ```
    curl -X POST \
    -H "Content-Type: application/json" \
    -d ' {"name": "adam","email": "adam@bdam.net","full_name": "adam bdam","secret": "supersecret"}' \
    http://127.0.0.1:5000/api/v1/accounts
    ```

* **Delete User:** `DELETE` - `http://127.0.0.1:5000/api/v1/accounts/<account_name>`
 
    Example:
    ```
    curl -X DELETE http://127.0.0.1:5000/api/v1/accounts/adam
    ```
    
* **Get User Info:** `GET` - `http://127.0.0.1:5000/api/v1/accounts/<account_name>`
 
    Example:
    ```
    curl -X GET http://127.0.0.1:5000/api/v1/accounts/adam
    ```
 
 
### Data API
The Data API allows to manage datastores and records. Records are associated with datastores.
 
#### Datastores
The server exposes REST endpoints to for datastore management 
* **Get All Datastores:** `GET` - `http://127.0.0.1:5000/api/v1/datastores` 

    Example:
    ```
    curl -X GET \
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    http://127.0.0.1:5000/api/v1/datastores
    ```

* **Get Datastore:** `GET` - `http://127.0.0.1:5000/api/v1/datastores/<id>`

    Example:
    ```
    curl -X GET \ 
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    http://127.0.0.1:5000/api/v1/datastores/1
    ```

* **Create Datastore:** `POST` - `http://127.0.0.1:5000/api/v1/datastores`
 
     Payload:
     ```json
     {
      "name": "Employee Records",
      "groupName": "",
      "redirectEnabled": false,
      "redirectUrl": null,
      "emailNotificationEnabled": true,
      "emailNotificationAddress": "adam@bdam.net",
      "postDataEnabled": true,
      "postDataUrl": "http://requestb.in/54ahed56h",
      "postReceiptEnabled": false,
      "postReceiptUrl": null
     }
     ```
     Example: 
     ```
     curl -X POST \
     -H "Content-Type: application/json" \
     -H "X-Username: adam@bdam.net" \
     -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
     -d ' {"name": "Employee Records"}' \
     http://127.0.0.1:5000/api/v1/datastores
     ```

* **Update Datastore:** `PUT` - `http://127.0.0.1:5000/api/v1/datastores/<id>`
     
    Payload: - only include fields you wish to update, others remain unchanged
    ```json
    {
     "name": "Employee Records",
     "groupName": "",
     "redirectEnabled": false,
     "redirectUrl": null,
     "emailNotificationEnabled": true,
     "emailNotificationAddress": "adam@bdam.net",
     "postDataEnabled": true,
     "postDataUrl": "http://requestb.in/54ahed56h",
     "postReceiptEnabled": false,
     "postReceiptUrl": null
    }
    ```
    Example: 
    ```
    curl -X PUT \
    -H "Content-Type: application/json" \
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    -d ' {"groupName": "HR"}' \
    http://127.0.0.1:5000/api/v1/datastores/1
    ```

* **Delete Datastore:** `DELETE` - `http://127.0.0.1:5000/api/v1/datastores/<id>`

    Example: 
    ```
    curl -X DELETE \ 
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    http://127.0.0.1:5000/api/v1/datastores/1
    ```

#### Records
The server exposes REST endpoints to manage records
* **Get Records:** `GET` - `http://127.0.0.1:5000/api/v1/records?datastoreId=<datastoreId>`

    [URL Parameters](https://tierion.com/docs/dataapi#api-get-records):
    * datastoreId - datastore ID 
    * page - page
    * pageSize - records per page
    * startDate - start date
    * endDate - end date 
    
    Example:
    ```
    curl -X GET \
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    http://127.0.0.1:5000/api/v1/records?datastoreId=1
    ```

* **Get Record:** `GET` - `http://127.0.0.1:5000/api/v1/records/<id>`

    Example:
    ```
    curl -X GET \
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    http://127.0.0.1:5000/api/v1/records/1
    ```

* **Create Record:** `POST` - `http://127.0.0.1:5000/api/v1/records`

    Payload: Please read the [tierion docs](https://tierion.com/docs/dataapi#api-create-record)    
    ```json
    {
      "datastoreId": 1,
      "name": "Adam",
      "occupation": "Breather"
    }
    ```
    Example:
    ```
    curl -X POST \
    -H "Content-Type: application/json" \
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \ 
    -d ' {"datastoreId": "1", "name", "Adam", "age", "42"}' \
    http://127.0.0.1:5000/api/v1/records
    ```

* **Delete Record:** `DELETE` - `http://127.0.0.1:5000/api/v1/records/<id>`

    Example:
    ```
    curl -X DELETE \
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    http://127.0.0.1:5000/api/v1/records/1
    ```

### Hash API
The server exposes REST endpoints to manage Hashitems

* **Submit Hashitem:** `POST` - `http://127.0.0.1:5000/api/v1/hashitems`

    Payload:
    ```json
    {
      "hash": "9dbd72de6836ce7c05c0c065b474af43598cdaace5deae8054e8efb03cb58d81"
    }
    ```
    Example:
    ```
    curl -X POST \
    -H "Content-Type: application/json" \
    -H "X-Username: adam@bdam.net" \
    -H "X-Api-Key: a84d1cc06b760cfc7fac01677062c4d920bceb5c5639886cbdabb86deadbc22209aed277650a87a08b0187e2cf112dc37f5d062b6da836128c2b4e16b00d8216" \
    -d ' {"hash": "9dbd72de6836ce7c05c0c065b474af43598cdaace5deae8054e8efb03cb58d81"}' \
    http://127.0.0.1:5000/api/v1/hashitems
    ```

* **Get Receipt:** `GET` - `http://127.0.0.1:5000/api/v1/receipts/<id>`

    Example:
    ```
    curl -X GET \  
    -H "X-Username: adam" \
    -H "X-Api-Key: 0c96a84589e6d18b322bb05ad7339a11ebe21ce2f4a4628ccfae2e947b7fd346daf1b5f2114b3f5" \
    http://127.0.0.1:5000/api/v1/receipts/1
    ```