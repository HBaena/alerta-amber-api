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


    def read_user(self, email: str) -> Union[None, tuple]:
        query = """
            SELECT * FROM {}
            WHERE "email"=%s
        """.format(self.user_table)
        columns = ('USUARIO_ID', 'EMAIL', 'TELEFONO', 'NOMBRE', 'NO EMPLEADO', 'CONTRASENA')

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
            RETURNING "user_id"
        """.format(self.user_table)
        return response[0][0] if (response := self.execute(query, data, commit=True)) else None 
            
            
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