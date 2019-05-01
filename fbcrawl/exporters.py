from scrapy.exporters import BaseItemExporter
from scrapy.utils.serialize import ScrapyJSONEncoder
from scrapy.utils.python import to_bytes
import logging
import zmq
import datetime

class TCPExports(BaseItemExporter):

    def __init__(self,**kwargs):
        self._configure(kwargs, dont_fail=True)
        # self.file = file
        # needs to be updated when migrating to proto-buff
        self.encoder = ScrapyJSONEncoder(**kwargs)
        self.first_item = True
        # creating ZMQ context and socket 
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)

    def start_exporting(self):
        #Connecting the socket 
        self.socket.bind("tcp://127.0.0.1:5000")

    def export_item(self, item):
        #sending the item 
         self.socket.send(str.encode(str(item)))

    def finish_exporting(self):
        #Closing the socket 
        self.socket.close()
