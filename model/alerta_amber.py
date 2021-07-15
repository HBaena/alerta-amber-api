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
        self.missing_person_table = 'extraviado'
        self.suspect_table = 'public."SOSPECHOSO"'
        self.person_table = 'persona'
        self.user_table = 'usuario'
        self.photos_table = 'foto'
        self.report_table = 'extravio'

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
                %(fecha)s, %(estado)s, %(municipio)s, %(colonia)s, 
                public.ST_GeomFromText('POINT(%(COORD_X)s %(COORD_Y)s)', 4326), 
                %(descripcion_vestimenta)s, %(descripcion_hechos)s, %(localizado)s, %(carpeta_investigacion)s
            ) RETURNING "extravio_id"
        """.format(self.report_table)
        return self.execute(query, data, commit=True, formatting=lambda response: response[0][0],**kwargs)

    def get_coincidences_info(self, person_type, idx, **kwargs):
        query = """
            SELECT 
                nombre, ap_paterno, ap_materno, to_char(age(current_date, e2.fecha), 'YY años "y" MM meses'), 
                to_char(e2.fecha, 'DD/MM/YYYY'), e2.estado, e2.municipio, e2.colonia,
                e2.carpeta_investigacion, e2.extravio_id, p.persona_id
            FROM persona p 
            LEFT JOIN extraviado e ON e.persona_id=p.persona_id
            LEFT JOIN extravio e2 ON e2.extravio_id=e.extravio_id
            LEFT JOIN registro_rf rr ON rr.persona_id=p.persona_id
            WHERE p.persona_id=%s AND rr.tipo=%s LIMIT 1
        """
        columns = ("NOMBRE", "AP_PATERNO", "AP_MATERNO", "EDAD", 
                "FECHA EXTRAVIO", "ESTADO EXTRAVIO", "MUNICIPIO EXTRAVIO", "COLONIA EXTRAVIO",
                "CARPETA_INVESTIGACION", "EXTRAVIO_ID", "PERSONA_ID")
        return self.execute(query, (idx, person_type), formatting=lambda response: response_to_dict(response, columns)[0], **kwargs)

    def create_alert(self, data, **kwargs):
        query = """
            INSERT INTO alerta_localizacion (
                "extravio_id", "coord", "cloud_rf_id", "usuario_id", "foto_consulta", "probabilidad", "fecha"
            ) VALUES (
                %(extravio_id)s, public.ST_GeomFromText('POINT(%(COORD_X)s %(COORD_Y)s)', 4326), 
                %(cloud_rf_id)s, %(usuario_id)s, %(foto_consulta)s, %(probabilidad)s, %(fecha)s
            ) RETURNING "alerta_id"
        """
        return self.execute(query, data, commit=True, formatting=lambda response:response[0][0], **kwargs)


    def read_alerts_by_zone(self, data, **kwargs):
        query = """
            SELECT 
                al.alerta_id, 
                p.nombre, p.ap_paterno, p.ap_materno,
                public.ST_Y(public.ST_TRANSFORM(al.coord ,4326)), 
                public.ST_X(public.ST_TRANSFORM(al.coord ,4326)),
                al.cloud_rf_id,
                cast(al.probabilidad*100 AS float), 
                public.ST_Y(public.ST_TRANSFORM(e.coord ,4326)), 
                public.ST_X(public.ST_TRANSFORM(e.coord ,4326)),
                to_char(e.fecha, 'DD/MM/YYYY HH:MI:SS'), 
                to_char(al.fecha, 'DD/MM/YYYY HH:MI:SS'), 
                e.carpeta_investigacion,
                e.extravio_id
            FROM alerta_localizacion al 
            LEFT JOIN usuario u ON u.usuario_id=al.usuario_id
            LEFT JOIN extravio e ON e.extravio_id=al.extravio_id 
            LEFT JOIN extraviado e2 ON e2.extravio_id=e.extravio_id 
            LEFT JOIN persona p ON p.persona_id=e2.persona_id 
            WHERE u.zona = %(zone)s OR %(all)s
            ORDER BY e.fecha DESC
        """ 
        columns = (
                "alerta_id", "nombre", "ap_paterno" , "ap_materno" ,"lat_consulta",  "lng_consulta", "cloud_rf_id", 
                "probabilidad",  "lat_extravio", "lng_extravio", "fecha_desaparicion", "fecha_consulta", "carpeta_investigacion", "extravio_id")
        return self.execute(query, data, formatting=lambda response: response_to_dict(response, columns), **kwargs)


    def read_alert(self, idx, **kwargs):
        query = """
            SELECT 
                public.ST_Y(public.ST_TRANSFORM(al.coord ,4326)), 
                public.ST_X(public.ST_TRANSFORM(al.coord ,4326)),
                al.cloud_rf_id, 
                encode(al.foto_consulta , 'base64'),
                cast(al.probabilidad*100 as float),
                to_char(e.fecha, 'DD/MM/YYYY'), 
                to_char(al.fecha, 'DD/MM/YYYY'), 
                e.carpeta_investigacion 
            FROM alerta_localizacion al
            LEFT JOIN usuario u ON u.usuario_id=al.usuario_id
            LEFT JOIN extravio e ON e.extravio_id=al.extravio_id
            WHERE al.alerta_id = %s
        """ 
        columns = ("lat_consulta",  "lng_consulta", "cloud_rf_id", "foto_consulta", 
                "probabilidad", "fecha_desaparicion", "fecha_consulta", "carpeta_investigacion")
        return self.execute(query, (idx, ), formatting=lambda response: response_to_dict(response, columns)[0] if response else None, 
            **kwargs)