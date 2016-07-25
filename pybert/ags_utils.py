__author__ = 'gmh148'

# Import needed modules
import urllib
import urllib2
import socket
import contextlib
import json
import sys
# For reading passwords without echoing
import getpass


def submit_request(request):
    """
    Returns the response from an HTTP request in json format.

    :param request: request to be sent via HTTP
    :return: json-format response from the parameter request
    """
    with contextlib.closing(urllib2.urlopen(request)) as response:
        job_info = json.load(response)
        return job_info


def get_PortalToken(username,
                    password,
                    server_url="",
                    portal_url=""):
    """
    Returns an authentication token for use in ArcGIS Online.

    :param username: username to be used for the Portal token
    :param password: password for the username to be used for the Portal token
    :return: Token if successful; exception if unsuccessful
    """

    # Set the username and password parameters before
    # getting the token.
    params = {"username": username,
              "password": password,
              "referer": "{0}/arcgis".format(server_url),
              "ip": socket.gethostbyname(socket.gethostname()),
              "f": "json"}
    # Establish the token url and point it at a designated portal
    token_url = "{0}/sharing/rest/generateToken".format(portal_url)
    # Send the request using urllib2
    request = urllib2.Request(token_url, urllib.urlencode(params))
    print("Getting Portal token...")
    # Use the submit_request function to receive a json response
    tokenResponse = submit_request(request)
    # If a token is present in tokenResponse's JSON...
    if "token" in tokenResponse:
        # Retrieve the token
        token = tokenResponse.get("token")
        print("Success")
        # Return the token
        return token
    # If a token is NOT present in tokenResponse's JSON...
    else:
        # If an error is present in tokenResponse...
        if "error" in tokenResponse:
            # Retrieve the error
            error_mess = tokenResponse.get("error", {}).get("message")
            # Raise an exception
            raise Exception("Portal error: {} ".format(error_mess))


def get_AGSToken(username, password):
    """
    Returns an authentication token for use in ArcGIS Server (AGS).

    :param username: username to be used for the AGS token
    :param password: password for the username to be used for the AGS token
    :return: Token if successful; exception if unsuccessful
    """

    # Set the username and password parameters before
    # getting the token.
    params = {"username": username,
              "password": password,
              "client": "ip",
              "ip": socket.gethostbyname(socket.gethostname()),
              "f": "json"}

    token_url = "{}/generateToken".format(
        "")
    request = urllib2.Request(token_url, urllib.urlencode(params))
    print("Getting Server token...")
    tokenResponse = submit_request(request)
    if "token" in tokenResponse:
        token = tokenResponse.get("token")
        print("Success")
        return token
    else:
        if "error" in tokenResponse:
            error_mess = tokenResponse.get("error", {}).get("message")
            raise Exception("Server error: {} ".format(error_mess))


def PortalToken_to_ServerToken(PortalToken):
    """
    Exchanges a Portal Token for a Server Token to provide access to
    restricted resources hosted on a Server federated with Portal
    """
    params = {"token": PortalToken,
              "serverURL": "",
              "f": "json"}
    tokenURL = "{}/generateToken".format(
        "")
    request = urllib2.Request(tokenURL, urllib.urlencode(params))
    print("Exchanging Portal token for Server token...")
    tokenResponse = submit_request(request)
    if "token" in tokenResponse:
        token = tokenResponse.get("token")
        print("Success")
        return token
    else:
        if "error" in tokenResponse:
            error_mess = tokenResponse.get("error", {}).get("message")
            raise Exception("Token Exchange error: {} ".format(error_mess))