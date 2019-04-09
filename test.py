import requests
import json
from flask import Flask
from flask import jsonify

def update_max_count_list(max_count_list, repo, repo_stats):
    if len(max_count_list) == 0:
        max_count_list.append((repo, repo_stats))
    elif len(max_count_list) == 1:
        if repo_stats["downloadCount"] < max_count_list[0][1]["downloadCount"]:
            repo_0, repo_stats_0 = max_count_list.pop()
            max_count_list.append((repo, repo_stats))
            max_count_list.append((repo_0, repo_stats_0))
        else:
            max_count_list.append((repo, repo_stats))
    else:
        if repo_stats["downloadCount"] < max_count_list[0][1]["downloadCount"]:
            return
        repo_1, repo_stats_1 = max_count_list.pop()
        repo_0, repo_stats_0 = max_count_list.pop()                
        if repo_stats["downloadCount"] >= repo_stats_1["downloadCount"]:
            max_count_list.append((repo_1, repo_stats_1))
            max_count_list.append((repo, repo_stats))
        else:
            max_count_list.append((repo, repo_stats))
            max_count_list.append((repo_1, repo_stats_1))



def get_max2():    
    url = "http://35.239.130.206/artifactory/api/search/aql"

    payload = "items.find(\n    {\n        \"repo\":{\"$eq\":\"jcenter-cache\"}\n} )"
    headers = {'Authorization': "Basic YWRtaW46MmtRZ3FucEF4Wg=="}
    response = requests.request("POST", url, data=payload, headers=headers)
    response_json = response.json()
    repo_list = response_json['results']
    querystring = {"stats":""}
    payload = ""
    headers = {'Authorization': "Basic YWRtaW46MmtRZ3FucEF4Wg=="}
    max_count_list = []


    for repo in repo_list:
        if repo['name'].endswith('jar'):
            path = ' http://35.239.130.206/artifactory/api/storage/' + repo['repo'] + '/' + repo['path'] + '/' + repo['name']
            response = requests.request("GET", path, data=payload, headers=headers, params=querystring)
            repo_stats = response.json()
            count = repo_stats["downloadCount"]
            print(count, '->', path)
            update_max_count_list(max_count_list, repo, repo_stats)

    print("Top 2")
    output = []
    for item in max_count_list:
        repo, repo_stats = item
        path = ' http://35.239.130.206/artifactory/api/storage/' + repo['repo'] + '/' + repo['path'] + '/' + repo['name']
        count = repo_stats["downloadCount"]
        print(count, '->', path)
        output.append(path)
    return output


app = Flask(__name__)
@app.route('/')
def hello_world():
    #return "hello"
    return jsonify(get_max2())

app.run(debug=True, host='0.0.0.0')
        
