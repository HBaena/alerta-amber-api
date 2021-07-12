from .generic import Model
from functions import response_to_dict
from typing import Union
from psycopg2 import Binary


class AlertaAmber(Model):
    """

    """        
    def __init__(self, pool):
        super(AlertaAmber, self).__init__(pool)
        self.pool = pool


    def create_person(self, data: dict, **kwargs) -> Union[int, None]:
        query = """
            INSERT INTO {} (
                "curp", "nombre", "ap_paterno", "ap_materno", "sexo_id", "fecha_nacimiento", "estatura", "peso", 
                "complexion_id", "tez_id", "cara_contorno_id", "cabello_id", "cejas_id", "ojos_id", "nariz_id", 
                "boca_id", "labios_id", "menton_id", "orejas_id", "pomulos_id", "barba_id", "bigote_id", 
                "senas_particulares", "padecimientos" 
            ) VALUES (
                %(curp)s, %(nombre)s, %(ap_paterno)s, %(ap_materno)s, %(sexo_id)s, %(fecha_nacimiento)s, %(estatura)s, %(peso)s, 
                %(complexion_id)s, %(tez_id)s, %(cara_contorno_id)s, %(cabello_id)s, %(cejas_id)s, %(ojos_id)s, %(nariz_id)s, 
                %(boca_id)s, %(labios_id)s, %(menton_id)s, %(orejas_id)s, %(pomulos_id)s, %(barba_id)s, %(bigote_id)s, 
                %(senas_particulares)s, %(padecimientos)s 
            ) RETURNING "persona_id"
        """.format(self.person_table)

        return response[0][0] if (response := self.execute(query, data, commit=True, cursor_=kwargs.get('cursor', None))) else None


    def create_missing_person(self, idx: int, extravio_id: int ,**kwargs) -> Union[int, None]:
        query = """
            INSERT INTO {} (
                "persona_id", "extravio_id"
            ) VALUES (
                %s, %s
            ) RETURNING "extraviado_id"
        """.format(self.missing_person_table)

        return response[0][0] if (response := self.execute(query, (idx, extravio_id), commit=True, cursor_=kwargs.get('cursor',None))) else None


    def create_suspect_person(self, data: dict, **kwargs) -> Union[int, None]:
        query = """
            INSERT INTO {} (
                "person_id", "extravio_id", 
                "parentezco", "antecedentes"
            ) VALUES (
                %(person_id)s, %(extravio_id)s, 
                %(parentezco)s, %(antecedentes)s
            ) RETURNING "sospechoso_id"
        """.format(self.suspect_table)
        return response[0][0] if (response := self.execute(query, data, commit=True, cursor_=kwargs.get('cursor',None))) else None


    def read_person(self, idx: int, **kwargs) -> Union[tuple, None]:
        query = """
            SELECT p.*, f.url_foto FROM persona p 
            left join registro_rf rr on rr.persona_id=p.persona_id
            left join foto f on f.registro_rf_id=rr.registro_rf_id 
            WHERE p.persona_id = %s and rr.tipo=0 limit 1
        """
        columns = (
                "ID_PERSONA", "CURP", "NOMBRE", "AP_PATERNO", "AP_MATERNO", "SEXO_ID", "FECHA_NACIMIENTO", "ESTATURA", "PESO", 
                "COMPLEXION_ID", "TEZ_ID", "CARA_CONTORNO_ID", "CABELLO_ID", "CEJAS_ID", "OJOS_ID", "NARIZ_ID", 
                "BOCA_ID", "LABIOS_ID", "MENTON_ID", "OREJAS_ID", "POMULOS_ID", "BARBA_ID", "BIGOTE_ID", 
                "SENAS_PARTICULARES", "PADECIMIENTOS", "URL_FOTO")
        return self.execute(query, (idx, ), formatting=lambda response: response_to_dict(response, columns), cursor_=kwargs.get('cursor', None))


    def read_suspect(self, idx: int, **kwargs) -> Union[dict, None]:
        """
        Function: read_suspect
        Summary: Read suspect person in two steps (Is the same that missing_person but is not minimized to mantain it readeable)
        Examples: read_suspect_person with id = 1
        Attributes: 
            @param (idx:int): suspect_id
            @param (**kwargs): cursor or any else
        Returns: dictionary with the info
        """
        cursor = kwargs.get('cursor', None)
        if not cursor:
            connection = self.get_connection(autocommit=True)
            cursor = connection.cursor()

        query = """
            SELECT * FROM {}
            WHERE "SOSPECHOSO_ID" = %s 
        """.format(self.suspect_table)

        columns = ("SOSPECHOSO_ID", "PERSONA_ID" , "EXTRAVIO_ID", "ANTECEDENTES", "PARENTEZCO")
        suspect =  self.execute(query, (idx, ), formatting=lambda response: response_to_dict(response, columns), **kwargs)
        if suspect:
            suspect = suspect[0]
        else:
            return None
        person = self.read_person(suspect['PERSONA_ID'], **kwargs)
        if person:
            person = person[0]
        else:
            return None
        if not kwargs.get('cursor', None):
            self.release_connection(connection)
        return dict(**suspect, **person)


    def read_missing_person(self, idx: int, **kwargs) -> Union[dict, None]:
        """
        Function: read_missing_person
        Summary: Read missing person in two steps (Is the same that suspect but is not minimized to mantain it readeable)
        Examples: read_missing_person with id = 1
        Attributes: 
            @param (idx:int): extraviad_id
            @param (**kwargs): cursor or any else
        Returns: dictionary with the info
        """
        cursor = kwargs.get('cursor', None)
        if not cursor:
            connection = self.get_connection(autocommit=True)
            cursor = connection.cursor()

        query = """
            SELECT * FROM {}
            WHERE "EXTRAVIADO_ID" = %s 
        """.format(self.missing_person_table)

        columns = ("EXTRAVIADO_ID", "PERSONA_ID", "EXTRAVIO_ID")
        missin_person =  self.execute(query, (idx, ), formatting=lambda response: response_to_dict(response, columns), **kwargs)
        if missin_person:
            missin_person = missin_person[0]
        else:
            return None
        person = self.read_person(missin_person['PERSONA_ID'], **kwargs)
        if person:
            person = person[0]
        else:
            return None
        if not kwargs.get('cursor', None):
            self.release_connection(connection)
        return dict(**missin_person, **person)


    def verify_rf_register(self, idx, person_type, **kwargs):
        query = """
            SELECT registro_rf_id
            FROM registro_rf
            WHERE persona_id=%s and tipo=%s
        """
        return self.execute(query, (idx, person_type), 
            formatting=lambda response: response[0][0], **kwargs)


    def create_rf_register(self, data, **kwargs):
        query = """
            INSERT INTO registro_rf (
                tipo, persona_id, cloud_id
            ) VALUES (
                %(tipo)s, %(persona_id)s, %(cloud_id)s
            ) RETURNING "registro_rf_id"
        """
        return self.execute(query, data, commit=True, formatting=lambda response: response[0][0], **kwargs)


    def get_photos_missing_person(self, idx, person_type, **kwargs):
        query = """
            SELECT rf.registro_rf_id, tipo, rf.persona_id, ENCODE(foto, 'base64') AS foto, url_foto
            FROM registro_rf rf
            LEFT JOIN foto f ON rf.registro_rf_id = f.registro_rf_id 
            WHERE rf.persona_id=%s AND tipo=%s
        """
        columns = ('registro_rf_id', 'tipo', 'persona_id', 'foto', 'url_foto')
        return self.execute(query, (idx, person_type), 
            formatting=lambda response: response_to_dict(response, columns), **kwargs)


    def add_photo_missing_person(self, data, **kwargs):
        query = """
            INSERT INTO foto (
                registro_rf_id, foto, url_foto, fecha_aprox, lucar_aprox
            ) VALUES (
                %(registro_rf_id)s, %(foto)s, %(url_foto)s, %(fecha_aprox)s, %(lucar_aprox)s
            ) RETURNING "foto_id"
        """
        return self.execute(query, data, formatting=lambda response: response[0][0], commit=True, **kwargs)



    def create_report(self, data, **kwargs):
        query = """
            INSERT INTO {} (
                "fecha", "estado", "municipio", "colonia", "coord", "descripcion_vestimenta", 
                "descripcion_hechos", "localizado", "carpeta_investigacion"
            ) VALUES (
                %(fecha)s, %(estado)s, %(municipio)s, %(colonia)s, %(coord)s, %(descripcion_vestimenta)s, 
                %(descripcion_hechos)s, %(localizado)s, %(carpeta_investigacion)s
            ) RETURNING "extravio_id"
        """.format(self.report_table)
        return self.execute(query, data, commit=True, formatting=lambda response: response[0][0],**kwargs)

    def get_coincidences_info(self, person_type, idx, **kwargs):
        query = """
            SELECT 
                nombre, ap_paterno, ap_materno, to_char(age(current_date, e2.fecha), 'YY años "y" MM meses'), 
                to_char(e2.fecha, 'DD/MM/YYYY'), e2.estado, e2.municipio, e2.colonia,
                e2.carpeta_investigacion, f.url_foto
            FROM persona p 
            LEFT JOIN extraviado e ON e.persona_id=p.persona_id
            LEFT JOIN extravio e2 ON e2.extravio_id=e.extravio_id
            LEFT JOIN registro_rf rr ON rr.persona_id=p.persona_id
            LEFT JOIN foto f ON f.registro_rf_id=rr.registro_rf_id 
            WHERE p.persona_id=%s AND rr.tipo=%s LIMIT 1
        """
        columns = ("NOMBRE", "AP_PATERNO", "AP_MATERNO", "EDAD", 
                "FECHA EXTRAVIO", "ESTADO EXTRAVIO", "MUNICIPIO EXTRAVIO", "COLONIA EXTRAVIO",
                "CARPETA_INVESTIGACION", "URL_FOTO")
        return self.execute(query, (idx, person_type), formatting=lambda response: response_to_dict(response, columns), **kwargs)