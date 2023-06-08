"""
Filename: server.py
Author: Savannah Alfaro, sea2985
"""
import datetime
import json
import logging
import platform
import subprocess
import sys
import socket
import threading

import requests as requests

import parser


def format_response(status_code, reason, message):
    """
    Formats the server response for a given request.
    :param status_code: (str) the response status code
    :param reason: (str) the response reason
    :param message: (str) the response message
    :return: (str) the HTTP server response
    """
    if message:
        response = "HTTP/1.1 {} {}\n" \
                   "Date: {}\n" \
                   "Server: Webserver\n" \
                   "Content-Length: {}\n" \
                   "Content-Type: text/html\n" \
                   "Connection: Closed\n\n" \
                   "{}".format(status_code, reason, datetime.datetime.now(), len(message), message)
    else:
        response = "HTTP/1.1 {} {}\n" \
                   "Date: {}\n" \
                   "Server: Webserver\n" \
                   "Connection: Closed\n".format(status_code, reason, datetime.datetime.now())
    return response


def handle_get_files(url):
    """
    Handles GET requests for server files.
    :param url: (str) the url of the request
    :return: (str) the HTTP server response
    """
    # variables
    host = url.strip().split("//")[1].strip().split("/")[0]
    file = url.strip().split(host)[1].strip()[1:]
    lines = ""

    # read contents of the file
    try:
        with open(file, 'r') as file:
            for line in file.readlines():
                lines += line
        return format_response(200, "OK", lines)
    except Exception:
        return format_response(404, "File Not Found", "404 Not Found")


def handle_get_php(url):
    """
    Handles GET server side PHP scripting.
    :param url: (str) the url of the request
    :return: (str) the HTTP server response
    """
    # variables
    host = url.strip().split("//")[1].strip().split("/")[0]
    php_file = url.strip().split("?")[0].strip().split(host)[1][1:]
    arguments = url.strip().split("?")[1]

    # write the shell script to file
    with open('Scripts/get_request.sh', 'w') as file:
        file.write("#!/bin/bash\n\n")
        file.write("export GATEWAY_INTERFACE=\"CGI/1.1\"\n")
        file.write("export SCRIPT_FILENAME=\"{}\"\n".format(php_file))
        file.write("export REQUEST_METHOD=\"GET\"\n")
        file.write("export SERVER_PROTOCOL=\"HTTP/1.1\"\n")
        file.write("export QUERY_STRING=\"{}\"\n\n".format(arguments))
        file.write("exec echo | php-cgi")

    # run the shell script on Windows platforms
    if platform.system() == "Windows":
        try:
            proc = subprocess.Popen(['C:\\Program Files\\Git\\bin\\bash.exe', 'Scripts/get_request.sh'], shell=True,
                                    stdout=subprocess.PIPE)
            return format_response(200, "OK", proc.stdout.read().decode())
        except Exception:
            return format_response(500, "Internal Server Error", "500 Internal Server Error")

    # run the shell script on Linux platforms
    if platform.system() == "Linux":
        try:
            proc = subprocess.run(['sh', 'Scripts/get_request.sh'], stdout=subprocess.PIPE)
            return format_response(200, "OK", proc.stdout.decode())
        except Exception:
            return format_response(500, "Internal Server Error", "500 Internal Server Error")


def handle_post_php(url, host, data):
    """
    Handles POST server side PHP scripting.
    :param url: (str) the url of the request
    :param host: (str) the host of the request
    :param data: (str) the data of the request
    :return: (str) the HTTP server response
    """
    # variables
    php_file = url.strip().split("?")[0].strip().split(host)[1][1:]
    json_object = json.loads(data)
    count = len(json_object)
    arguments = ""

    # load all arguments from the body
    for key in json_object:
        arguments += "{}={}".format(key, json_object[key])
        if count != 1:
            arguments += "&"
        count -= 1

    # write the shell script to file
    with open('Scripts/post_request.sh', 'w') as file:
        file.write("#!/bin/bash\n\n")
        file.write("export GATEWAY_INTERFACE=\"CGI/1.1\"\n")
        file.write("export SCRIPT_FILENAME=\"{}\"\n".format(php_file))
        file.write("export REQUEST_METHOD=\"POST\"\n")
        file.write("export SERVER_PROTOCOL=\"HTTP/1.1\"\n")
        file.write("export REMOTE_HOST=\"{}\"\n".format(host))
        file.write("export CONTENT_LENGTH={}\n".format(len(arguments)))
        file.write("export BODY=\"{}\"\n".format(arguments))
        file.write("export CONTENT_TYPE=\"application/x-www-form-urlencoded\"\n\n")
        file.write("exec echo \"$BODY\" | php-cgi")

    # run the shell script on Windows platforms
    if platform.system() == "Windows":
        try:
            proc = subprocess.Popen(['C:\\Program Files\\Git\\bin\\bash.exe', 'Scripts/post_request.sh'], shell=True,
                                    stdout=subprocess.PIPE)
            return format_response(200, "OK", proc.stdout.read().decode())
        except Exception:
            return format_response(500, "Internal Server Error", "500 Internal Server Error")

    # run the shell script on Linux platforms
    if platform.system() == "Linux":
        try:
            proc = subprocess.run(['sh', 'Scripts/post_request.sh'], stdout=subprocess.PIPE)
            return format_response(200, "OK", proc.stdout.decode())
        except Exception:
            return format_response(500, "Internal Server Error", "500 Internal Server Error")


def request_without_data(request_line, lines, protocol):
    """
    Parses through the request to determine the url and host.
    :param request_line: (str) the request line
    :param lines: (str) the remaining request lines
    :param protocol: (str) the request protocol
    :return: (str) url, host
    """
    # variables
    resource_path = request_line.strip().split()[1]
    host = ""

    # iterate through each line of the request
    for line in lines:
        potential = line.strip().split()[0]
        if potential == "Host:":
            host = line.strip().split()[1].strip().split(":")[0]
            break

    # build and return url and host
    url = protocol + "://" + host + resource_path
    return url, host


def request_with_data(request_line, lines, protocol):
    """
    Parses through the request to determine the url, host, and data.
    :param request_line: (str) the request line
    :param lines: (str) the remaining request lines
    :param protocol: (str) the request protocol
    :return: (str) url, host, data
    """
    # variables
    resource_path = request_line.strip().split()[1]
    flag = False
    host = ""
    data = ""

    # iterate through each line of the request
    for line in lines:
        if line == '':
            continue

        # look for host in the request
        potential = line.strip().split()[0]
        if potential == "Host:":
            host = line.strip().split()[1]

        # look for the json data in the request
        if line[0] == '{':
            flag = True
        if flag:
            data += line.strip()

    # build and return url, host, and data
    url = protocol + "://" + host + resource_path
    return url, host, data


def handle_request(request, certificate_file, key_file):
    """
    Handles the client request.
    :param request: (str) the HTTP client request
    :param certificate_file: (str) the certificate filename
    :param key_file: (str) the key filename
    :return: (str) the HTTP server response
    """
    lines = request.strip().split("\n")
    request_line = lines[0]
    method = request_line.strip().split()[0]
    lines.remove(request_line)

    # check to see what protocol is needed
    protocol = "http"
    if certificate_file and key_file:
        protocol = "https"

    # logging information
    print("Request: {}".format(request_line))
    logging.info("Request: {}".format(request_line))

    match method:
        case "GET":
            # variables
            variables = request_without_data(request_line, lines, protocol)
            url = variables[0]
            host = variables[1]

            # send the http GET request
            if protocol == "https":
                if host == "localhost" or host == "127.0.0.1":
                    if ".php" in url:
                        return handle_get_php(url)
                    else:
                        return handle_get_files(url)
                else:
                    request = requests.get(url=url, cert=(certificate_file, key_file))
            else:
                if host == "localhost" or host == "127.0.0.1":
                    if ".php" in url:
                        return handle_get_php(url)
                    else:
                        return handle_get_files(url)
                else:
                    request = requests.get(url)
            return format_response(request.status_code, request.reason, request.text)
        case "POST":
            # variables
            variables = request_with_data(request_line, lines, protocol)
            url = variables[0]
            host = variables[1]
            data = variables[2]

            # send the http POST request
            if protocol == "https":
                if host == "localhost" or host == "127.0.0.1":
                    return handle_post_php(url, host, data)
                else:
                    request = requests.post(url=url, json=data, cert=(certificate_file, key_file))
            else:
                if host == "localhost" or host == "127.0.0.1":
                    return handle_post_php(url, host, data)
                else:
                    request = requests.post(url=url, json=data)
            return format_response(request.status_code, request.reason, None)
        case "PUT":
            # variables
            variables = request_with_data(request_line, lines, protocol)
            url = variables[0]
            data = variables[2]

            # send the http PUT request
            if protocol == "https":
                request = requests.put(url=url, json=data, cert=(certificate_file, key_file))
            else:
                request = requests.put(url=url, json=data)
            return format_response(request.status_code, request.reason, None)
        case "DELETE":
            # variables
            variables = request_without_data(request_line, lines, protocol)
            url = variables[0]

            # send the http DELETE request
            if protocol == "https":
                request = requests.delete(url=url, cert=(certificate_file, key_file))
            else:
                request = requests.delete(url=url)
            return format_response(request.status_code, request.reason, None)
        case "HEAD":
            # variables
            variables = request_without_data(request_line, lines, protocol)
            url = variables[0]

            # send the http HEAD request
            if protocol == "https":
                request = requests.head(url=url, cert=(certificate_file, key_file))
            else:
                request = requests.head(url=url)
            return format_response(request.status_code, request.reason, request.headers)


def handle_client(client_socket, certificate_file, key_file):
    """
    Handles the client socket connection.
    :param client_socket: (Socket) the client connection
    :param certificate_file: (str) the certificate filename
    :param key_file: (str) the key filename
    :return: None
    """
    # get the client request
    request = client_socket.recv(1024).decode('utf-8')
    parse_response = parser.parse_request(request)

    if parse_response == "200 OK":
        # handle the request
        response = handle_request(request, certificate_file, key_file)

        # send HTTP response
        client_socket.send(response.encode('utf-8'))
    else:
        # send HTTP response (error)
        client_socket.send(parse_response.encode('utf-8'))

    # close the client connection
    client_socket.close()


def start_server(server_host, server_port, certificate_file, key_file):
    """
    Starts the server with the provided hostname and port. If a certificate
    file and key file are provided, the server starts an encrypted connection.
    :param server_host: (str) the server's hostname
    :param server_port: (int) the server's port
    :param certificate_file: (str) the certificate filename
    :param key_file: (str) the key filename
    :return: None
    """
    # create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)

    # logging information
    print("Listening on {}:{} ...".format(server_host, server_port))
    logging.info("Listening on {}:{} ...".format(server_host, server_port))

    while True:
        # wait for client connections
        client_socket, client_address = server_socket.accept()
        print("Accepted client connection from {}:{}".format(client_address[0], client_address[1]))
        logging.info("Accepted client connection from {}:{}".format(client_address[0], client_address[1]))

        # start threaded client handler for incoming connections
        client_handler = threading.Thread(target=handle_client, args=(client_socket, certificate_file, key_file,))
        client_handler.start()


def main():
    """
    The main program function.
    :return: None
    """
    # check command line arguments
    if len(sys.argv) != 3 and len(sys.argv) != 5:
        sys.exit("Invalid argument")

    # command line arguments
    server_host = sys.argv[1]
    server_port = sys.argv[2]
    certificate_file = None
    key_file = None

    # certificate and key file are provided
    if len(sys.argv) == 5:
        certificate_file = sys.argv[3]
        key_file = sys.argv[4]

    # set up logging
    logging.basicConfig(filename="server.log", level=logging.INFO)

    # start the server
    start_server(server_host, int(server_port), certificate_file, key_file)


if __name__ == '__main__':
    main()
