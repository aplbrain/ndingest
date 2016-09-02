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

import sys
import os
sys.path += [os.path.abspath('../../django')]
import ND.settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'ND.settings'
from nddynamo.tileindexdb import TileIndexDB

project_name = 'kasthuri11'
channel_name = 'image'
resolution = 0

class Test_TileIndexDB():

  def setup_class(self):
    """Setup parameters"""
    TileIndexDB.createTable(endpoint_url='http://localhost:8000')
    self.tileindex_db = TileIndexDB(project_name, channel_name, endpoint_url='http://localhost:8000')
    
  def teardown_class(self):
    """Teardown parameters"""
    TileIndexDB.deleteTable(endpoint_url='http://localhost:8000')
    
  def test_putItem(self):
    """Test data insertion"""
    
    # inserting three values for task 0
    self.tileindex_db.putItem('0_0_1.tif', 0)
    self.tileindex_db.putItem('0_0_2.tif', 0)
    self.tileindex_db.putItem('0_0_3.tif', 0)

    # inserting 2 values for task 1
    self.tileindex_db.putItem('0_0_66.tif', 1)
    self.tileindex_db.putItem('0_0_67.tif', 1)

    # checking if the items were inserted
    item_value = self.tileindex_db.getItem('kasthuri11&image&0&0&0&0')
    assert( item_value['slice_list'] == set([1, 2, 3]) )

    item_value = self.tileindex_db.getItem('kasthuri11&image&0&0&0&1')
    assert( item_value['slice_list'] == set([66, 67]) )
  
  def test_queryTaskItems(self):
    """Test the query over SI"""
    
    item_values, count = self.tileindex_db.getTaskItems(0)
    assert( count == 1 )
    assert( item_values[0]['slice_list'] == set([1, 2, 3]) )


  def test_deleteItem(self):
    """Test item deletion"""
    
    value = self.tileindex_db.deleteItem('0_0_0.tif')
    item_value = self.tileindex_db.getItem('kasthuri11&image&0&0&0&0')
    assert(item_value == None)