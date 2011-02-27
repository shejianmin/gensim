#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Radim Rehurek <radimrehurek@seznam.cz>
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl.html


"""
Indexed corpus is a mechanism for random-accessing corpora.

While the standard corpus interface in gensim allows iterating over corpus with
`for doc in corpus: pass`, indexed corpus allows accessing the documents with 
`corpus[docno]` (in O(1) look-up time).
"""

import logging
import shelve

from gensim import interfaces, utils


class IndexedCorpus(interfaces.CorpusABC):
    def __init__(self, fname, index_fname=None):
        """
        Initialize this abstract base class, by loading a previously saved index 
        from `index_fname` (or `fname.index`). This index will allow subclasses 
        to support the `corpus[docno]` syntax (random access to document no. `docno`).
        
        >>> # save corpus in SvmLightCorpus format with an index
        >>> corpus = [[(1, 0.5)], [(0, 1.0), (1, 2.0)]]
        >>> gensim.corpora.SvmLightCorpus.saveIndexedCorpus('testfile.svmlight', corpus)
        
        >>> # load back
        >>> corpus_with_random_access = gensim.corpora.SvmLightCorpus('tstfile.svmlight')
        >>> print corpus_with_random_access[1]
        [(0, 1.0), (1, 2.0)]
        
        """
        if index_fname is None:
            index_fname = fname + '.index'
        try:
            self.index = utils.unpickle(index_fname)
            logging.info("loaded corpus index from %s" % index_fname)
        except:
            self.index = None
        self.length = None
    

    @classmethod
    def saveIndexedCorpus(serializer, fname, corpus, id2word=None, index_fname=None):
        """
        Iterate through the document stream `corpus`, saving the documents to `fname`
        and recording byte offset of each document. Save the resulting index 
        structure to file `index_fname`.
        
        This relies on the underlying corpus class `serializer` providing (in 
        addition to standard iteration):
          * `saveCorpus` method that returns a sequence of byte offsets, one for
             each saved document,
          * the `docbyoffset(offset)` method, which returns a document
            positioned at `offset` bytes within the persistent storage (file).
        
        """
        if index_fname is None:
            index_fname = fname + '.index'
        
        offsets = serializer.saveCorpus(fname, corpus, id2word)
        if offsets is None:
            raise NotImplementedError("called saveIndexedCorpus on class %s which \
            doesn't support indexing!" % serializer.__name__)
        
        # store offsets persistently, using pickle
        logging.info("saving %s index to %s" % (serializer.__name__, index_fname))
        utils.pickle(offsets, index_fname)


    def __len__(self):
        """
        Return cached corpus length if the corpus is indexed. Otherwise delegate 
        `len()` call to base class.
        """
        if self.index is not None:
            return len(self.index)
        if self.length is None:
            logging.info("caching corpus length")
            self.length = sum(1 for doc in self)
        return self.length
    
    
    def __getitem__(self, docno):
        if self.index is None:
            raise RuntimeError("cannot call corpus[docid] without an index")
        return self.docbyoffset(self.index[docno])
#endclass IndexedCorpus
