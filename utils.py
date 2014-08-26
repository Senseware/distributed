import requests
import pytz
from django.db.models.fields import DateTimeField
from django.db.models.fields.related import ForeignKey
from django.utils.dateparse import parse_date, parse_datetime, parse_time



def json_to_datetime(s):
    """ Convert JSON to time zone aware datetime """
    dt = parse_datetime(s)
    if not dt.tzinfo:
        tz = pytz.timezone('Africa/Johannesburg')
        dt = tz.localize(dt)
    return dt



def unserialize_json(data, model_class):
    """ Take raw json data and unserialize to be compatible with a Django model """
    for field_name in data.keys():
        if not data[field_name]:
            continue
        value = data[field_name]
        # field type
        field_class = model_class._meta.get_field_by_name(field_name)[0]

        # foreign key - lookup based on uuid
        if issubclass(ForeignKey, field_class.__class__):
            value = field_class.related_field.model.objects.get(uuid=data[field_name])

        # datetime
        elif issubclass(DateTimeField, field_class.__class__):
            value = parse_datetime(data[field_name])
            # if not timezone aware default to SAST
            if not value.tzinfo:
                value = pytz.timezone('Africa/Johannesburg').localize(value)
        # done
        data[field_name] = value
    return data


    
