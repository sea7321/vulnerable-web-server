#!/bin/bash

export GATEWAY_INTERFACE="CGI/1.1"
export SCRIPT_FILENAME="Scripts/getdemo.php"
export REQUEST_METHOD="GET"
export SERVER_PROTOCOL="HTTP/1.1"
export QUERY_STRING="example1=Hello&example2=World"

exec echo | php-cgi