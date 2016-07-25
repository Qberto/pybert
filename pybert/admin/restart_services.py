__author__ = 'Alberto Nieto'
__version__ = '0.0.1'


# Demonstrates how to stop or start all services in a folder

# Import needed utilities module
import pybert

# For Http calls
import httplib
import urllib
import urllib2
import contextlib
import json
import socket

# For system tools
import sys

# For reading passwords without echoing
import getpass

# For server authentication
from arcrest import security, manageorg


# Defines the entry point into the script
def main(argv=None):
    # Print some info
    print
    print "This tool is a script that stops or starts all services in a folder."
    print

    # Ask for admin/publisher user name and password
    username = raw_input("Enter user name: ")
    password = getpass.getpass("Enter password: ")

    # Ask for server name
    # serverName = raw_input("Enter server name: ")
    serverName = pybert.config.gis_server
    serverPort = pybert.config.gis_server_port

    folder = raw_input("Enter the folder name or ROOT for the root location: (WARNING: Entering ROOT will affect the preconfigured geometry and search services.)")
    # folder = "Dev"
    stopOrStart = raw_input("Enter whether you want to START or STOP all services: ")

    # Check to make sure stop/start parameter is a valid value
    if str.upper(stopOrStart) != "START" and str.upper(stopOrStart) != "STOP":
        print "Invalid STOP/START parameter entered"
        return

    # Get a token
    # token = getToken(username, password, serverName, serverPort)
    # if token == "":
    #     print "Could not generate a token with the username and password provided."
    #     return

    portal_token = pybert.gisserver_utils.get_PortalToken(username, password)
    token = pybert.gisserver_utils.PortalToken_to_ServerToken(portal_token)

    # Construct URL to read folder
    if str.upper(folder) == "ROOT":
        folder = ""
    else:
        folder += "/"

    folderURL = "/arcgis/admin/services/" + folder

    # This request only needs the token and the response formatting parameter
    params = urllib.urlencode({'token': token, 'f': 'json'})
    # params = {'token': token, 'f': 'json'}

    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

    # Connect to URL and post parameters
    httpConn = httplib.HTTPConnection(serverName, serverPort)
    httpConn.request("POST", folderURL, params, headers)
    # httpConn = requests.post()

    # Read response
    response = httpConn.getresponse()
    if (response.status != 200):
        httpConn.close()
        print "Could not read folder information."
        return
    else:
        data = response.read()

        # Check that data returned is not an error object
        if not assertJsonSuccess(data):
            print "Error when reading folder information. " + str(data)
        else:
            print "Processed folder information successfully. Now processing services..."

        # Deserialize response into Python object
        dataObj = json.loads(data)
        httpConn.close()

        # Loop through each service in the folder and stop or start it
        for item in dataObj['services']:

            fullSvcName = item['serviceName'] + "." + item['type']

            # Construct URL to stop or start service, then make the request
            stopOrStartURL = "/arcgis/admin/services/" + folder + fullSvcName + "/" + stopOrStart
            httpConn.request("POST", stopOrStartURL, params, headers)

            # Read stop or start response
            stopStartResponse = httpConn.getresponse()
            if (stopStartResponse.status != 200):
                httpConn.close()
                print "Error while executing stop or start. Please check the URL and try again."
                return
            else:
                stopStartData = stopStartResponse.read()

                # Check that data returned is not an error object
                if not assertJsonSuccess(stopStartData):
                    if str.upper(stopOrStart) == "START":
                        print "Error returned when starting service " + fullSvcName + "."
                    else:
                        print "Error returned when stopping service " + fullSvcName + "."

                    print str(stopStartData)

                else:
                    print "Service " + fullSvcName + " processed successfully."

            httpConn.close()

        return


def submit_request(request):
    """
    Returns the response from an HTTP request in json format.

    :param request: request to be sent via HTTP
    :return: json-format response from the parameter request
    """
    with contextlib.closing(urllib2.urlopen(request)) as response:
        job_info = json.load(response)
        return job_info


def get_PortalToken(username, password, server_path, portal_url):
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
              "referer": server_path + "/arcgis",
              "ip": socket.gethostbyname(socket.gethostname()),
              "f": "json"}
    # Establish the token url and point it at a designated portal
    token_url = "{}/generateToken".format(
        portal_url + "/sharing/rest")
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


# Script start
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))