from flask import request  # Flask, receiving data from requests, json handling
from flask import send_file  # Create url from statics files
from flask import jsonify  # Flask, receiving data from requests, json handling
from flask import after_this_request  
from flask import render_template
from flask import url_for

from flask_restful import Resource  # modules for fast creation of apis

from config import app
from config import api
from config import jwt
from config import connect_to_db_from_json
from config import init_notification_manager
from config import pdf_options

from config import logo_amber_b64
from config import logo_jalisco_b64


from model.user import User as UserModel 
from model.alerta_amber import AlertaAmber

from model.enums import StatusMsg
from model.enums import ErrorMsg 
from model.enums import DBErrorMsg
from model.enums import RouteErrorMsg
from model.enums import SuccessMsg
from model.enums import PersonType
from model.enums import FaceRecognitionMsg

from typing import Any, NoReturn

from os import getcwd
from os import path 
from os import remove 

from functools import wraps
from functions import encript_password
from functions import verify_password
from functions import extract_person_info
from functions import extract_suspect_info
from functions import validate_datetime_from_form

from face_recognition import FaceRecognitionService

from collections import defaultdict
from imgkit import from_string as poster_from_string


from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import get_jwt
from flask_jwt_extended import set_access_cookies
from flask_jwt_extended import unset_jwt_cookies
from flask_jwt_extended import verify_jwt_in_request

from datetime import datetime
from datetime import timedelta
from datetime import timezone

from time import time

from icecream import ic

API_VERSION = '1.0.000'
pool = None
user_model = None
aa_model = None
notification_manager = None

@app.after_request
def after_request(response) -> Any:
    """
    Prevent CORS problems after each request
    :param response: Response of any request
    :return: The same request
    """
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE, PATCH')
    return response

@app.before_first_request
def initialize() -> NoReturn:
    """
    Function: initialize
    Summary: Functions that start services that the appi needs
    Examples: validate licenses, create db connections or start face recognition service 
    Returns: Nothing
    """
    # from pathlib import Path
    from pathlib import Path
    global pool, user_model, aa_model, notification_manager

    pool = connect_to_db_from_json("connection.json")
    pool = connect_to_db_from_json("connection.json")
    user_model = UserModel(pool)
    aa_model = AlertaAmber(pool)
    notification_manager = init_notification_manager()
    Path(path.join(getcwd(), "temp")).mkdir(parents=True, exist_ok=True)


@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    """
    Function: my_expired_token_callback
    Summary: Functions that handle usless token
    Attributes: 
        @param (jwt_header):InsertHere
        @param (jwt_payload):InsertHere
    Returns: estatus=token_expired
    """
    return jsonify(estatus="token_expired", error=jwt_payload, message="Token expired, try to get another one using refresh token")


@jwt.invalid_token_loader
def my_invalid_token_callback(jwt_payload):
    """
    Function: my_expired_token_callback
    Summary: Functions that handle usless token
    Attributes: 
        @param (jwt_header):InsertHere
        @param (jwt_payload):InsertHere
    Returns: estatus=token_expired
    """
    return jsonify(estatus="invalid_token", error=jwt_payload, message="Token invalid, try to get another one using refresh token")


@jwt.unauthorized_loader
def my_unauthorized_callback(jwt_payload):
    """
    Function: my_expired_token_callback
    Summary: Functions that handle usless token
    Attributes: 
        @param (jwt_header):InsertHere
        @param (jwt_payload):InsertHere
    Returns: estatus=token_expired
    """
    return jsonify(estatus="unauthorized", error=jwt_payload, message="Missing Authorization header")


def jwt_required_in_db():
    """
    Function: jwt_required_in_db
    Summary: Check if the token is valid or not and then read the database to verify that is active in database
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            token = request.headers['Authorization'][7:]
            if user_model.validate_token_activo(token):
                return fn(*args, **kwargs)
            else:
                return jsonify(error="Token is not in db")
        return decorator
    return wrapper


class Index(Resource):
    @jwt_required_in_db()
    def get(self):
        """
        Function: get
        Summary: Return information about the API
        Endpoint: /
        Returns: json
        """
        # verification_code = user_model.generar_codigo_verificacion(int(46))

        return dict(message="Alerta amber API", Version=API_VERSION)


class User(Resource):
    """
    
    """
    # @jwt_required_in_db()
    def get(slef):
        """
        Function: get
        Summary: Get data from user by id
        Endpoitn: /robot/user/
        Php endpoint: datos_usuario_get
        Returns: Data in json format   
        """
        email = request.args.get('email')
        if not email:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('email'))
        
        user = user_model.read_user(email)
        if not user:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.USER_NOT_EXISTS)
        user = user.pop()
        del user['CONTRASENA']
        return jsonify(status=StatusMsg.OK, message=SuccessMsg.READED, data=user)

    def post(self):
        """
        Function: post
        Summary: Create a new user
        Php endpoint: usuario_registro_cn_post
        Returns: Message, access_tokens and id
        """
        if not request.files.get('foto'):
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('foto'))
        photo = request.files.get('foto').read()
        if photo == b'':
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('foto'))

        form = request.form
        data = {
            'email': form.get('email'), 
            'telefono': form.get('telefono'), 
            'nombre': form.get('nombre'), 
            'no_empleado': form.get('no_empleado', 1), 
            'contrasena': form.get('contrasena'), 
            'zona': form.get('contrasena', 0), 
            'notificaciones_device_id': form.get('notificaciones_device_id'), 
        }
        # TODO: verify nulls
        connection = aa_model.get_connection(autocommit=False)
        if not connection:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CONNECTION_ERROR)
        cursor = connection.cursor()

        user = user_model.read_user(data['email'], cursor_=cursor)
        if user:
            return jsonify(status=StatusMsg.FAIL, message=DBErrorMsg.USER_EXISTS, error=ErrorMsg.DB_ERROR)

        fr_service = FaceRecognitionService(path.join(getcwd(), 'luxand.json'))
        response_rf =  fr_service.add_person(f"usuario/{data['email']}", photo)

        if not response_rf:
            connection.rollback()
            aa_model.release_connection(connection)
            return jsonify(status=StatusMsg.FAIL, message=FaceRecognitionMsg.UPLOAD_ERROR, error=ErrorMsg.FR_SERVICE_ERROR)

        data['contrasena'] = encript_password(data['contrasena'])  # password 
        data['rf_cloud_id'] = response_rf.get('id')

        user_id = user_model.create_user(data, cursor_=cursor)


        if not user_id:
            connection.rollback()
            aa_model.release_connection(connection)
            return jsonify(status=StatusMsg.FAIL, message=DBErrorMsg.CREATING_ERROR, error=ErrorMsg.DB_ERROR)

        connection.commit()
        aa_model.release_connection(connection)
        return jsonify(
                message=SuccessMsg.CREATED,
                status= StatusMsg.OK, 
                data= { 'user_id': user_id }
            )


    def patch(self):
        """
        Function: patch
        Summary: Update partially an user (rango edad, educacion, genero)
        Php endpoint: update_datos_usuario_post
        Returns: estatus
        """
        data = request.form
        data_db = {
            'usuario_id':  data.get('usuario_id'),
            'notificaciones_device_id':  data.get('notificaciones_device_id')
        }
        if not data_db['usuario_id']:
            return jsonify(status=StatusMsg.FAIL, message=ErrorMsg.NEEDED_VALUES.format("usuario_id, notificaciones_device_id"), 
                error=ErrorMsg.MISSING_VALUES)

        if user_model.update_notification_id(data_db):
            return dict(status=StatusMsg.OK, message=SuccessMsg.UPDATED)
        else:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.ID_ERROR)


class Users(Resource):
    def get(self):
        zone = request.args.get('zona')
        rol = request.args.get('rol')
        response = user_model.read_users_by_zone(zone, rol)
        if response:
            return jsonify(status=StatusMsg.OK, message=SuccessMsg.READED, data=response)
        else:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.NO_EXISTS_INFO)


class Token(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """
        Function: post
        Summary: Refresh access token from refresh token
        Endpoint: /user/refresh-token 
        """
        old_token = request.form.get('token')
        if not old_token:
            return jsonify(status=StatusMsg.FAIL, message=ErrorMsg.NEEDED_VALUES.format("old token not received"), 
                error=ErrorMsg.MISSING_VALUES)
        identity = get_jwt_identity()
        access_token = create_access_token(identity=identity)
        refresh_token = create_refresh_token(identity=identity)
        return jsonify(status=StatusMsg.OK, access_token=access_token, refresh_token=refresh_token)


class Login(Resource):
    def post(self):
        """
        Function: post
        Summary: Login user
        Endpoint: /robot/login/
        Php endpoint: login_cn_post
        """
        form = request.form
        data = {
            'email': form.get('email'),
            'contrasena': form.get('contrasena')
        }
        # TODO: validation
        user = user_model.read_user(data['email'])
        if not user:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.USER_NOT_EXISTS)
        user = user[0]
        if verify_password(user['CONTRASENA'], data['contrasena']):
            access_token = create_access_token(identity=data['email'])
            refresh_token = create_refresh_token(identity=data['email'])
            del user['CONTRASENA']
            ic(user_model.add_jwt(access_token))

            return jsonify(status=StatusMsg.OK, message='Login successfully', user_data=user,
                    access_token=access_token, refresh_token=refresh_token)
        else:
            return jsonify(status=StatusMsg.FAIL, message=ErrorMsg.WRONG_PASSWORD, error=ErrorMsg.WRONG_PASSWORD)


class Logout(Resource):
    @jwt_required_in_db()
    def delete(self):
        token = request.headers['Authorization'][7:]
        if not user_model.delete_jwt(token):
            return jsonify(dict(status=StatusMsg.FAIL))
        else:
            return jsonify(status=StatusMsg.OK)


class Person(Resource):

    def get(self, person_type: str):
        """
        Function: get
        Summary: Get missing people info by id
        Attributes: 
            @args (extraviado_id): id
        Returns: person data
        """
    
        idx = request.args.get('idx')
        if not idx:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('idx'))

        if person_type == 'extraviado':
            data = aa_model.read_person(idx)
        elif person_type == 'sospechoso':
            data = aa_model.read_suspect(idx)
        else:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.ROUTE_ARG_ERROR, message=RouteError.ARG_ERROR)
        if not data:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.READING_ERROR)
        return jsonify(status=StatusMsg.OK, message=SuccessMsg.READED, data=data[0])


    def post(self, person_type: str):
        """
        Function: post
        Summary: 
        Examples: InsertHere
        Attributes: 
            @form (person info):
        Returns: InsertHere
        """
        if person_type not in ('extraviado', 'sospechoso'):
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.ROUTE_ARG_ERROR, message=RouteError.ARG_ERROR)

        form = defaultdict(lambda: None, request.form)
        ic(form.get('foto'), form.get('nombre'), form.get('a_paterno'))
        if not all((request.files.get('foto'), form.get('nombre'), form.get('ap_paterno'))):
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('foto, nombre y appelido'))
        ic(form)
        # DB CONNECTION
        connection = aa_model.get_connection(autocommit=False)
        if not connection:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CONNECTION_ERROR)
        cursor = connection.cursor()
        
        # CREATE PERSON
        person_id = aa_model.create_person(form, cursor_=cursor)
        if not person_id:
            connection.rollback()
            aa_model.release_connection(connection)
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CREATING_ERROR)
        ic(person_id)
        # CREATE MISSING_PERSON or SUSPECT
        response = dict(status=StatusMsg.OK, message=SuccessMsg.CREATED)        
        if person_type == 'extraviado':
            extraviado_id = aa_model.create_missing_person(person_id, form.get("extravio_id"),cursor_=cursor)
            if not extraviado_id:
                return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CREATING_ERROR)
            response['extraviado_id'] = extraviado_id
        else:
            suspect_data = extract_supect_info(form, person_id)
            sospechoso_id = aa_model.create_suspect_person(suspect_data)
            if not sospechoso_id:
                return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CREATING_ERROR)
            response['sospechoso_id'] = sospechoso_id

        ic(response)
        # RF SERVICE
        fr_service = FaceRecognitionService(path.join(getcwd(), 'luxand.json'))

        response_rf = fr_service.add_person(   # Creating a void rf_register
            f"{PersonType.MISSING_PERSON if person_type == 'extraviado' else PersonType.SUSPECT}/{person_id}", b'')  
        if not response_rf:
            connection.rollback()
            aa_model.release_connection(connection)
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.FR_SERVICE_ERROR, message=DBErrorMsg.CREATING_ERROR)
        data_rf = {
            'tipo': PersonType.MISSING_PERSON if person_type == 'extraviado' else PersonType.SUSPECT,
            'persona_id': person_id,
            'cloud_id': response_rf.get('id'),
        }
        rf_id = aa_model.create_rf_register(data_rf, cursor_=cursor)  # creating rf register to relate cloud service and db
        if not rf_id:
            connection.rollback()
            aa_model.release_connection(connection)
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CREATING_ERROR)

        data_rf['registro_rf_id'] = rf_id
        data_rf['foto'] = request.files.get('foto').read()
        ic(data_rf['cloud_id'])
        response_rf = fr_service.add_face_to_person(data_rf['cloud_id'], data_rf['foto'])
        if not response_rf:
            connection.rollback()
            aa_model.release_connection(connection)
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.FR_SERVICE_ERROR, message=DBErrorMsg.CREATING_ERROR)
        ic(response_rf)
        data_rf['url_foto'] = response_rf['url']
        data_rf['fecha_aprox'] = form.get('fecha_aprox')
        data_rf['lucar_aprox'] = form.get('lucar_aprox')
        foto_id = aa_model.add_photo_missing_person(data_rf, cursor_=cursor)

        # MAKE DB CHANGES and RELEASE DB CONNECTION
        connection.commit()
        aa_model.release_connection(connection)
        response['url_foto'] = data_rf['url_foto']
        response['cloud_id'] = data_rf['cloud_id']
        return jsonify(response)



class Report(Resource):
    """
        Alerta amber report
        /report/
    """
    def get(self):
        """
        Function: get
        Summary: Get info about AA report
        Returns: AA report Info 
        """
        ...

    def post(self):
        """
        Function: post
        Summary: Create new AA report (Missing person info, Event info, Contact info and suspicious )
        Returns: report ID
        """
        form = defaultdict(lambda: None, request.form)
        coord = form.get('coord')
        if coord:
            x, y = coord.split(',')
            form['COORD_X'] =  float(y)
            form['COORD_Y'] =  float(x)

        validate_datetime_from_form(form, 'fecha')

        extravio_id = aa_model.create_report(form)
        if not extravio_id:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CREATING_ERROR)
        else:
            return jsonify(status=StatusMsg.OK, message=SuccessMsg.CREATED, extravio_id=extravio_id)

    def patch(self):
        """
        Function: patch
        Summary: Update info about AA report
        Returns: report ID
        """
        ...


class CloseReport(Resource):
    def post(self, idx):
        connection = aa_model.get_connection(autocommit=False)
        if not connection:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CONNECTION_ERROR)
        cursor = connection.cursor()
        data = defaultdict(lambda: None, request.form)
        coord = request.form.get('coord')
        if coord:
            x, y = coord.split(',')
            data['COORD_X'] =  float(y)
            data['COORD_Y'] =  float(x)
        validate_datetime_from_form(data, 'fecha')
        idx_close_report = aa_model.close_report(idx, data, cursor_=cursor)
        if not idx_close_report:
            connection.rollback()
            aa_model.release_connection(connection)
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CREATING_ERROR)
        connection.commit()
        aa_model.release_connection(connection)
        return jsonify(status=StatusMsg.OK, message=SuccessMsg.CREATED, folio=idx_close_report)



class FaceRecognition(Resource):

    def post(self):
        """
        Function: post
        Summary: Search face into db`
        dataform:
            foto: file
            deep: bool 
        """
        deep = request.form.get('deep', True)
        coord = request.form.get('coord')
        usuario_id = request.form.get('usuario_id')
        data = defaultdict(lambda: None)
        if coord:
            x, y = coord.split(',')
            data['COORD_X'] =  float(y)
            data['COORD_Y'] =  float(x)
        data['usuario_id'] = usuario_id
        if not request.files.get('foto'):
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('foto'))
        photo = request.files.get('foto').read()
        if photo == b'':
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('foto'))
        
        fr_service = FaceRecognitionService(path.join(getcwd(), 'luxand.json'))
        coincidences = fr_service.recognize(photo, deep=bool(deep))        
        if not coincidences or (isinstance(coincidences, dict) and coincidences['status'] == 'failure'):
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.FR_SERVICE_ERROR, message=FaceRecognitionMsg.NO_COINCIDENCE)
        coincidences = tuple(filter(lambda item: item['name'][0].isdigit(), coincidences))
        if not coincidences:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.FR_SERVICE_ERROR, message=FaceRecognitionMsg.NO_COINCIDENCE)

        connection = aa_model.get_connection(autocommit=False)
        if not connection:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CONNECTION_ERROR)
        cursor = connection.cursor()
        response = list()
        for coincidence in coincidences:
            data['cloud_rf_id'] = coincidence['id']
            data['probabilidad'] = coincidence['probability']
            ic(coincidence['name'])
            ic(coincidence['name'].split('/'))
            temp = aa_model.get_coincidences_info(*coincidence['name'].split('/'), cursor_=cursor)
            if not temp:
                aa_model.release_connection(connection)
                return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.CONNECTION_ERROR, log='reading')
            ic() 
            data['foto_consulta'] = photo
            data['extravio_id'] = temp['EXTRAVIO_ID']
            data['fecha'] = datetime.today()
            alerta_id = aa_model.create_alert(data, cursor_=cursor)
            temp['ALERTA_ID'] = alerta_id
            response.append(temp)
        connection.commit()
        aa_model.release_connection(connection)

        return jsonify(status=StatusMsg.OK, coincidences=response, message=FaceRecognitionMsg.COINCIDENCE)


class FaceVerification(Resource):
    def post(self):
        cloud_rf_id = request.form.get("cloud_rf_id")
        if not request.files.get('foto') or not cloud_rf_id:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('foto, cloud_rf_id'))
        photo = request.files.get('foto').read()
        if photo == b'':
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('foto'))

        fr_service = FaceRecognitionService(path.join(getcwd(), 'luxand.json'))

        verified = fr_service.verify(cloud_rf_id, photo)
        ic(verified)
        if not verified or verified.get('status') == 'failure':
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.FR_SERVICE_ERROR, message=FaceRecognitionMsg.NOT_VERIFIED)
        # IF VERIFIED
        return jsonify(status=StatusMsg.OK, message=FaceRecognitionMsg.VERIFIED)



class Alert(Resource):
    def get(self):
        idx = request.args.get('idx')
        response = aa_model.read_alert(idx)
        if not response:
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.NO_EXISTS_INFO)
        # fr_service = FaceRecognitionService(path.join(getcwd(), 'luxand.json'))
        # fr_data = fr_service.list_person_faces(response['cloud_rf_id'])
        # response['fotos_db'] = fr_data
        return jsonify(status=StatusMsg.OK, message=SuccessMsg.READED, data=response)



class Alerts(Resource):
    def get(self):
        data = {
            "zone": request.args.get("zona"),
            "all": request.args.get("all", True)
        }
        response = aa_model.read_alerts_by_zone(data)
        if not response: 
            return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.DB_ERROR, message=DBErrorMsg.NO_EXISTS_INFO)
        # fr_service = FaceRecognitionService(path.join(getcwd(), 'luxand.json'))
        # for coincidence in response:
        #     ic(coincidence['cloud_rf_id'])
        #     coincidence['fotos_db'] = fr_service.list_person_faces(coincidence['cloud_rf_id'])

        return jsonify(status=StatusMsg.OK, message=SuccessMsg.READED, data=response)


class Notification(Resource):
    def get(self):
        ...
    #     TODO
    #     args = request.args
    #     type_ = args.get('user_type')
    #     idx = args.get('id')
    #     if type_ == 'pl':
    #         response = d911_cripto_model.notification_id_sm(idx)
    #     elif type_ == 'sm': 
    #         response = d911_cripto_model.notification_id_pl(idx)
    #     elif type_ == 'cn': 
    #         response = user_model.notification_id_cn(idx)
    #     else:
    #         return jsonify(estatus="fail", error="type needed")
    #     return jsonify(estatus="good", data=response)

    def post(self):
        """
        Function: post
        Summary: Send notifications by tags or ids
        """
        data = request.get_json()
        mode = data.get("mode", None)
        ic(mode)
        ic(data)
        if mode == 'tags':
            ic()
            code, _json = notification_manager.send_notification_tag_base(data)
        elif mode == "idx":
            code, _json = notification_manager.send_notification_idx_base(data)
        else:
            return dict(status=StatusMsg.FAIL, error=ErrorMsg.MISSING_VALUES, message=ErrorMsg.NEEDED_VALUES.format('mode [tags, idx]'))
        return jsonify(status=StatusMsg.OK, message=SuccessMsg.SENT, status_code=code, response=_json)


class FotoExtraviado(Resource):
    def get(self):
        ...


api.add_resource(Index, '/alerta-amber/')
api.add_resource(User, '/alerta-amber/user/')
api.add_resource(Users, '/alerta-amber/users/list/')
api.add_resource(Token, '/alerta-amber/user/refresh-token/')
api.add_resource(Login, '/alerta-amber/user/login/')
api.add_resource(Logout, '/alerta-amber/user/logout/')
api.add_resource(Report, '/alerta-amber/reporte/')
api.add_resource(CloseReport, '/alerta-amber/reporte/<int:idx>/cerrar/')
api.add_resource(Person, '/alerta-amber/persona/<string:person_type>')
api.add_resource(FaceRecognition, '/alerta-amber/face-recognition/')
api.add_resource(FaceVerification, '/alerta-amber/face-verification/')
api.add_resource(Notification, '/alerta-amber/notifications/')
api.add_resource(Alerts, '/alerta-amber/list/')
api.add_resource(Alert, '/alerta-amber/alerta/')


@app.route("/alerta-amber/reporte/<int:extravio_id>/poster/")
def poster_html(extravio_id: int):
    # print(extravio_id)
    persona = aa_model.read_info_for_poster(extravio_id)
    if not persona:
        raise Exception(DBErrorMsg.NO_EXISTS_INFO)
    html = render_template("report.html", persona=persona[0], 
        logo_amber=logo_amber_b64, logo_jalisco=logo_jalisco_b64)
    return html


@app.route("/alerta-amber/reporte/<int:extravio_id>/poster/download/")
def poster_jpeg(extravio_id: int):
    # print(extravio_id)
    persona = aa_model.read_info_for_poster(extravio_id)
    if not persona:
        raise RouteError
    ic(persona[0]['nombre'])
    html = render_template("report.html", persona=persona[0], 
        logo_amber=logo_amber_b64, logo_jalisco=logo_jalisco_b64)
    jpeg_path = path.join(getcwd(), 'temp', f'{extravio_id}.jpeg')
    poster_from_string(html, jpeg_path)
    return send_file(jpeg_path, as_attachment=True)


@app.errorhandler(Exception)
def handle_exception(e):
    ic(e)
    return jsonify(status=StatusMsg.FAIL, error=ErrorMsg.UNKNOWN_ERROR, message=str(e))
