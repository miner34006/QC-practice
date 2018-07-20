"""QC client module"""

import json
import re
import sys

import requests

import constants
import qc_exceptions
import quality_center_utils
import utils
from constants import Entities


# check QA environment
#from framework_constants import Framework
#qaenv = os.environ.get('QAENV', Framework.CODEBASE)
#sys.path.append(qaenv + '/modules/')


class QcClient(object):
    """Class object of QcClient"""

    def __init__(self, username, password, project="442994577_DEMO"):
        """Initiate a REST session to Quality Center server

        :param project: project in QC
        :type project: str
        :return: self
        """
        self.baseUrl = "https://almalmqc1250saastrial.saas.hpe.com/qcbin/"
        self.domain = "DEFAULT_442994577"
        self.project = project

        self.username = username
        self.password = password

        self.url = '{0}rest/domains/{1}/projects/{2}/'.format(self.baseUrl, self.domain, self.project)
        self.session = requests.session()

        self.session.headers.update({'Accept': 'application/xml'})

    def __enter__(self):
        try:
            if not self.login():
                raise requests.exceptions.HTTPError("Exception while login, check username and password")

            if not self.createSession():
                raise requests.exceptions.HTTPError("Exception while creating session")

        except requests.exceptions.HTTPError as e:
            if self.logout():
                raise e
            else:
                raise requests.exceptions.HTTPError('Exception while logout')

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.logout():
            raise requests.exceptions.HTTPError('Exception while logout')

    def login(self):
        """Logging in to system with standard http login (basic authentication)

        :return: True if login successful, False otherwise
        :rtype: bool
        """
        authenticationStatus = self.isAuthenticated()
        if authenticationStatus is True:
            return True

        # authenticationUrl = authenticationStatus + '/authenticate'
        # authorizationHeader = self._getValidBasicAuthorizationHeader(self.username, self.password)
        #
        # self._session.headers.update(authorizationHeader)
        # self._session.headers.update({'Accept': 'application/xml'})

        authenticationUrl = 'https://login.software.microfocus.com/msg/actions/doLogin.action'
        data = 'username={0}&password={1}'.format(self.username, self.password)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'login.software.microfocus.com',
        }

        response = requests.post(authenticationUrl, data=data, headers=headers)

        failedAuthentication = False
        successAuthentication = True

        if response.status_code == requests.codes.ok:
            if 'LWSSO_COOKIE_KEY' in response.cookies.get_dict():
                self.session.cookies.set('LWSSO_COOKIE_KEY', response.cookies.get('LWSSO_COOKIE_KEY'))
                return successAuthentication
            else:
                return failedAuthentication
        else:
            return failedAuthentication

    def createSession(self):
        """Create session with server and update/create cookies

        :return: True if creating session successful, False otherwise
        :rtype: bool
        """

        requestUrl = self.baseUrl + 'rest/site-session'
        response = self.session.post(requestUrl)

        failedSessionCreation = False
        successSessionCreation = True

        if response.status_code == requests.codes.created:
            cookies = response.cookies.get_dict()
            if ('XSRF-TOKEN' in cookies and 'QCSession' in cookies):
                self.session.cookies.set(
                    'X-XSRF-TOKEN',
                    response.cookies.get('XSRF-TOKEN'),
                    domain='almalmqc1250saastrial.saas.hpe.com'
                )
                return successSessionCreation
            else:
                return failedSessionCreation
        else:
            return failedSessionCreation


    def isAuthenticated(self):
        """Check user authentication status

        :raises: requests.HTTPError

        :return: True if authenticated, a url to authenticate against if not authenticated
        :rtype: bool, str
        """
        response = self.session.get(self.baseUrl + 'rest/is-authenticated')
        if response.status_code == requests.codes.ok:
            return True

        elif response.status_code == requests.codes.unauthorized:
            authenticationUrl = (re.search('\"(.*)\"', response.headers.get('WWW-Authenticate'))).group(1)
            return authenticationUrl

        else:
            raise response.raise_for_status()

    def logout(self):
        """Close session on server and clear cookies

        :return: True if logout successful, False otherwise
        :rtype: bool
        """

        logoutUrl = self.baseUrl + 'authentication-point/logout'
        response = self.session.get(logoutUrl)

        successLogout = True
        failedLogout = False

        if response.status_code == requests.codes.ok:
            self.session.cookies.clear()
            return successLogout
        else:
            return failedLogout

    @utils.ResetSession
    def GetEntity(self, entityType, entityId=None, query=None):
        """Get an entity

        :param entityType: type of entity to get:
            tests/test-sets/test-configs/test-set-folders/test-instances/runs/release-cycles/defects
        :type entityType: str
        :param entityId: id of entity to get. If None returns all instances of entity
        :type entityId: str | int
        :param query: query string to filter data. e.g: {name[Basic]}
        :type query: str
        :return: requested entity(s)
        :rtype: dict
        """
        url = "{url}{entityType}".format(url=self.url, entityType=entityType)
        if entityId:
            url += "/{0}".format(entityId)
        if query:
            url += "?page-size=max&query={0}".format(query)
        request = self.session.get(url, headers={'Accept': 'application/json'})
        if request.status_code == 401:
            raise qc_exceptions.QCAuthenticationError("Not logged in")
        content = json.loads(request.content)
        if request.status_code == 200:
            data = utils.ConvertJsonToDict(content)
            return data
        raise qc_exceptions.QCError("Failed to get data of type '{0}'. [{1}] {2}. {3}".format(entityType,
                                                                                              request.status_code,
                                                                                              content['Title'], url))

    @utils.ResetSession
    def GetFields(self, entityType):
        """Get entity's fields

        :param entityType: type of entity to get fields for
        :type entityType: str
        :return: requested fields for entity
        :rtype: list
        """
        url = self.url + "customization/entities/{0}/fields".format(entityType)
        request = self.session.get(url, headers={'Accept': 'application/json'})
        if request.status_code == 401:
            raise qc_exceptions.QCAuthenticationError("Not logged in")
        content = json.loads(request.content)
        if request.status_code == 200:
            return content["Fields"]["Field"]
        raise qc_exceptions.QCError("Failed to get data of type '{0}'. [{1}] {2}. {3}".format(entityType,
                                                                                              request.status_code,
                                                                                              content['Title'], url))

    @utils.ResetSession
    def UpdateEntity(self, entityType, entityData, entityId):
        """Update an entity or multiple entities

        :param entityType: type of entity to update
        :type entityType: str
        :param entityData: data of entity(s) to update
        :type entityData: dict
        :param entityId: id of entity to update if updating multiple instances at once
        :type entityId: int | str
        :return: content of updated data
        :rtype: dict
        """
        url = "{url}{entity}/{id}".format(url=self.url, entity=entityType, id=entityId)
        data = utils.DictToXml(entityData, re.sub(r's$', '', entityType))
        request = self.session.put(url, data=data, headers={'Accept': 'application/json',
                                                            'Content-Type': 'application/xml'})
        if request.status_code == 401:
            raise qc_exceptions.QCAuthenticationError("Not logged in")
        content = json.loads(request.content)
        if request.status_code == 200:
            return content
        raise qc_exceptions.QCError("Failed to update entity. {0}".format(content['Title']))

    @utils.ResetSession
    def CreateEntity(self, entityType, entityData):
        """Create an entity

        :param entityType: type of entity to create. e.g: defect, run, test
        :type entityType: str
        :param entityData: data to update. Class must inherit from base_entity.BaseEntity
        :type entityData: BaseEntity
        :return: created object data
        :rtype: dict
        """
        url = "{url}{entity}".format(url=self.url, entity=entityType)
        request = self.session.post(url, data=entityData.ToXml(), headers={'Content-Type': 'application/xml',
                                                                           'Accept': 'application/json'})
        if request.status_code == 401:
            raise qc_exceptions.QCAuthenticationError("Not logged in")
        content = json.loads(request.content)
        if request.status_code in [200, 201]:
            return utils.ConvertJsonToDict(content)
        raise qc_exceptions.QCError("Failed to create entity. {0}".format(content['Title']))

    @utils.ResetSession
    def GetTestSetById(self, testSetId):
        """Get test-set by id

        :param testSetId: ID of test-set
        :type testSetId: str | int
        :return: list of dicts representing test-set
        :rtype: list
        """
        testSet = self.GetEntity('test-sets', query='{{id["{0}"]}}'.format(testSetId))
        return testSet

    @utils.ResetSession
    def GetRuns(self, runId=None, instanceId=None):
        """Get runs by runId or instanceId

        :param id: ID of run
        :type id: str | int
        :param instanceId: ID of test-instance
        :type instanceId: str | int
        :return: list of dicts representing runs
        :rtype: list
        """
        runId = 'id["{0}"]'.format(runId) if runId else None
        instanceId = 'testcycl-id["{0}"]'.format(instanceId) if instanceId else None
        runs = self.GetEntity('runs', query='{{{0}}}'.format(";".join(filter(None, [runId, instanceId]))))
        return runs

    @utils.ResetSession
    def GetTestByName(self, testName):
        """Get test id by name

        :param testName: ID of test-set
        :type testName: str | int
        :return: list of tests with name testName
        :rtype: list
        """
        test = self.GetEntity('tests', query='{{name["{0}"]}}'.format(testName))
        return test

    @utils.ResetSession
    def GetTestSetByParentId(self, testSetParentId, testSetName=None):
        """Get test-set by id

        :param testSetParentId: ID of test-set
        :type testSetParentId: str | int
        :param testSetName: if want to get by test set name
        :type testSetName: str | int
        :return: list of dicts representing test-set
        :rtype: list
        """
        testSet = self.GetEntity('test-sets', query='{{parent-id["{0}"]{1}}}'.format(testSetParentId,
                                                                                     ';name["{0}"]'.format(
                                                                                             testSetName) if \
                                                                                         testSetName else ""))
        return testSet

    @utils.ResetSession
    def GetTestSetByName(self, testSetName):
        """Get test-set by name

            :param testSetName: name of test-set
            :type testSetName: str
            :return: list of dicts representing test-set
            :rtype: list
            """
        testSet = self.GetEntity('test-sets', query='{{name["{0}"]}}'.format(testSetName))
        return testSet

    @utils.ResetSession
    def GetTestSetFolderByName(self, testSetFolderName):
        """Get test-set by name

            :param testSetFolderName: the prefix of test-set-folder name
            :type testSetFolderName: str
            :return: list of dicts representing test-set-folder
            :rtype: list
        """
        testSetFolder = self.GetEntity('test-set-folders', query='{{name["{0}*"]}}'.format(testSetFolderName))
        return testSetFolder

    @utils.ResetSession
    def GetTestSetFoldersByParentId(self, testSetFolderParentId, testSetFolderName=None):
        """Get test-set by parent ID

            :param testSetFolderParentId: ID of parent test-set-folder
            :type testSetFolderParentId: str
            :param testSetFolderName: the prefix of test-set-folder name
            :type testSetFolderName: str
            :return: list of dicts representing test-set-folder
            :rtype: list
        """
        testSetFolder = self.GetEntity('test-set-folders', query='{{parent-id["{0}"]{1}}}'.format(testSetFolderParentId,
                                                ';name["{0}"]'.format(testSetFolderName) if testSetFolderName else ""))
        return testSetFolder

    @utils.ResetSession
    def GetTestSetFoldersById(self, testSetFolderId):
        """Get test-set-folder by ID

            :param testSetFolderId: id of test-set-folder
            :type testSetFolderId: str
            :return: list of dicts representing test-set-folder
            :rtype: list
        """
        testSetFolder = self.GetEntity('test-set-folders', query='{{id["{0}"]}}'.format(testSetFolderId))
        return testSetFolder

    @utils.ResetSession
    def GetReleaseCyclesByDates(self, id, startDate, endDate):
        """
        get release cycles by given start date and end date

        :param id: id of release cycle
        :type id: str
        :param startDate: start date of release in format Y-M-D
        :type startDate: str
        :param endDate: end date of release in format Y-M-D
        :type endDate: str
        :return: release cycle
        :rtype: list
        """
        releaseCycles = self.GetEntity('release-cycles',
                                       query='{{id["{0}"];start-date[<="{1}"];end-date[>="{2}"]}}'.format(id, startDate,
                                                                                                          endDate))
        return releaseCycles

    @utils.ResetSession
    def GetTestByTestlinkId(self, testlinkId):
        """Get test by Testlink test ID

            :param testlinkId: Testlink test ID (x-###)
            :type testlinkId: str
            :return: dictionary representing test object
            :rtype: dict
            """
        test = self.GetEntity('tests', query='{{user-16["{0}"]}}'.format(testlinkId))
        return test

    @utils.ResetSession
    def GetTestById(self, id, testIdName=None):
        """Get test by ID

            :param id: test ID
            :type id: str
            :param testIdName: test ID name (testlink ID) - x-####|QC-####
            :type testIdName: str
            :return: dictionary representing test object
            :rtype: dict
            """
        id = 'id["{0}"]'.format(id)
        testIdName = 'user-16["{0}"]'.format(testIdName) if testIdName else None
        tests = self.GetEntity('tests', query='{{{0}}}'.format(";".join(filter(None, [id, testIdName]))))
        return tests

    @utils.ResetSession
    def GetTestInstances(self, testSetId=None, testId=None, testConfigId=None, id=None):
        """Get test instances from a test-set

        :param testSetId: ID of test-set
        :type testSetId: str | int
        :param testId: ID of test
        :type testId: str | int
        :param testConfigId: ID of test config
        :type testConfigId: str | int
        :param id: ID of test instance
        :type id: str | int
        :return: list of dictionaries representing tests
        :rtype: list
        """
        id = 'id["{0}"]'.format(id) if id else None
        testSetId = 'cycle-id["{0}"]'.format(testSetId) if testSetId else None
        testId = 'test-id[{0}]'.format(testId) if testId else None
        testConfigId = 'test-config-id[{0}]'.format(testConfigId) if testConfigId else None
        testInstances = self.GetEntity('test-instances',
                                       query='{{{0}}}'.format(
                                               ";".join(filter(None, [testSetId, testId, testConfigId, id]))))
        return testInstances

    @utils.ResetSession
    def GetMandatoryFields(self, entityType):
        """Get mandatory fields for an entity

        :param entityType: name of entity to check. e.g: tests, runs, test-instances
        :type entityType: str
        :return: list of required fields
        """
        request = self.session.get(self.url + "customization/entities/{0}/fields?required=true".format(
                re.sub('s$', '', entityType)), headers={'Accept': 'application/json'})
        if request.status_code == 401:
            raise qc_exceptions.QCAuthenticationError("Not logged in")
        requiredFields = [field['name'] for field in json.loads(request.content)['Fields']['Field']]
        return requiredFields

    @utils.ResetSession
    def GetTestConfigs(self, testId):
        """Get test configurations for test ID

        :param testId: ID of test
        :type testId: str | int
        :return: list of configurations for test ID
        :rtype: list
        """
        testConfigs = self.GetEntity('test-configs', query='{{parent-id["{0}"]}}'.format(testId))
        return testConfigs

    @utils.ResetSession
    def GetTestObjByTcId(self, tcId):
        """Get test object from a testId

        :param tcId: ID of test
        :type tcId: str | int
        :return: list of dictionaries representing tests
        :rtype: list
        """
        testObj = self.GetEntity('tests', query='{{user-16["{0}"]}}'.format(tcId))
        return testObj

    @utils.ResetSession
    def GetTestsByProductComponent(self, productComponent):
        """Get tests by specific product component

        :param productComponent: product component
        :type productComponent: str
        :return: list of dictionaries representing tests
        :rtype: list
        """
        testObj = self.GetEntity('tests', query='{{user-12["{0}"]}}'.format(productComponent))
        return testObj

    @utils.ResetSession
    def GetTestConfigById(self, configId):
        """Get test-config by id

        :param configId: ID of test-config
        :type configId: str | int
        :return: list of dicts representing test-configs for test
        :rtype: list
        """
        testConfig = self.GetEntity('test-configs', query='{{id["{0}"]}}'.format(configId))
        return testConfig

    @utils.ResetSession
    def GetTestParameters(self, testId):
        """Get test parameters for test ID

        :param testId: ID of test
        :type testId: str | int
        :return: list of parameters for test ID
        :rtype: list
        """
        testParameters = self.GetEntity('test-parameters', query='{{parent-id["{0}"]}}'.format(testId))
        return testParameters

    @utils.ResetSession
    def CreateTestRun(self, run, status, instanceDataToUpdate):
        """Report a new test to QC

        :param run: Run object
        :type run: quality_center.run.Run
        :param status: status of test
        :type status: str
        :param instanceDataToUpdate: dict contains data to update test instance with
        :type instanceDataToUpdate: dict
        :return: dict representing new run
        :rtype: dict
        """
        newRun = self.CreateEntity(Entities.RUNS, run)

        finishedRun = self.UpdateEntity(constants.Entities.RUNS,
                                        entityData={'status': status},
                                        entityId=newRun[0]['id'])

        testsToRun = self.GetEntity(constants.Entities.TEST_INSTANCES, entityId=run.testcyclId)[0]
        iterations = quality_center_utils.UpdateIterations(testsToRun['iterations'], status)
        instanceDataToUpdate.update({"iterations": iterations})
        self.UpdateEntity(constants.Entities.TEST_INSTANCES,
                          entityData=instanceDataToUpdate,
                          entityId=run.testcyclId)
        return utils.ConvertJsonToDict(finishedRun)

    @utils.ResetSession
    def CreateTestInstance(self, testInstanceObj):
        """Create a new test instance in QC

        :param testInstanceObj: test instance object
        :type testInstanceObj: test_instance.TestInstance
        :return: dict representing new test instance
        :rtype: dict
        """
        return self.CreateEntity(Entities.TEST_INSTANCES, testInstanceObj)

    @utils.ResetSession
    def UpdateTestInstance(self, testInstanceId, paramsToUpdate):
        """update fields in test instance

        :param testInstanceId: id of test instance to update
        :type testInstanceId: int | str
        :param paramsToUpdate: dict contains params to update in test instance
        :type paramsToUpdate: dict
        :return: dict representing the updated test instance
        :rtype: dict
        """

        testInstance = self.GetTestInstances(id=testInstanceId)
        if not testInstance:
            raise qc_exceptions.QCError("Could not find test instance matching {0}".format(testInstanceId))
        return self.UpdateEntity(constants.Entities.TEST_INSTANCES, entityData=paramsToUpdate,
                                 entityId=testInstance[0]["id"])

    @utils.ResetSession
    def CreateTestSet(self, testSetObj):
        """Create a new test set in QC

        :param testSetObj: test set object
        :type testSetObj: test_set.TestSet
        :return: dict representing new test set
        :rtype: dict
        """
        return self.CreateEntity(Entities.TEST_SETS, testSetObj)


if __name__ == '__main__':

    password = sys.argv.pop()
    username = sys.argv.pop()

    with QcClient(username, password) as client:
        client.session.cookies.set('QCSession', '123', domain='almalmqc1250saastrial.saas.hpe.com')
        print client.isAuthenticated()
