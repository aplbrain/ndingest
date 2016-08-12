# Copyright 2014 NeuroData (http://neurodata.io)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto3
from boto3.dynamodb.conditions import Key, Attr
import botocore

# TODO KL Import this from settings/parameter file
table_name = 'Test'

class IngestDB:

  def __init__(self, project_name='kasthuri11', channel_name='image', resolution=0):

    db = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:8000")
    self.table = db.Table(table_name)
    self.project = project_name
    self.channel = channel_name
    self.resolution = resolution
 
  @staticmethod
  def createTable():
    """Create the ingest database in dynamodb"""
    
    dynamo = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:8000")
    try:
      table = dynamo.create_table(
          TableName = table_name,
          KeySchema = [
            {
              'AttributeName': 'cuboid_key',
              'KeyType': 'HASH'
            }
          ],
          AttributeDefinitions = [
            {
              'AttributeName': 'cuboid_key',
              'AttributeType': 'S'
            },
            {
              'AttributeName': 'task_id',
              'AttributeType': 'N'
            }
          ],
          GlobalSecondaryIndexes = [
            {
              'IndexName': 'task_id',
              'KeySchema': [
                {
                  'AttributeName': 'task_id',
                  'KeyType': 'HASH'
                },
              ],
              'Projection': {
                'ProjectionType': 'ALL'
              },
              'ProvisionedThroughput': {
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
              }
            },
          ],
          ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
          }
      )
      print "Table {} Status: {}".format(table.table_name, table.table_status)
    except Exception as e:
      print e
      raise e


  @staticmethod
  def deleteTable():
    """Delete the ingest database in dynamodb"""

    dynamo = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url="http://localhost:8000")
    try:
      table = dynamo.Table(table_name)
      table.delete()
    except Exception as e:
      print e
      raise e


  def generateKey(self, x, y, z):
    """Generate key for each supercuboid"""
    return {'cuboid_key': '{}&{}&{}&{}&{}&{}'.format(self.project, self.channel, self.resolution, x, y, z/64)}


  def updateItem(self, file_name, task_id=0):
    """Updating item for a give slice number"""
    
    x, y, z = [int(i) for i in file_name.split('.')[0].split('_')]
    key = self.generateKey(x, y, z)
    print key
    
    try:
      self.table.update_item(
          Key = key,
          UpdateExpression = 'ADD slice_list :slice_number SET task_id = :id',
          ExpressionAttributeValues = 
            {
              ':slice_number': set([z]),
              ':id': task_id
            }
      )
    except botocore.exceptions.ClientError as e:
      print e  
      raise e
  
  
  def getItem(self, key):
    """Get the item from the ingest table"""
    
    try:
      response = self.table.query(
          KeyConditionExpression = Key('cuboid_key').eq(key)
      )
      # TODO write a yield function to pop one item at a time
      return response['Items'][0]
    except Exception as e:
      print e
      raise e


  def getTaskItems(self, task_id):
    """Get all the items for a given task from the ingest table"""

    try:
      response = self.table.query(
          IndexName = 'task_id-index',
          KeyConditionExpression = 'task_id = :id',
          ExpressionAttributeValues = {
            ':id' : task_id
          }
      )
      return response
    except Exception as e:
      print e
      raise e


  def deleteItem(self, key):
    """Delete item from database"""
    
    try:
      response = self.table.delete_item(
          Key = self.generateKey(0, 0, 0)
      )
      return response
    except botocore.exceptions.ClientError as e:
      raise e
