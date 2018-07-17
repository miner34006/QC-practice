# coding: utf-8


import sys
import unittest

import requests

from src.AlmRestfulClient import AlmRestfulClient


class AlmRestfulClientTestCase(unittest.TestCase):

    username = 'username'
    password = 'password'
    domain = 'domain'
    project = 'project'

    def test_isAuthenticatedWhenNotAuthenticated(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        self.assertNotEqual(True, client.isAuthenticated())

    def test_isAuthenticatedWhenAuthenticated(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        client.login()
        self.assertTrue(client.isAuthenticated())

    def test_logout(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        client.login()
        client.logout()
        self.assertNotEqual(True, client.isAuthenticated())

    def test_getValidBasicAuthorizationHeader(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        username = 'username'
        password = 'password'
        template = {'Authorization': 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='}
        self.assertEqual(template, client._getValidBasicAuthorizationHeader(username, password))

    def test_loginWithCorrectData(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        self.assertTrue(client.login())

    def test_loginWithIncorrectData(self):
        client = AlmRestfulClient('username', self.password, self.domain, self.project)
        self.assertFalse(client.login())

    def test_loginAfterLogin(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        client.login()
        self.assertTrue(client.login())

    def test_containsCookieAfterLogin(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        client.login()
        self.assertIn('LWSSO_COOKIE_KEY', client._session.cookies.get_dict().keys())

    def test_createSessionWithoutLogin(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        self.assertFalse(client.createSession())

    def test_containsCookiesAfterCreateSession(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        client.login()
        client.createSession()

        self.assertIn('X-XSRF-TOKEN', client._session.cookies.get_dict().keys())
        self.assertIn('QCSession', client._session.cookies.get_dict().keys())

    def test_getEntityWithCorrectData(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        client.login()
        client.createSession()
        self.assertIsInstance(client.getEntity('tests'), list)

    def test_getEntityWithIncorrectData(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        client.login()
        client.createSession()
        with self.assertRaises(ValueError):
            client.getEntity('entity')

    def test_getEntityWithoutLoginAndSession(self):
        client = AlmRestfulClient(self.username, self.password, self.domain, self.project)
        with self.assertRaises(requests.HTTPError):
            self.assertRaises(client.getEntity('tests'))


if __name__ == '__main__':
    if len(sys.argv) == 5:
        AlmRestfulClientTestCase.project = sys.argv.pop()
        AlmRestfulClientTestCase.domain = sys.argv.pop()
        AlmRestfulClientTestCase.password = sys.argv.pop()
        AlmRestfulClientTestCase.username = sys.argv.pop()
    else:
        sys.exit(1)

    unittest.main()

