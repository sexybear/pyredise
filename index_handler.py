#!/usr/bin/python2.6.5
#
# Copyright 2011 Christos Spiliopoulos.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



__authors__ = [
  '"Christos Spiliopoulos" <santos.koniordos@gmail.com>',
]



import index_base
import math
    

class IndexHandler(index_base.IndexBase):
    '''
    This class provides basic methods for INDEX manipulation
    '''
    
    def __init__(self, **kwargs):
        index_base.IndexBase.__init__(self, **kwargs)
        
    
    def update_cardinality(self, value = 1):
        ''' updates cardinality '''
        self.pipe.hincrby(self._dict_key, self._cardinality_key, value)
    
    def update_term_idf(self, term, value = 1):  
        ''' updates the # docs containing this term''' 
        self.pipe.hincrby(self._dict_key, term, value)
        
    def add_doc_id(self, doc_id):
        ''' adds this doc_id into our set of DocIds '''
        self.pipe.sadd(self._set_key, doc_id)   
        
    def remove_doc_id(self, doc_id):
        '''removes this doc_id from our set of DocIds '''
        self.pipe.srem(self._set_key, doc_id)         

    def doc_id_exists(self, doc_id):
        ''' checks whether this doc_id exists in our set of DocIds '''
        return self.db.sismember(self._set_key, doc_id) 
        
    def update_term_posting(self, term, doc_id, score):  
        '''
        insert DocId in posting list for the key term, with frequency (of this term in this Doc) as a score
        Every term is a sorted set key in redis server.
        ''' 
        self.pipe.zadd(term, doc_id, score)
                
    def get_term_idf(self, term): 
        ''' calculates the idf for the given term'''
        try: return math.log(  float(self.db.hget(self._dict_key, self._cardinality_key)) / (float(self.db.hget(self._dict_key, term))) )
        except: return False
    
    def piped_get_idf(self, term_list):
        ''' piped version of the above . 
        Because execution of the pipeline is atomic, it is guaranteed that all duplicate or more terms
        in term_list are assigned the same idf (cause in the meanwhile, no other client can call update_term_idf() )
        '''
        self.pipe.hget(self._dict_key, self._cardinality_key)
        for term in term_list:  
            self.pipe.hget(self._dict_key, term)
        
        res = self.flush()
        # res[0] is cardinality and the rest are the idf of every term   
        return [math.log( float(res[0])/float(i) ) for i in res[1:] if i != None]
    
    