class CustomException(Exception):
    def __init__(self, request, message):
        self.request = request
        self.message = "Request: {}\nError: {}".format(request, message)
        super().__init__(self.message)
