"""
  Program to provide the top 2 downloaded artifacts.
"""
import requests
import json
from flask import Flask, Response
from flask import jsonify

SERVER_IP = "35.232.202.36"
AUTH_HEADER = {"Authorization": "Basic YWRtaW46Nm0xVGRhblNpYg=="}
POST = "POST"
SERVER_ERROR = 500

# Global list to maintain Top 2 downloads
top2_list = []

def get_repo_list():
    """
    Wrapper around the artifactory/api/search/aql API.
    Provides list of all artifacts in a repository.

    Params:
        None

    Returns:
        status_code: int : HTTP status code
        error: str: error message for debugging
        results: List[dict] : List of dictionaries containing artifact info. 
    """
    # API information
    url = "http://" + SERVER_IP + "/artifactory/api/search/aql"
    payload = "items.find(\n{\n\"repo\":{\"$eq\":\"jcenter-cache\"}\n})"
    results, error = [], ""

    # Issue the request
    try:
        response = requests.post(url, data=payload, headers=AUTH_HEADER, timeout=10)
        status_code = response.status_code
    except Exception as exp:
        # Interesting errors like timeout error might happen
        error = str(exp)
        print(error)
        status_code = SERVER_ERROR

    # Response could be bad or the data could be malformed.
    # Return 500 when there is an error.
    if status_code == requests.codes.ok:
        try:
            response_json = response.json()
            results = response_json['results']
        except ValueError as exp:
            status_code = SERVER_ERROR
            error = "Response from " + url + " not in expected format. Couldnt get repo list."
    else:
        error = "Response from " + url + "failed with error code " + str(status_code)

    if error:
        print(error)        
    return status_code, error, results

def get_repo_count(repo):
    """
    Given repo, path and name provide the download count

    Params:
        repo: repo dictionary
        path: str: path within the repo
        name: str: name of the artifact

    Returns:
        status_code: int : HTTP status code
        error: str: error message for debugging
        results: tuple(fullname: str, count: int) : Tuple of fullpath of the artifact
                                          and download count
    """
    if not repo.get('repo') or not repo.get('path') or not repo.get('name'):
        error = "Missing repo, path or name in repo " + str(repo)
        print(error)
        return SERVER_ERROR, error, ("", "")
    
    base_url = 'http://' + SERVER_IP + '/artifactory/api/storage/'
    repo_fullpath = repo['repo'] + '/' + repo['path'] + '/' + repo['name']
    url = base_url + repo_fullpath
    querystring = {"stats":""}    
    results, error = ("", ""), ""

    try:
        response = requests.get(url, headers=AUTH_HEADER, params=querystring, timeout=10)
        status_code = response.status_code
    except Exception as exp:
        # Interesting errors like timeout error might happen
        error = str(exp)
        print(error)
        status_code = SERVER_ERROR

    # Response could be bad or the data could be malformed.
    # Return 500 when there is an error.
    if status_code == requests.codes.ok:
        try:
            repo_stats = response.json()
            count = repo_stats["downloadCount"]
            results = (repo_fullpath, count)
        except ValueError as exp:
            status_code = SERVER_ERROR
            error = "Response from " + url + " not in expected format. Ignoring this artifact"
    else:
        error = "Response from " + url + "failed with error code " + str(status_code)

    if error:
        print(error)
    return status_code, error, results 

def update_top2_list(result):
    """
    Updates list of top 2 downloaded artifacts

    Params:
        result: tuple(fullname: str, count: int) : Tuple of fullpath of the artifact
                                          and download count
    Returns:
        None
    """    
    top2_list.append(result)
    if len(top2_list) > 2:
        top2_list.sort(key = lambda x: x[1], reverse = True)
        top2_list.pop()

def get_top2_downloads():
    """
    Gets the Top 2 downloaded artifacts

    Params:
        None

    Returns:
        status_code: int : HTTP status code
        error: str: error message for debugging
        results: dict[fullname: str] -> count: int: Dictionary of repo name and count
    """    
    # Get the repo list
    status_code, error, repo_list = get_repo_list()
    if status_code != requests.codes.ok:
        return status_code, error, {}

    # Get the counts for each repo
    for repo in repo_list:
        if repo['name'].endswith('jar'):
            status_code, error, result = get_repo_count(repo)
            if status_code != requests.codes.ok:
                # If we are unable to get a repo count, print error in get_repo_count and continue
                continue
            # Update top2_list
            update_top2_list(result)

    results = {}
    for (name, count) in top2_list:
        results[name] = count
        
    return 200, "", results


app = Flask(__name__)
@app.route('/')
def api_get_top2_downloads():
    """
    API returns a json dictionary/map of top 2 downloaded artifacts along with the count.
    """
    status_code, error, results = get_top2_downloads()
    if status_code != requests.codes.ok:
        return Response("{\"error\": \"" + error + "\"}",status=status_code, mimetype='application/json')
    else:
        return jsonify(results)
app.run(host='0.0.0.0')
        
