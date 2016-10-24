# coding: utf-8
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


class TestAPIViews(TestCase):

    def setUp(self):
        """
        Objetos necessarios para os testes
        :return:
        """
        self.client = APIClient()
        self.user = User.objects.create_user('testuser@test.com', password='testing')
        self.user.save()
        self.token = Token.objects.get(user=self.user)

    def _require_login(self):
        """
        Token do usuario de teste
        :return: APIClient().credentials()
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(self.token))

    def test_login_account(self):
        """
        Login
        :return: 200
        """
        response = self.client.post(path='/v1/rest-auth/login/',
                                    data={"username": 'testuser@test.com', "password": 'testing'}, format='json')
        self.assertEqual(response.status_code, 200,
                         'Expected Response Code 200, received {0} instead.'.format(response.status_code))

    def test_login_account_fail(self):
        """
        Falha no login (credenciais erradas).
        :return: 400
        """
        response = self.client.post('/v1/rest-auth/login/',
                                    {"username": 'testuser@test.com', "password": 'testings'},
                                    format='json')

        self.assertEqual(response.status_code, 400,
            'Expected Response Code 400, received {0} instead.'.format(response.status_code))

    def test_create_account_user(self):
        """
        Criação de conta de usuario.
        :return: 201
        """

        response = self.client.post('/v1/users/',
                                    {"username": 'toni@maluco', "password": 'cidade'},
                                    format='json')

        self.assertEqual(response.status_code, 201,
            'Expected Response Code 201, received {0} instead.'.format(response.status_code))

    def test_update_account_user(self):
        """
        Update de usuario e senha.
        :return: 200
        """
        self._require_login()

        response = self.client.put('/v1/users/' +str(self.user.id)+'/',
                                    {"username": 'toni@malucao', "password": 'cidadeeee'},
                                    format='json')

        self.assertEqual(response.status_code, 200,
            'Expected Response Code 200, received {0} instead.'.format(response.status_code))

    def test_update_account_user_fail(self):
        """
        Update de usuario e senha não autorizados.
        :return: 401
        """
        response = self.client.put('/v1/users/' +str(self.user.id)+'/',
                                    {"username": 'toni@malucao', "password": 'cidadeeee'},
                                    format='json')

        self.assertEqual(response.status_code, 401,
            'Expected Response Code 401, received {0} instead.'.format(response.status_code))

    def test_delete_account_user(self):
        """
        Deleção da conta.
        :return: 204
        """
        self._require_login()
        response = self.client.delete('/v1/users/' +str(self.user.id)+'/', format='json')
        self.assertEqual(response.status_code, 204,
            'Expected Response Code 204, received {0} instead.'.format(response.status_code))

    def test_delete_account_user_fail(self):
        """
        Deleção da conta não autorizado.
        :return: 401
        """
        response = self.client.delete('/v1/users/' +str(self.user.id)+'/', format='json')
        self.assertEqual(response.status_code, 401,
            'Expected Response Code 401, received {0} instead.'.format(response.status_code))

    def test_list_users(self):
        """
        Listagem dos usuários.
        :return: 200
        """
        self._require_login()
        response = self.client.get('/v1/users/', format='json')
        self.assertEqual(response.status_code, 200,
            'Expected Response Code 200, received {0} instead.'.format(response.status_code))

    def test_list_users_fail(self):
        """
        Listagem dos usuários não autorizado.
        :return: 401
        """
        response = self.client.get('/v1/users/', format='json')
        self.assertEqual(response.status_code, 401,
            'Expected Response Code 401, received {0} instead.'.format(response.status_code))