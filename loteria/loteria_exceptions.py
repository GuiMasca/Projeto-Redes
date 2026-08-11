class LoteriaException(Exception) :
    def __init__(self, message, error_code=1001) :
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} (Error code: {self.error_code})"

class ParameterSetException(LoteriaException) :
    def __init__(self, message, error_code=1002) :
        super().__init__(message, error_code)

class AddTicketException(LoteriaException) :
    def __init__(self, message, error_code=1003) :
        super().__init__(message, error_code)