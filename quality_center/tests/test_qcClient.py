# coding: utf-8


import sys
import unittest

import requests

from quality_center.qc_client import QcClient
import quality_center.base_entity as base_entity
from quality_center.constants import *


class QcClientTestCase(unittest.TestCase):

    username = 'username'
    password = 'password'

    def setUp(self):
        self.createdEntities = []

        self.client = QcClient(self.username, self.password)
        self.client.login()
        self.client.createSession()

        testEntity = type('test', (base_entity.BaseEntity,), {})()
        testEntity.name = 'TestEntity'
        testEntity.user01 = 'Reviewed'
        testEntity.user03 = '5-Urgent'
        testEntity.user04 = 'Basic'
        testEntity.subtypeId = 'MANUAL'
        testEntity.parentId = '1173'

        self.testEntity = {
            'type': Entities.TESTS,
            'entity': self._createEntity(Entities.TESTS, testEntity)
        }

        testSetEntity = type('test-set', (base_entity.BaseEntity,), {})()
        testSetEntity.name = 'TestSetEntity'
        testSetEntity.subtypeId = 'hp.qc.test-set.default'
        testSetEntity.parentId = '-2'

        self.testSetEntity = {
            'type': Entities.TEST_SETS,
            'entity': self._createEntity(Entities.TEST_SETS, testSetEntity)
        }

    def tearDown(self):
        for entity in self.createdEntities:
            self.client.deleteEntity(entity['type'], entity['id'])

        self.client.logout()

    def _createEntity(self, type, enity):
        returnEntity = self.client.CreateEntity(type, enity)[0]
        self.createdEntities.append({'type': type, 'id': returnEntity.get('id')})
        return returnEntity

    def _deleteEntity(self, type, enity):
        self.client.deleteEntity(type, enity.get('id'))
        self.createdEntities.remove({'type': type, 'id': enity.get('id')})

    def test_createEntity(self):
        testEntity = type('test', (base_entity.BaseEntity, ), {})()
        testEntity.name = 'Test created from python'
        testEntity.user01 = 'Reviewed'
        testEntity.user03 = '5-Urgent'
        testEntity.user04 = 'Basic'
        testEntity.subtypeId = 'MANUAL'
        testEntity.parentId = '1173'

        returnEntity = self._createEntity(Entities.TESTS, testEntity)
        self.assertEqual(testEntity.name, returnEntity.get('name'))
        self.assertEqual(testEntity.user01, returnEntity.get('user-01'))
        self.assertEqual(testEntity.user03, returnEntity.get('user-03'))
        self.assertEqual(testEntity.user04, returnEntity.get('user-04'))
        self.assertEqual(testEntity.subtypeId, returnEntity.get('subtype-id'))
        self.assertEqual(testEntity.parentId, returnEntity.get('parent-id'))

        self._deleteEntity(Entities.TESTS, returnEntity)

    def test_getEntityWithOneParameter(self):
        entities = self.client.GetEntity(self.testEntity.get('type'))
        ids = [entity.get('id') for entity in entities]
        self.assertIn(self.testEntity.get('entity').get('id'), ids)

    def test_getEntityWithIdParameter(self):
        id = self.testEntity.get('entity').get('id')
        entities = self.client.GetEntity(self.testEntity.get('type'), entityId=id)
        self.assertEqual(entities[0], self.testEntity.get('entity'))

    def test_getEntityWithQueryParameter(self):
        query = '{{name["{0}"]}}'.format(self.testEntity.get('entity').get('name'))
        entities = self.client.GetEntity(self.testEntity.get('type'), query=query)
        self.assertEqual(entities[0], self.testEntity.get('entity'))

    def test_getEntityWithAllParameters(self):
        query = '{{name["{0}"]}}'.format(self.testEntity.get('entity').get('name'))
        id = self.testEntity.get('entity').get('id')
        entities = self.client.GetEntity(self.testEntity.get('type'), entityId=id, query=query)
        self.assertEqual(entities[0], self.testEntity.get('entity'))

    def test_getFields(self):
        fields = self.client.GetFields('defect')
        self.assertNotEqual(len(fields), 0)

    def test_updateEntity(self):
        testEntity = type('test', (base_entity.BaseEntity,), {})()
        testEntity.name = 'Test created from python'
        testEntity.user01 = 'Reviewed'
        testEntity.user03 = '5-Urgent'
        testEntity.user04 = 'Basic'
        testEntity.subtypeId = 'MANUAL'
        testEntity.parentId = '1173'

        returnEntity = self._createEntity(Entities.TESTS, testEntity)
        self.client.UpdateEntity(Entities.TESTS, {'name': 'newName'}, returnEntity.get('id'))
        changedEntity = self.client.GetTestById(returnEntity.get('id'))[0]

        self.assertEqual('newName', changedEntity.get('name'))

        self._deleteEntity(Entities.TESTS, changedEntity)

    def test_getTestSetById(self):
        id = self.testSetEntity.get('entity').get('id')
        entities = self.client.GetTestSetById(id)
        self.assertIn(self.testSetEntity.get('entity'), entities)

    def test_getRuns(self):
        # TODO add test run in setUp and test it
        runs = self.client.GetRuns()
        self.assertNotEqual(len(runs), 0)

    def test_getTestByName(self):
        name = self.testEntity.get('entity').get('name')
        entities = self.client.GetTestByName(name)
        self.assertIn(self.testEntity.get('entity'), entities)

    def test_getTestSetByParentIdWithOneParameter(self):
        parentId = self.testSetEntity.get('entity').get('parent-id')
        entities = self.client.GetTestSetByParentId(parentId)
        self.assertIn(self.testSetEntity.get('entity'), entities)

    def test_getTestSetByParentIdWithName(self):
        parentId = self.testSetEntity.get('entity').get('parent-id')
        name = self.testSetEntity.get('entity').get('name')
        entities = self.client.GetTestSetByParentId(parentId, testSetName=name)
        self.assertIn(self.testSetEntity.get('entity'), entities)

    def test_getTestSetFoldersById(self):
        # TODO create folder for testing
        folder = self.client.GetTestSetFolderByName('My Test Folder')[0]
        self.assertEqual('My Test Folder', folder.get('name'))

    def test_getReleaseCyclesByDates(self):
        # TODO create cycle for testing
        cycle = self.client.GetReleaseCyclesByDates('1001', '2018-07-10', '2018-07-11')[0]
        self.assertEqual('first cycle', cycle.get('name'))

    # def test_getTestByTestlinkId(self):
    #     # TODO

    def test_getTestById(self):
        id = self.testEntity.get('entity').get('id')
        entities = self.client.GetTestById(id)
        self.assertIn(self.testEntity.get('entity'), entities)

    def test_getTestInstances(self):
        # TODO create test-instance for testing
        instances = self.client.GetTestInstances(91)
        names = ['Profiling [1]', 'Flight Reservation [1]', 'Itinerary Page [1]', 'Site_Stability [1]']
        for instance in instances:
            self.assertIn(instance.get('name'), names)

    def test_getMandatoryFields(self):
        fields = self.client.GetMandatoryFields(Entities.TESTS)
        self.assertEqual([u'user-04', u'user-03', u'user-01', u'parent-id', u'name', u'subtype-id'], fields)

        fields = self.client.GetMandatoryFields(Entities.TEST_SETS)
        self.assertEqual([u'name'], fields)

    def test_getTestConfigs(self):
        # TODO create test with configs for testing
        config = self.client.GetTestConfigById(1119)
        self.assertEqual(config[0].get('name'), 'Edit Profile Page')

    # def test_getTestObjByTcId(self):
    #     # TODO
    #
    # def test_getTestsByProductComponent(self):
    #     # TODO

    def test_getTestConfigById(self):
        # TODO create test config for testing
        config = self.client.GetTestConfigById(1169)[0]
        self.assertEqual(config.get('name'), 'Determine')

    def test_getTestParameters(self):
        # TODO create test with params for testing
        params = self.client.GetTestParameters(170)
        self.assertEqual(params[0].get('name'), 'first')
        self.assertEqual(params[1].get('name'), 'second')

    def test_createTestRun(self):
        # TODO edit hardcode values
        runEntity = type('run', (base_entity.BaseEntity,), {})()
        runEntity.name = 'Test run created from python'
        runEntity.testId = '54'
        runEntity.testcyclId = '212'
        runEntity.subtypeId = 'hp.qc.run.MANUAL'
        runEntity.owner = 'polyanok.bd_edu.spbstu.ru'

        returnEntity = self._createEntity(Entities.RUNS, runEntity)
        self.assertEqual(runEntity.name, returnEntity.get('name'))
        self.assertEqual(runEntity.testId, returnEntity.get('test-id'))
        self.assertEqual(runEntity.testcyclId, returnEntity.get('testcycl-id'))
        self.assertEqual(runEntity.subtypeId, returnEntity.get('subtype-id'))
        self.assertEqual(runEntity.owner, returnEntity.get('owner'))

        self._deleteEntity(Entities.RUNS, returnEntity)

    def test_createTestInstance(self):
        testInstanceEntity = type('test-instance', (base_entity.BaseEntity,), {})()
        testInstanceEntity.testId = self.testEntity.get('entity').get('id')
        # TODO edit hardcode value
        testInstanceEntity.cycleId = '8'
        testInstanceEntity.subtypeId = 'hp.qc.test-instance.MANUAL'

        returnEntity = self._createEntity(Entities.TEST_INSTANCES, testInstanceEntity)
        self.assertEqual(testInstanceEntity.testId, returnEntity.get('test-id'))
        self.assertEqual(testInstanceEntity.cycleId, returnEntity.get('cycle-id'))
        self.assertEqual(testInstanceEntity.subtypeId, returnEntity.get('subtype-id'))

        self._deleteEntity(Entities.TEST_INSTANCES, returnEntity)

    def test_updateTestInstance(self):
        testInstanceEntity = type('test-instance', (base_entity.BaseEntity,), {})()
        testInstanceEntity.testId = self.testEntity.get('entity').get('id')
        # TODO edit hardcode value
        testInstanceEntity.cycleId = '8'
        testInstanceEntity.subtypeId = 'hp.qc.test-instance.MANUAL'

        returnEntity = self._createEntity(Entities.TEST_INSTANCES, testInstanceEntity)
        self.client.UpdateTestInstance(returnEntity.get('id'), {'status': 'Failed'})
        changedEntity = self.client.GetEntity(Entities.TEST_INSTANCES, returnEntity.get('id'))[0]

        self.assertEqual('Failed', changedEntity.get('status'))

        self._deleteEntity(Entities.TEST_INSTANCES, changedEntity)


    def test_CreateTestSet(self):
        testSetEntity = type('test-set', (base_entity.BaseEntity,), {})()
        testSetEntity.name = 'Test set created from python'
        testSetEntity.subtypeId = 'hp.qc.test-set.default'

        returnEntity = self._createEntity(Entities.TEST_SETS, testSetEntity)
        self.assertEqual(testSetEntity.name, returnEntity.get('name'))
        self.assertEqual(testSetEntity.subtypeId, returnEntity.get('subtype-id'))

        self._deleteEntity(Entities.TEST_SETS, returnEntity)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        QcClientTestCase.password = sys.argv.pop()
        QcClientTestCase.username = sys.argv.pop()
    else:
        sys.exit(1)

    unittest.main()

