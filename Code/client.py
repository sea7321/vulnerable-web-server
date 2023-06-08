"""
Filename: client.py
Author: Savannah Alfaro, sea2985
"""
import socket
import sys


def start_client(target_host, target_port, input_filename):
    """
    Starts the client connection to the server with the provided hostname and port.
    :param target_host: (str) the target's hostname
    :param target_port: (int) the target's port
    :param input_filename: (str) the input filename
    :return: None
    """
    # create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect the client
    client.connect((target_host, target_port))

    # read data
    with open(input_filename, "r") as file:
        data = file.read()

    # send request
    client.send(data.encode('utf-8'))

    # response
    response = client.recv(1024)
    print(response.decode('utf-8'))
    client.close()


def main():
    """
    The main program function.
    :return: None
    """
    # check command line arguments
    if len(sys.argv) != 4:
        sys.exit("Invalid argument")

    # command line arguments
    target_host = sys.argv[1]
    target_port = sys.argv[2]
    input_filename = sys.argv[3]

    # start the client
    start_client(target_host, int(target_port), input_filename)


if __name__ == '__main__':
    main()

