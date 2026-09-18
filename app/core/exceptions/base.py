

class AppException(Exception):
    def __init__(self, detail, status_code, error_code, *args):
        super().__init__(*args)
        self.detail = detail
        self.status_code = status_code
        self.error_code = error_code


    def to_dict(self):
        error_dict = {
            "status": "error",
            "error_code": self.error_code,
            "status_code": self.status_code
        }
        if self.detail:
            error_dict['detail'] = self.detail

        return error_dict