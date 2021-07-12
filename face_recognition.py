# /usr/bin/python3.8

import json
import requests

from typing import Union
from icecream import ic




class FaceRecognitionService:

    def __init__(self, path):
        with open(path) as file:
            data = json.loads(file.read())
            self.token = data['token']
            self.url = data['url']
        self.headers = dict(token=self.token)
        self.urls = {
            'list_persons': self.url.format('subject'),
            'create_person': self.url.format('subject/v2'),
            'recognize': self.url.format('photo/search'),
            'recognize-all': self.url.format('photo/search/all'),
            'verify': self.url.format('photo/verify/%s'),

        }


    def _validate_response(func):
        def inner(self, *args, **kwargs):
            response = func(self, *args, **kwargs)
            if response.status_code == 200:
                return response.json()
        return inner

    @_validate_response    
    def list_persons(self) -> list:
        response = requests.get(self.urls['list_persons'], headers=self.headers)
        return response

    @_validate_response    
    def add_person(self, name: str, photo: bytearray, store: int=1) -> dict:
        """
        Function: create_person
        Summary: Create a person to luxand cloud
        Examples: fr.create_person('Fulanito', photo.read(), store=1)
        Attributes: 
            @param (name:str):Name of the person
            @param (photo:bytearray):Photo in bytes array
            @param (store:int) default=1: If the photo will be store or not
        Returns: response like json
        """
        # ic(photo[:10])
        response = requests.post(self.urls['create_person'], data=dict(name=name, store=store), 
            files=dict(photo=photo), headers=self.headers)
        ic(response.text)
        return response

    @_validate_response    
    def add_face_to_person(self, idx: int, photo: bytearray) -> dict:
        """
        Function: create_person
        Summary: Create a person to luxand cloud
        Examples: fr.create_person('Fulanito', photo.read(), store=1)
        Attributes: 
            @param (name:str):Name of the person
            @param (photo:bytearray):Photo in bytes array
            @param (store:int) default=1: If the photo will be store or not
        Returns: response like json
        """
        url = f"{self.urls['list_persons']}/{idx}"
        response = requests.post(url, files=dict(photo=photo), headers=self.headers)
        return response


    @_validate_response    
    def list_person_faces(self, idx: int) -> dict:
        url = f"{self.urls['list_persons']}/{idx}"
        response = requests.post(url, headers=self.headers)
        return response


    @_validate_response    
    def delete_all_persons(self):
        response = requests.delete(self.urls['list_persons'], headers=self.headers)
        if response.status_code == 200:
            return response
        else: 
            return None


    @_validate_response        
    def recognize(self, photo: bytearray, deep: bool=False) -> list:
        """
        Function: recognize
        Summary: Recognize people in the photo with the faces in db
        Examples: recognize(open('photo.jpeg', 'rb').read())
        Attributes: 
            @param (photo:bytearray): photo with people
        Returns: list with the possibilities
        """
        response = requests.post(self.urls['recognize' if not deep else 'recognize-all'], 
            files=dict(photo=photo), headers=self.headers)
        return response


    @_validate_response    
    def verify(self, idx: int, photo: bytearray) -> dict:
        url = self.urls['verify'] % idx
        ic(url)
        response = requests.post(url, files=dict(photo=photo), headers=self.headers)
        return response


