from flask import jsonify


class RequestValidator:
    @staticmethod
    def validate_payload(data, required_fields):
        """Checks if the JSON payload exists and if the required fields are in the JSON.

        :param data: The request JSON.
        :param required_fields: List of required fields.
        :return: A tuple (is_valid, response, status_code), where is_valid is a boolean
                 indicating the validity of the payload, response is a JSON response in
                 case of error, and status_code is the HTTP status code.
        """
        if not data:
            return False, {"success": False, "message": "JSON payload is required."}, 400

        for field in required_fields:
            if field not in data:
                return False, {"success": False, "message": f"{field} is required."}, 400

        return True, None, None

    @staticmethod
    def validate_fields_not_empty(data, fields):
        """Validates if the specified fields in the data are not empty.

        :param data: The request JSON.
        :param fields: List of fields to check for emptiness.
        :return: A tuple (is_valid, response, status_code), where is_valid is a boolean
                 indicating if the fields are not empty, response is a JSON response in
                 case of error, and status_code is the HTTP status code.
        """
        for field in fields:
            if not data.get(field):
                return False, {"success": False, "message": f"{field} should not be empty."}, 400
        return True, None, None

    @staticmethod
    def validate_and_extract_payload(request, required_fields):
        _json = request.json
        print(_json)
        is_valid, response, status_code = request_validator.validate_payload(_json, required_fields=required_fields)
        if not is_valid:
            return None, response, status_code

        is_valid, response, status_code = request_validator.validate_fields_not_empty(_json, required_fields)
        if not is_valid:
            return None, response, status_code

        return _json, None, None


request_validator = RequestValidator()
