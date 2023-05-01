import json
import os
from django.conf import settings

def read_hall_status(json_filename=None):
    if json_filename != None:
        try:
            json_filepath = os.path.join(settings.ALL_STATUS_FILES_ROOT,json_filename)
            jfp = open(json_filepath,'r')
            hall_status = json.load(jfp)
            
        except:
            return None 