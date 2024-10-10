from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from utils.return_object import returnObject
from pyyoutube import Client, Api
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow
from urllib.parse import urlparse
import json, datetime, pickle, requests


router = APIRouter(prefix='/auth', tags=['auth'])

client = Client(client_id='id', client_secret='secret')
auth_url = client.get_authorize_url(redirect_uri='https://localhost:8080/auth')[0]

api = Api(api_key='api_key')

session_state = ''

scopes = ['https://www.googleapis.com/auth/youtube.readonly', 
        'https://www.googleapis.com/auth/youtube', 
        'https://www.googleapis.com/auth/youtube.force-ssl', 
        'https://www.googleapis.com/auth/youtube.upload'
        ]

# def store_token(token):
#     with open('auth_token.tkn', 'w') as f:
#         json.dump(token, f)

# def store_refresh_token(token):
#     with open('refresh_token.tkn', 'w') as f:
#         json.dump(token.json, f)

def store_creds(creds):
    with open('credentials.cr', 'wb') as f:
        pickle.dump(creds, f)

def load_creds():
    try:
        f = open('credentials.cr', 'rb')
        creds = pickle.load(f)

        if creds.expired == False:
            client.access_token = creds.token
            api._access_token = creds.token
        #else do refresh flow
        refresh_token = get_refresh_token(creds)
        client.access_token = refresh_token
        api._access_token = refresh_token
    except Exception as ex:
        return returnObject(message="Could not authenticate. ", success=False, data=ex, status_code=500) 

    return returnObject(message="Authenticated!", success=True, data=creds.token, status_code=200)  

def get_refresh_token(creds):
    params = {
            "grant_type": "refresh_token",
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "refresh_token": creds.refresh_token
    }

    authorization_url = "https://oauth2.googleapis.com/token"

    r = requests.post(authorization_url, data=params)

    if r.ok:
        return r.json()['access_token']
    else:
        return None

@router.get('/login')
def login():
    creds_result = load_creds()
    if creds_result.success:
        return returnObject(message="Successfully logged in!", success=True, data=creds_result.data, status_code=200) 
    else:
        # Create the OAuth flow object
        flow = InstalledAppFlow.from_client_secrets_file('client_secret_file', scopes=scopes)
        flow.redirect_uri = urlparse('https://localhost:8080/auth').geturl()
        authorization_url, state = flow.authorization_url(access_type='offline', prompt='select_account')

        # Save the state so we can verify the request later
        global session_state
        session_state = state

        return authorization_url

@router.get("")
async def auth(request: Request):
    if request.query_params['state'] != session_state:
        return returnObject(message="Could not generate token. Invalid state.", success=False, status_code=500)
    
     # Create the OAuth flow object
    flow = InstalledAppFlow.from_client_secrets_file('client_secret_file', scopes=scopes, state=session_state)
    flow.redirect_uri = 'https://localhost:8080/auth'

    # Exchange the authorization code for an access token
    authorization_response = urlparse(request.url._url).geturl()
    flow.fetch_token(authorization_response=authorization_response)

    # Save the credentials to the session
    credentials = flow.credentials

    store_creds(credentials)
    if load_creds().success == False:
        return returnObject(message="Could not authenticate!", success=False, status_code=500)
    
    return returnObject(message="Authenticated!", success=True, status_code=200)

    # try:
    #     token = client.generate_access_token(authorization_response=request.url._url, redirect_uri='https://localhost:8080/auth')
    #     store_token(token)

    #     get_token()
    # except Exception as ex:
    #     return returnObject(message="Could not generate token.", success=False, status_code=500)

@router.get('/get_token')
async def get_token():
    try:
        f = open('auth_token.tkn', 'r')
        token = json.load(f)

        expiration = datetime.datetime.fromtimestamp(float(token['expires_at']))

        if expiration > datetime.datetime.now():
            client.access_token = token['access_token']
            api._access_token = token['access_token']
        else:
            new_token = client.refresh_access_token(refresh_token=token['refresh_token'])
            client.access_token = new_token.access_token
            api._access_token = new_token.access_token
    except Exception as ex:
        print({"message": "Could not authenticate. Redirecting...", "exception": ex})
        try:
            # return RedirectResponse(auth_url)     
            return returnObject(message="Could not authenticate. Redirecting...", success=False,  data=auth_url, status_code=307)     
        except Exception as ex:
            return returnObject(message="Could not redirect for authentication", success=False, status_code=500)
    
    return returnObject(message="Authenticated!", success=True, status_code=200)
