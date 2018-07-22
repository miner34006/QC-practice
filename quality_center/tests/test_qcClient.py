# coding: utf-8


import sys
import unittest

from quality_center.qc_client import QcClient
import quality_center.base_entity as base_entity
from quality_center.constants import *
import testUtils


class QcClientTestCase(unittest.TestCase):

    username = 'username'
    password = 'password'

    client = None
    cleanUpList = []

    @classmethod
    def setUpClass(cls):
        cls.client = QcClient(cls.username, cls.password)
        cls.client.login()
        cls.client.createSession()

        cls.testFolder = testUtils.createTestFolder(cls.client)
        cls.cleanUpList.append({'type': Entities.TEST_FOLDERS, 'id': cls.testFolder['id']})

        cls.test = testUtils.createTest(cls.client, cls.testFolder['id'])
        cls.cleanUpList.append({'type': Entities.TESTS, 'id': cls.test['id']})

        cls.testSetFolder = testUtils.createTestSetFolder(cls.client)
        cls.cleanUpList.append({'type': Entities.TEST_SET_FOLDERS, 'id': cls.testSetFolder['id']})

        cls.testSet = testUtils.createTestSet(cls.client, cls.testSetFolder['id'])
        cls.cleanUpList.append({'type': Entities.TEST_SETS, 'id': cls.testSet['id']})

        cls.testInstance = testUtils.createTestInstance(cls.client, cls.test['id'], cls.testSet['id'])
        cls.testRun = testUtils.createTestRun(cls.client, cls.test['id'], cls.testInstance['id'])

    @classmethod
    def tearDownClass(cls):
        for entity in cls.cleanUpList:
            cls.client.deleteEntity(entity['type'], entity['id'])
        cls.client.logout()

    def test_createEntity(self):
        testEntity = type('test', (base_entity.BaseEntity, ), {})()
        testEntity.name = 'Test created from python'
        testEntity.user01 = 'Reviewed'
        testEntity.user03 = '5-Urgent'
        testEntity.user04 = 'Basic'
        testEntity.subtypeId = 'MANUAL'
        testEntity.parentId = self.testFolder['id']

        returnEntity = self.client.CreateEntity(Entities.TESTS, testEntity)[0]
        self.assertEqual(testEntity.name, returnEntity['name'])
        self.assertEqual(testEntity.user01, returnEntity['user-01'])
        self.assertEqual(testEntity.user03, returnEntity['user-03'])
        self.assertEqual(testEntity.user04, returnEntity['user-04'])
        self.assertEqual(testEntity.subtypeId, returnEntity['subtype-id'])
        self.assertEqual(testEntity.parentId, returnEntity['parent-id'])

        self.client.deleteEntity(Entities.TESTS, returnEntity['id'])

    def test_getEntityWithOneParameter(self):
        entities = self.client.GetEntity(Entities.TESTS)
        ids = [entity['id'] for entity in entities]
        self.assertIn(self.test['id'], ids)

    def test_getEntityWithIdParameter(self):
        id = self.test['id']
        entities = self.client.GetEntity(Entities.TESTS, entityId=id)
        self.assertEqual(entities[0], self.test)

    def test_getEntityWithQueryParameter(self):
        query = '{{name["{0}"]}}'.format(self.test['name'])
        entities = self.client.GetEntity(Entities.TESTS, query=query)
        self.assertEqual(entities[0], self.test)

    def test_getEntityWithAllParameters(self):
        query = '{{name["{0}"]}}'.format(self.test['name'])
        id = self.test['id']
        entities = self.client.GetEntity(Entities.TESTS, entityId=id, query=query)
        self.assertEqual(entities[0], self.test)

    def test_getFields(self):
        fields = self.client.GetFields('defect')
        self.assertNotEqual(len(fields), 0)
    #
    def test_updateEntity(self):
        testEntity = type('test', (base_entity.BaseEntity,), {})()
        testEntity.name = 'Test created from python'
        testEntity.user01 = 'Reviewed'
        testEntity.user03 = '5-Urgent'
        testEntity.user04 = 'Basic'
        testEntity.subtypeId = 'MANUAL'
        testEntity.parentId = self.testFolder['id']

        returnEntity = self.client.CreateEntity(Entities.TESTS, testEntity)[0]
        self.client.UpdateEntity(Entities.TESTS, {'name': 'newName'}, returnEntity['id'])
        changedEntity = self.client.GetTestById(returnEntity['id'])[0]

        self.assertEqual('newName', changedEntity['name'])

        self.client.deleteEntity(Entities.TESTS, changedEntity['id'])

    def test_getTestSetById(self):
        id = self.testSet['id']
        entities = self.client.GetTestSetById(id)
        self.assertIn(self.testSet, entities)

    def test_getRuns(self):
        runs = self.client.GetRuns()
        self.assertIn(self.testRun, runs)

    def test_getTestByName(self):
        name = self.test['name']
        entities = self.client.GetTestByName(name)
        self.assertIn(self.test, entities)

    def test_getTestSetByParentIdWithOneParameter(self):
        parentId = self.testSet['parent-id']
        entities = self.client.GetTestSetByParentId(parentId)
        self.assertIn(self.testSet, entities)

    def test_getTestSetByParentIdWithName(self):
        parentId = self.testSet['parent-id']
        name = self.testSet['name']
        entities = self.client.GetTestSetByParentId(parentId, testSetName=name)
        self.assertIn(self.testSet, entities)

    def test_getTestSetFoldersById(self):
        name = self.testSetFolder['name']
        folder = self.client.GetTestSetFolderByName(name)[0]
        self.assertEqual(name, folder['name'])

    def test_getTestById(self):
        id = self.test['id']
        entities = self.client.GetTestById(id)
        self.assertIn(self.test, entities)

    def test_getTestInstances(self):
        instances = self.client.GetTestInstances(self.testInstance['id'])
        names = [self.test['name']]
        for instance in instances:
            self.assertIn(instance['name'], names)

    def test_getMandatoryFields(self):
        fields = self.client.GetMandatoryFields(Entities.TESTS)
        self.assertEqual([u'user-04', u'user-03', u'user-01', u'parent-id', u'name', u'subtype-id'], fields)

        fields = self.client.GetMandatoryFields(Entities.TEST_SETS)
        self.assertEqual([u'name'], fields)

    def test_getReleaseCyclesByDates(self):
        # TODO create cycle for testing
        cycle = self.client.GetReleaseCyclesByDates('1001', '2018-07-10', '2018-07-11')[0]
        self.assertEqual('first cycle', cycle['name'])

    def test_getTestConfigs(self):
        # TODO create test with configs for testing
        config = self.client.GetTestConfigById(1119)
        self.assertEqual(config[0]['name'], 'Edit Profile Page')

    def test_getTestConfigById(self):
        # TODO create test config for testing
        config = self.client.GetTestConfigById(1169)[0]
        self.assertEqual(config['name'], 'Determine')

    def test_getTestParameters(self):
        # TODO create test with params for testing
        params = self.client.GetTestParameters(170)
        self.assertEqual(params[0]['name'], 'first')
        self.assertEqual(params[1]['name'], 'second')

    @unittest.skip('Not enough permission for that test, could not create additional fields')
    def test_getTestByTestlinkId(self):
        pass

    @unittest.skip('Not enough permission for that test, could not create additional fields')
    def test_getTestObjByTcId(self):
        pass

    @unittest.skip('Not enough permission for that test, could not create additional fields')
    def test_getTestsByProductComponent(self):
        pass

    @unittest.skip('In develop')
    def test_createTestRun(self):
        runEntity = type('run', (base_entity.BaseEntity,), {})()
        runEntity.name = 'Test run created from python'
        runEntity.testId = self.test['id']
        runEntity.testcyclId = self.testInstance['id']
        runEntity.subtypeId = 'hp.qc.run.MANUAL'
        runEntity.owner = 'polyanok.bd_edu.spbstu.ru'

        returnEntity = self.client.CreateTestRun(runEntity, 'Failed', {})[0]

        self.assertEqual(runEntity.name, returnEntity['name'])
        self.assertEqual(runEntity.testId, returnEntity['test-id'])
        self.assertEqual(runEntity.testcyclId, returnEntity['testcycl-id'])
        self.assertEqual(runEntity.subtypeId, returnEntity['subtype-id'])
        self.assertEqual(runEntity.owner, returnEntity['owner'])

        self.client.deleteEntity(Entities.RUNS, returnEntity['id'])

    @unittest.skip('In develop')
    def test_createTestInstance(self):
        testInstanceEntity = type('test-instance', (base_entity.BaseEntity,), {})()
        testInstanceEntity.testId = self.test['id']
        testInstanceEntity.cycleId = self.testSet['id']
        testInstanceEntity.subtypeId = 'hp.qc.test-instance.MANUAL'

        returnEntity = self.client.CreateTestInstance(testInstanceEntity)[0]

        self.assertEqual(testInstanceEntity.testId, returnEntity['test-id'])
        self.assertEqual(testInstanceEntity.cycleId, returnEntity['cycle-id'])
        self.assertEqual(testInstanceEntity.subtypeId, returnEntity['subtype-id'])

        self.client.deleteEntity(Entities.TEST_INSTANCES, returnEntity['id'])

    def test_updateTestInstance(self):
        testInstanceEntity = type('test-instance', (base_entity.BaseEntity,), {})()
        testInstanceEntity.testId = self.test['id']
        testInstanceEntity.cycleId = self.testSet['id']
        testInstanceEntity.subtypeId = 'hp.qc.test-instance.MANUAL'

        returnEntity = self.client.CreateEntity(Entities.TEST_INSTANCES, testInstanceEntity)[0]
        self.client.UpdateTestInstance(returnEntity['id'], {'status': 'Failed'})
        changedEntity = self.client.GetEntity(Entities.TEST_INSTANCES, returnEntity['id'])[0]

        self.assertEqual('Failed', changedEntity['status'])

        self.client.deleteEntity(Entities.TEST_INSTANCES, changedEntity['id'])

    def test_CreateTestSet(self):
        testSetEntity = type('test-set', (base_entity.BaseEntity,), {})()
        testSetEntity.name = 'TestSet'
        testSetEntity.subtypeId = 'hp.qc.test-set.default'

        returnEntity = self.client.CreateTestSet(testSetEntity)[0]
        self.assertEqual(testSetEntity.name, returnEntity['name'])
        self.assertEqual(testSetEntity.subtypeId, returnEntity['subtype-id'])

        self.client.deleteEntity(Entities.TEST_SETS, returnEntity['id'])

if __name__ == '__main__':
    if len(sys.argv) == 3:
        QcClientTestCase.password = sys.argv.pop()
        QcClientTestCase.username = sys.argv.pop()
    else:
        sys.exit(1)

    unittest.main()
