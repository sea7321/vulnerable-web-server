"""
Filename: parser.py
Author: Savannah Alfaro, sea2985
"""
import sys
import json
import re

from CustomException import CustomException


def check_http_version(request_line):
    """
    Checks the http version of the request line
    :param request_line: (String) the request line of the request
    :return: None
    """
    http_versions = ["HTTP/0.9", "HTTP/1.0", "HTTP/1.1", "HTTP/2.0"]

    http_version = request_line[2]
    if http_version not in http_versions:
        raise CustomException(request_line, "400 Bad Request")


def check_request_headers(request_line, lines, request_headers):
    """
    Checks the request headers are correct based on the method provided.
    :param request_line: (String) the request line of the request
    :param lines: (String) the lines of the request
    :param request_headers: (String[]) the list of accepted headers
    :return: None
    """
    for line in lines:
        header = line.strip().split(":")[0]
        if header == '':
            break
        if header not in request_headers:
            raise CustomException(request_line, "400 Bad Request")


def parse_request(data):
    """
    Parses through the lines of the request by checking the format of
    the resource path, http version, request headers, and body.
    :param data: (String) the request data
    :return: None
    """
    lines = data.split("\n")
    request_line = lines[0].strip().split()
    content_flag = False

    try:
        # parse through lines based on method
        method = lines[0].strip().split(" ")[0]
        match method:
            case "GET":
                # variables
                request_headers = ["Host", "Accept"]
            case "POST":
                # variables
                request_headers = ["Host", "Accept", "Content-Type", "Content-Length"]
                content_flag = True
            case "PUT":
                # variables
                request_headers = ["Host", "Accept", "Content-Type", "Content-Length"]
                content_flag = True
            case "DELETE":
                # variables
                request_headers = ["Host", "Accept", "Authorization"]
            case "HEAD":
                # variables
                request_headers = ["Host", "Accept", "Content-Type", "Content-Length"]
            case _:
                raise CustomException(request_line, "400 Bad Request")

        # check format of the request line
        request_line = lines[0].strip()
        if len(request_line.split()) != 3:
            raise CustomException(request_line, "400 Bad Request")
        lines.remove(lines[0])

        # check the format of the resource path
        resource_path_pattern = '\/[a-zA-Z0-9!@?#=\/:$&()\\-`.+,/\"]*'
        resource_path = re.compile('{}'.format(resource_path_pattern))
        if not (resource_path.search(request_line.split()[1])):
            raise CustomException(request_line, "400 Bad Request")

        # check the http version
        check_http_version(request_line.split())

        # check format of the request headers
        # check_request_headers(request_line, lines, request_headers)

        # check format of the body content
        if content_flag:
            flag = False
            new_lines = ""
            try:
                for line in lines:
                    if line == '':
                        continue
                    if line[0] == '{':
                        flag = True
                    if flag:
                        new_lines += line
                json.loads(new_lines)
            except Exception as e:
                raise CustomException(request_line, "400 Bad Request")
    except CustomException as exception:
        return exception.message

    # return success message
    return "200 OK"


def read_input_file(filename):
    """
    Reads the input file name and parses through lines
    of the file based on the method.
    :param filename: (String) the input file name
    :return: None
    """
    # extract lines from input file
    with open(filename, "r") as file:
        return file.read()


def main():
    """
    The main program function.
    :return: None
    """
    # command line arguments
    input_filename = sys.argv[1]
    if len(sys.argv) != 2:
        sys.exit("Invalid argument")

    # read input file
    data = read_input_file(input_filename)

    # parse request
    parse_request(data)


if __name__ == '__main__':
    main()
