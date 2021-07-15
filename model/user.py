from .generic import Model
from psycopg2 import sql
from typing import Any, Union
from icecream import ic
from functions import response_to_dict
from functions import encript_password
from functions import response_to_dict

class User(Model):
    """

    """        
    def __init__(self, pool):
        super(User, self).__init__(pool)
        self.pool = pool
        self.user_table = 'usuario'

    def read_user(self, email: str) -> Union[None, tuple]:
        query = """
            SELECT * FROM {}
            WHERE "email"=%s
        """.format(self.user_table)
        columns = ('USUARIO_ID', 'EMAIL', 'TELEFONO', 'NOMBRE', 'NO EMPLEADO', 'CONTRASENA', 'ZONA', 'NOTIFICACIONES_DEVICE_ID', 'ROL')

        return self.execute(
                query, (email,), commit=True, 
                formatting=lambda response: response_to_dict(response, columns))

    def create_user(self, data: dict) -> int:
        query = """
            INSERT INTO {} 
            (
                "email", "telefono", "nombre", 
                "no_empleado", "contrasena"
            )
            VALUES
            (
                %(email)s, %(telefono)s, %(nombre)s, 
                %(no_empleado)s, %(contrasena)s
            )
            RETURNING "usuario_id"
        """.format(self.user_table)
        return  self.execute(query, data, commit=True, formatting=lambda response: response[0][0])
            
            
    def jwt_update(self, jwt_token_old: str, jwt_token_new: str) -> int:
        query = """
            UPDATE public."JWT"
            SET "TOKEN" = %s
            WHERE "TOKEN" = %s
            RETURNING "TOKEN_ID"
        """
        if response := self.execute(sql.SQL(query), (jwt_token_old, jwt_token_new), commit=True):
            return response[0][0]
        else:
            return False 


    def update_notification_id(self, data, **kwargs):
        query = """
            UPDATE {} SET notificaciones_device_id=%(notificaciones_device_id)s
            WHERE usuario_id=%(usuario_id)s
        """.format(self.user_table)
        return self.execute(query, data, commit=True, **kwargs)


    def read_users_by_zone(self, zone: int, rol: int) -> Union[None, tuple]:
        query = """
            SELECT 
                "usuario_id", "email", "telefono", "nombre", "no_empleado", 
                "zona", "notificaciones_device_id", "rol" 
            FROM {}
            WHERE zona=%s {}
        """.format(self.user_table, f"AND rol={rol}" if rol else "")
        columns = ('USUARIO_ID', 'EMAIL', 'TELEFONO', 'NOMBRE', 'NO EMPLEADO', 'ZONA', 'NOTIFICACIONES_DEVICE_ID', 'ROL')

        return self.execute(
                query, (zone, ), commit=True, 
                formatting=lambda response: response_to_dict(response, columns))


    def add_jwt(self, token, **kwargs):
        query = """
            INSERT INTO jwt ("TOKEN") VALUES (%s)        
        """
        return self.execute(query, (token, ), commit=True, **kwargs)

    def delete_jwt(self, token, **kwargs):
        query = """
            DELETE FROM jwt 
            WHERE "TOKEN"=%s
        """
        return self.execute(query, (token, ), commit=True, **kwargs)

    def validate_token_activo(self, token, **kwargs):
        query = """
            SELECT * FROM jwt
            WHERE "TOKEN"=%s
        """
        return self.execute(query, (token, ), commit=True, **kwargs)