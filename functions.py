from passlib.hash import sha256_crypt
from typing import Union, Tuple, List
from datetime import datetime

def validate_datetime_from_form(form, key: str):
    date_ = form.get(key)
    form[key] = datetime.today() if not date_ else datetime.strptime(date_, '%d/%m/%Y')
    return form

def response_to_dict(response: Union[Tuple[str], List[str]], keys: Tuple[str]):
    return list(map(lambda items: dict(zip(keys, items)), response))


def encript_password(password: str) -> str:
    return sha256_crypt.hash(password)


def verify_password(hash_: str, password: str) -> bool:
    return sha256_crypt.verify(password, hash_)

def extract_suspect_info(form: dict, person_id: int) -> dict:
    return {
            'person_id': person_id,
            'extravio_id': form.get('extravio_id', None),
            'parentezco': form.get('parentezco', None),
            'antecedentes': form.get('antecedentes', None),
            }

def extract_person_info(form: dict) -> dict:
    return {
        'curp': form.get('curp', None),
        'nombre': form.get('nombre', None),
        'a_paterno': form.get('a_paterno', None),
        'a_materno': form.get('a_materno', None),
        'sexo': form.get('sexo', None),
        'fecha_nacimiento': form.get('fecha_nacimiento', None),
        'estatura': form.get('estatura', None),
        'complexion': form.get('complexion', None),
        'tez': form.get('tez', None),
        'controno_cara': form.get('controno_cara', None),
        'cabello': form.get('cabello', None),
        'cejas': form.get('cejas', None),
        'ojos': form.get('ojos', None),
        'nariz': form.get('nariz', None),
        'boca': form.get('boca', None),
        'labios': form.get('labios', None),
        'menton': form.get('menton', None),
        'senas_particulares': form.get('senas_particulares', None),
        'padecimientos': form.get('padecimientos', None),
    }
