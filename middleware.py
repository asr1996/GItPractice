from flask import Flask, request, Response
import requests
import redis

app = Flask(__name__)
cache = redis.Redis(host='cache', port=6379, db=1)


def handle_get_request(path):
    try:
        # Check cache for file
        cached_file = cache.get(path)
        if cached_file:
            return Response(cached_file, mimetype='application/octet-stream')

        # Forward request to file server
        file_server_url = 'http://file_server:1234/api/fileserver/' + path
        # response = requests.get(file_server_url, headers=request.headers, data=request.get_data())
        response = requests.get(file_server_url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx responses

        # Cache file if response is successful
        if response.status_code == 200:
            cache.set(path, response.content)

        return Response(response.content, response.status_code, response.headers.items())

    except requests.exceptions.RequestException as e:
        # Handle error responses from file server
        return Response(str(e), status=500)

    except redis.exceptions.RedisError as e:
        # Handle cache errors
        return Response(str(e), status=500)

    except Exception as e:
        # Handle other errors (e.g. file not found)
        return Response('File not found', status=404)


def handle_put_request(path):
    try:
        # Forward request to file server
        file_server_url = 'http://file_server:1234/api/fileserver/' + path
        # response = requests.put(file_server_url, headers=request.headers, data=request.get_data())
        response = requests.put(file_server_url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx responses

        # Invalidate cache if response is successful
        if response.status_code == 200:
            cache.set(path, request.get_data())

        return Response(response.content, response.status_code, response.headers.items())

    except requests.exceptions.RequestException as e:
        # Handle error responses from file server
        return Response(str(e), status=500)

    except redis.exceptions.RedisError as e:
        # Handle cache errors
        return Response(str(e), status=500)

def handle_delete_request(path):
    try:
        # Forward request to file server
        file_server_url = 'http://file_server:1234/api/fileserver/' + path
        # response = requests.delete(file_server_url, headers=request.headers, data=request.get_data())
        response = requests.delete(file_server_url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx responses

        # Invalidate cache if response is successful
        if response.status_code == 200:
            cache.delete(path)

        return Response(response.content, response.status_code, response.headers.items())

    except requests.exceptions.RequestException as e:
        # Handle error responses from file server
        return Response(str(e), status=500)

    except redis.exceptions.RedisError as e:
        # Handle cache errors
        return Response(str(e), status=500)

@app.route('/api/fileserver/<path:path>', methods=['GET'])
def get_request_handler(path):
    return handle_get_request(path)

@app.route('/api/fileserver/<path:path>', methods=['PUT'])
def put_request_handler(path):
    return handle_put_request(path)

@app.route('/api/fileserver/<path:path>', methods=['DELETE'])
def delete_request_handler(path):
    return handle_delete_request(path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)