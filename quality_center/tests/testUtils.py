# coding: utf-8

import random
import string

import quality_center.base_entity as base_entity
from quality_center.constants import Entities


def getRandomName(length):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(length))

def createTestFolder(client):
    testFolderEntity = type('test-folder', (base_entity.BaseEntity,), {})()
    testFolderEntity.name = getRandomName(5)
    testFolderEntity.parentId = '2'

    return client.CreateEntity(Entities.TEST_FOLDERS, testFolderEntity)[0]


def createTest(client, parentId):
    testEntity = type('test', (base_entity.BaseEntity,), {})()
    testEntity.name = getRandomName(5)
    testEntity.user01 = 'Reviewed'
    testEntity.user03 = '5-Urgent'
    testEntity.user04 = 'Basic'
    testEntity.subtypeId = 'MANUAL'
    testEntity.parentId = parentId

    return client.CreateEntity(Entities.TESTS, testEntity)[0]


def createTestSetFolder(client):
    testSetFolderEntity = type('test-set-folder', (base_entity.BaseEntity,), {})()
    testSetFolderEntity.name = getRandomName(5)

    return client.CreateEntity(Entities.TEST_SET_FOLDERS, testSetFolderEntity)[0]


def createTestSet(client, parentId):
    testSetEntity = type('test-set', (base_entity.BaseEntity,), {})()
    testSetEntity.name = getRandomName(5)
    testSetEntity.subtypeId = 'hp.qc.test-set.default'
    testSetEntity.parentId = parentId

    return client.CreateEntity(Entities.TEST_SETS, testSetEntity)[0]


def createTestInstance(client, testId, testSetId):
    testInstanceEntity = type('test-instance', (base_entity.BaseEntity,), {})()
    testInstanceEntity.testId = testId
    testInstanceEntity.cycleId = testSetId
    testInstanceEntity.subtypeId = 'hp.qc.test-instance.MANUAL'

    return client.CreateEntity(Entities.TEST_INSTANCES, testInstanceEntity)[0]


def createTestRun(client, testId, testInstanceId):
    runEntity = type('run', (base_entity.BaseEntity,), {})()
    runEntity.name = getRandomName(5)
    runEntity.testId = testId
    runEntity.testcyclId = testInstanceId
    runEntity.subtypeId = 'hp.qc.run.MANUAL'
    runEntity.owner = 'polyanok.bd_edu.spbstu.ru'

    return client.CreateEntity(Entities.RUNS, runEntity)[0]

