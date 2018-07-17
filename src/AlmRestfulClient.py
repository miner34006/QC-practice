import re
import requests
import base64
import xml.etree.ElementTree as ET


class AlmRestfulClient:
    _baseUrl = "https://almalmqc1250saastrial.saas.hpe.com/qcbin"

    def __init__(self, username, password, domain, project):
        self.username = username
        self.password = password
        self.domain = domain
        self.project = project

        self._session = requests.Session()

    def __del__(self):
        self._session.close()

    def login(self):
        """Logging in to system with standard http login (basic authentication)

        :return: True if login successful, False otherwise
        :rtype: bool
        """
        authenticationStatus = self.isAuthenticated()
        if authenticationStatus is True:
            return True

        authenticationUrl = authenticationStatus + '/authenticate'
        authorizationHeader = self._getValidBasicAuthorizationHeader(self.username, self.password)

        self._session.headers.update(authorizationHeader)
        self._session.headers.update({'Accept': 'application/xml'})

        response = self._session.get(authenticationUrl)

        failAuthentication = False
        successAuthentication = True

        if response.status_code == requests.codes.ok:
            setCookie = response.headers.get('Set-Cookie')
            if 'LWSSO_COOKIE_KEY' in setCookie:
                self._session.cookies.update({
                    'LWSSO_COOKIE_KEY': re.search('LWSSO_COOKIE_KEY=(\S+);', setCookie).group(1),
                })
                return successAuthentication
            else:
                return failAuthentication
        else:
            return failAuthentication

    def createSession(self):
        """Create session with server and update/create cookies

        :return: True if creating session successful, False otherwise
        :rtype: bool
        """
        requestUrl = self._baseUrl + '/rest/site-session'
        response = self._session.post(requestUrl)

        failSessionCreation = False
        successSessionCreation = True

        if response.status_code == requests.codes.ok:
            setCookie = response.headers['Set-Cookie']
            if ('X-XSRF-TOKEN' in setCookie and 'QCSession' in setCookie):
                self._session.cookies.update({
                    'X-XSRF-TOKEN': re.search('XSRF-TOKEN=(\S+)', setCookie).group(1),
                    'QCSession': re.search('QCSession=(\S+)', setCookie).group(1),
                })
                return successSessionCreation
            else:
                return failSessionCreation
        else:
            return failSessionCreation

    def logout(self):
        """Close session on server

        :return: True if logout successful, False otherwise
        :rtype: bool
        """
        #TODO clear cookies in self._session

        logoutUrl = self._baseUrl + '/authentication-point/logout'
        response = requests.get(logoutUrl)
        return response.status_code == requests.codes.ok

    def isAuthenticated(self):
        """Check user authentication status

        :raises: requests.HTTPError

        :return: True if authenticated, a url to authenticate against if not authenticated
        :rtype: bool, str
        """
        response = self._session.get(self._baseUrl + '/rest/is-authenticated')
        if response.status_code == requests.codes.ok:
            return True

        elif response.status_code == requests.codes.unauthorized:
            authenticationUrl = (re.search('\"(.*)\"', response.headers.get('WWW-Authenticate'))).group(1)
            return authenticationUrl

        else:
            raise response.raise_for_status()

    def getStringRepresentationOfEntity(self, entityType, entityId=None, query=None):
        """Get xml data of an entity

        :param entityType: type of entity to get:
            tests/test-sets/test-configs/test-set-folders/test-instances/runs/release-cycles/defects
        :type entityType: str

        :param entityId: id of entity to get. If None returns all instances of entity
        :type entityId: str | int

        :param query: query string to filter data. e.g: {name[Basic]}
        :type query: str

        :return: requested entity(s)
        :rtype: list of entities
        """
        entities = ['tests', 'test-sets', 'test-configs',
                    'test-set-folders', 'test-instances',
                    'runs', 'release-cycles', 'defects']

        if entityType not in entities:
            raise ValueError("Wrong entity type;")

        entityRequestUrl = '{0}/rest/domains/{1}/projects/{2}/{3}'.format(self._baseUrl, self.domain, self.project, entityType)
        if entityId is not None:
            entityRequestUrl = entityRequestUrl + '/{0}'.format(entityId)

        response = self._session.get(entityRequestUrl, params={'query': query})

        # TODO parse objects in python representation
        xml = ET.fromstring(response.content)
        return xml.findall('Entity')

    def _getValidBasicAuthorizationHeader(self, username, password):
        """Encode username and password with 64encode for basic authorization

        :param username: username to be encoded
        :type username: str

        :param password: password to be encoded
        :type password: str

        :return: header with auth data
        :rtype: dict
        """
        usernameWithPassword = '{0}:{1}'.format(username, password)
        encodeString = base64.b64encode(str.encode(usernameWithPassword)).decode("utf-8")
        authorizationHeader = {'Authorization': 'Basic {0}'.format(encodeString)}
        return authorizationHeader

