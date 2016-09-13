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

from __future__ import print_function
from __future__ import absolute_import
import sys
sys.path.append('..')
from settings.settings import Settings
settings = Settings.load('Neurodata')
import urllib
import boto3
import json
import cStringIO
from PIL import Image
from ndlib.ndlib import MortonXYZ
from ndlib.ndtype import *
from spdb.cube import Cube
from ndqueue.ingestqueue import IngestQueue
from nddynamo.tileindexdb import TileIndexDB
from ndbucket.tilebucket import TileBucket
from ndbucket.cuboidbucket import CuboidBucket
from nddynamo.cuboidindexdb import CuboidIndexDB
from ndqueue.ndserializer import NDSerializer
from ndingestproj.ingestproj import IngestProj
ProjClass = IngestProj.load('Neurodata')

def lambda_handler(event, context):
  """Arrange data in the state database and ready it for ingest"""
  
  # receive SNS notification event
  # message_id, receipt_handle = ???
  message = event['Records'][0]['Sns']['Message']
  supercuboid_key, message_id, receipt_handle = NDSerializer.decodeIngestMessage(message)

  # create ndproj from SNS notification
  nd_proj, (morton_index, time_index) = ProjClass.fromSupercuboidKey(supercuboid_key)
  [x_tile, y_tile, z_tile] = MortonXYZ(morton_index)

  # create a supercuboid from the slab
  cube = Cube.getCube(settings.SUPER_CUBOID_SIZE, IMAGE, UINT8)
  cube.zeros()
  
  cuboidindex_db = CuboidIndexDB(nd_proj.project_name, endpoint_url='http://localhost:8000')
  cuboid_bucket = CuboidBucket(nd_proj.project_name, endpoint_url='http://localhost:4567')

  tile_bucket = TileBucket(nd_proj.project_name, endpoint_url='http://localhost:4567')
  # read all 64 tiles from bucket into a slab
  for z_index in range(z_tile, settings.SUPER_CUBOID_SIZE[2], 1):
    try:
      image_data, message_id, receipt_handle = tile_bucket.getObject(nd_proj.channel_name, nd_proj.resolution, x_tile, y_tile, z_index, time_index)
      cube.data[z_index, :, :] = np.asarray(Image.open(cStringIO.StringIO(image_data)))
    except Exception as e:
      print ("Executing exception")
      pass

  # import pdb; pdb.set_trace()
  # insert supercuboid if it has data
  if cube.isNotZeros() or True:
    cuboidindex_db.putItem(nd_proj.channel_name, nd_proj.resolution, x_tile, y_tile, z_tile)
    cuboid_bucket.putCube(nd_proj.channel_name, nd_proj.resolution, morton_index, blosc.pack_array(data))
  
  # remove message from ingest queue
  ingest_queue = IngestQueue(nd_proj, endpoint_url='http://localhost:4568')
  ingest_queue.deleteMessage(message_id, receipt_handle)

  # insert message to cleanup queue
  cleanup_queue = CleanupQueue(nd_proj, endpoint_url='htp://localhost:4568')
  cleanup_queue.sendMessage(supercuboid_key)