import requests
import pytz
from decimal import Decimal
from django.db.models.fields import DateTimeField, DateField, TimeField, DecimalField
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
    all_fields = model_class._meta.get_all_field_names()
    for field_name in data.keys():
        # skip if the model doesn't have that field
        if not (field_name in all_fields):
            continue
        # skip None
        if not data[field_name]:
            continue

        value = data[field_name]
        field_class = model_class._meta.get_field_by_name(field_name)[0]

        # decimal
        if issubclass(DecimalField, field_class.__class__):
            value = Decimal(value)

        # date
        elif issubclass(DateField, field_class.__class__):
            value = parse_date(data[field_name])
        # time
        elif issubclass(DateField, field_class.__class__):
            value = parse_time(data[field_name])
            # if not timezone aware default to SAST
            if not value.tzinfo:
                value = pytz.timezone('Africa/Johannesburg').localize(value)
        # datetime
        elif issubclass(DateTimeField, field_class.__class__):
            value = parse_datetime(data[field_name])
            # if not timezone aware default to SAST
            if not value.tzinfo:
                value = pytz.timezone('Africa/Johannesburg').localize(value)

        # foreign key - lookup based on uuid
        elif issubclass(ForeignKey, field_class.__class__):
            value = field_class.related_field.model.objects.all_with_deleted().get(uuid=data[field_name])

        # done
        data[field_name] = value
    return data


    
