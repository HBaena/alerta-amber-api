class StatusMsg():
    OK = 'ok'
    FAIL = 'fail'

class ErrorMsg():
    DB_ERROR = 'db_error'
    VALUES_REQUIRED = 'all_values_are_required'
    MISSING_VALUES = 'missing_values'
    WRONG_PASSWORD = 'wrong_password'
    ROUTE_ERROR = 'endpoint_error'
    NEEDED_VALUES = '[{}] need value(s)'
    FR_SERVICE_ERROR = 'fr_service_fails'

class RouteErrorMsg():
    ARG_ERROR = 'endpoint_argument_unexpected'


class DBErrorMsg():
    USER_EXISTS = 'user_already_exists'
    USER_NOT_EXISTS = 'user_not_exists'
    CREATING_ERROR = 'error_writing_db'
    READING_ERROR = 'error_reading_db'
    CONNECTION_ERROR = 'error_with_db_connection'
    ID_ERROR = 'id_not_exists_in_db'

class SuccessMsg():
    SENT = 'sent_message'
    CREATED = 'created_successfully'
    READED = 'read_successfully'
    UPDATED = 'updated_successfully'
    DELETED = 'deleted_successfully'
    FOUND = 'coincidences_found'

class PersonType():
    MISSING_PERSON = 0
    SUSPECT = 1

class FaceRecognitionMsg():
    COINCIDENCE = "possible_coincidence"
    NO_COINCIDENCE = "no_coincidence"