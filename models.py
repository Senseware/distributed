import requests
import uuid
import pytz
from django.conf import settings
from django.db import models
from django.db.models import Max
from django.db.models.fields import DateTimeField
from django.db.models.fields.related import ForeignKey
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime, parse_time
from django.utils.translation import ugettext_lazy as _

from distributed.fields import UUIDField
from distributed.utils import unserialize_json



class UndeleteQuerySet(models.query.QuerySet):
    def delete(self):
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
        for obj in self.all():
            obj.delete()
        self._result_cache = None
    delete.alters_data = True



class UndeleteManager(models.Manager):
    def get_query_set(self):
        return UndeleteQuerySet(self.model, using=self._db).filter(date_deleted__isnull=True)
    
    def all_with_deleted(self):
        return super(UndeleteManager, self).get_query_set()
    
    def only_deleted(self):
        return super(UndeleteManager, self).get_query_set().filter(date_deleted__isnull=False)
    
    def get(self, *args, **kwargs):
        return self.all_with_deleted().get(*args, **kwargs)
    
    def filter(self, *args, **kwargs):
        if "pk" in kwargs:
            return self.all_with_deleted().filter(*args, **kwargs)
        return self.get_query_set().filter(*args, **kwargs)



class UndeleteMixin(models.Model):
    """ Changes delete actions to only set the deleted flag, retrieve querysets accordingly """
    date_deleted              = models.DateTimeField(                 null=True,  editable=False, db_index=True, verbose_name=_('Deleted at'))

    objects = UndeleteManager()

    class Meta:
        abstract = True

    def delete(self, timestamp=None):
        """ Mark related objects as deleted """
        timestamp = timestamp or timezone.now()
        related = [relation.get_accessor_name() for relation in self._meta.get_all_related_objects()]
        # delete related
        for related_name in related:
            objects = getattr(self, related_name).all()
            for obj in objects:
                # Only if they inherit from UndeleteMixin
                if not issubclass(obj.__class__, UndeleteMixin):
                    break
                obj.delete(timestamp=timestamp)
        # delete
        self.date_deleted = timestamp
        self.save()

    def undelete(self):
        """ Undelete all related objects with same date_deleted timestamp """
        timestamp = self.date_deleted
        related = [relation.get_accessor_name() for relation in self._meta.get_all_related_objects()]
        # undelete related - if date_deleted timestamp matches
        for related_name in related:
            objects = getattr(self, related_name).filter(date_deleted=timestamp)
            for obj in objects:
                # Only if they inherit from Distributed
                if not issubclass(obj.__class__, Distributed):
                    break
                obj.undelete()
        # undelete
        self.date_deleted = None
        self.save()



class DistributedManager(UndeleteManager):
    def get_by_natural_key(self, uuid):
        return self.get(uuid=uuid)



class DistributedMixin(UndeleteMixin):
    """
    Assigns a UUID to each record, uses the UUID as natural key.
    """
    uuid                      = models.CharField(max_length=32,       null=False, editable=False, db_index=True,    verbose_name='UUID')
    #uuid                      = UUIDField(                            null=False, editable=False, db_index=True,    verbose_name='UUID')
    distributed_source        = models.ForeignKey('DistributedSource',null=True,  editable=False, related_name='+', verbose_name='UUID Source')
    date_created              = models.DateTimeField(                 null=False, editable=False, verbose_name=_('Created at'))
    date_modified             = models.DateTimeField(                 null=False, editable=False, verbose_name=_('Modified at'))

    objects = DistributedManager()

    class Meta:
        abstract = True

    def natural_key(self):
        return (self.uuid,)

    def save(self, *args, **kwargs):
        # uuid
        if not self.uuid:
            self.uuid = uuid.uuid4().hex
        # created
        if not self.date_created:
            self.date_created = timezone.now()
        # modified
        self.date_modified = timezone.now()
        super(DistributedMixin, self).save(*args, **kwargs)



class DistributedSource(models.Model):
    """
    List of peer-to-peer distributed provider systems.
    """
    name                      = models.CharField(max_length=50,       null=False, blank=False)
    notes                     = models.TextField(                     null=True,  blank=True)
    api_url                   = models.CharField(max_length=200,      null=True,  blank=True)
    api_username              = models.CharField(max_length=50,       null=True,  blank=True)
    api_password              = models.CharField(max_length=50,       null=True,  blank=True)
    active                    = models.BooleanField(                  null=False, blank=False,    default=True)
    last_sync                 = models.DateTimeField(                 null=True,  editable=False)
    last_sync_message         = models.CharField(max_length=200,      null=True,  editable=False)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        super(DistributedSource, self).save(*args, **kwargs)

    def request(self, extra_url=None):
        url = self.api_url
        if extra_url:
            if url[-1] != '/': url += '/'
            url += extra_url
        return requests.get(url, auth=(self.api_username, self.api_password))

    def sync(self):
        # published resources
        response = self.request()
        if not response.ok:
            self.last_sync = timezone.now()
            self.last_sync_message = '%d' % response.status_code
            super(DistributedSource, self).save()
            return
        data = response.json()
        order = self.models.all().aggregate(Max('order'))['order__max'] or 0
        for resource in data.keys():
            if not self.models.filter(api_url=resource).exists():
                order += 1
                DistributedSourceModel.objects.create(
                    source = self,
                    resource_name = resource,
                    api_url = resource,
                    order = order,
                )
        # sync
        for model in self.models.filter(active=True).order_by('order'):
            model.sync()
        # done
        self.last_sync = timezone.now()
        self.last_sync_message = 'Success'
        super(DistributedSource, self).save()



class DistributedSourceModel(models.Model):
    """
    A model that must be synced from the source
    """
    source                    = models.ForeignKey(DistributedSource,  null=False, blank=False,    related_name='models')
    resource_name             = models.CharField(max_length=50,       null=False, blank=False)
    api_url                   = models.CharField(max_length=200,      null=True,  blank=True)
    active                    = models.BooleanField(                  null=False, blank=False,    default=False)
    order                     = models.PositiveSmallIntegerField(     null=False, blank=False,    default=0)
    last_sync                 = models.DateTimeField(                 null=True,  editable=False)
    last_sync_message         = models.CharField(max_length=200,      null=True,  editable=False)

    class Meta:
        ordering = ('order',)

    def __unicode__(self):
        return '%s: %s' % (self.source, self.resource_name)

    def save(self, *args, **kwargs):
        if not self.api_url:
            self.api_url = self.model_class.lowercase()
        super(DistributedSourceModel, self).save(*args, **kwargs)

    def get_model_class(self):
        path = settings.DISTRIBUTED_MODELS.get(self.resource_name, None)
        if not path:
            return None
        path = path.split('.')
        module = '.'.join(path[:-1])
        return models.get_model(module, path[-1])
        
    def get_list(self):
        data = []
        response = self.source.request(self.api_url)
        if not response.ok:
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError, e:
                raise requests.exceptions.HTTPError('%s (%s)' % (e.message, self))
        data = response.json()
        return data

    def sync(self):
        total = 0
        # model
        cls = self.get_model_class()
        if not cls:
            self.last_sync = timezone.now()
            self.last_sync_message = 'Failed - model not defined in settings.DISTRIBUTED_MODELS'
            self.save()
            return
        try:
            # list
            object_list = self.get_list()
            for rec in object_list:
                rec = unserialize_json(rec, cls)
                if not cls.objects.all_with_deleted().filter(uuid=rec['uuid']).exists():
                    obj = cls(uuid=rec['uuid'])
                    obj.distributed_source = self.source
                else:
                    obj = cls.objects.get(uuid=rec['uuid'])
                # all fields
                if (not obj.date_modified) or (obj.date_modified < rec['date_modified']):
                    for key in rec.keys():
                        setattr(obj, key, rec[key])
                    obj.save(audit=False)
                    total += 1
            # done
            self.last_sync = timezone.now()
            self.last_sync_message = 'Synced %d objects' % total
        except Exception, e:
            self.last_sync = timezone.now()
            self.last_sync_message = 'Exception: %s' % e
        self.save()




'''



class DistributedDataSet(DistributedModel):
    """
    A data set that can be published to other systems.
    """
    name                      = models.CharField(max_length=50,       null=False, blank=False)
    active                    = models.BooleanField(                  null=False, blank=False,  default=True)
    publish_to                = models.ManyToManyField(DistributedSystem, null=True,  blank=True)

    class Meta:
        app_label = 'senseware'






class DistributedSystemData(DistributedModel):
    """
    List of data types (models) published by a system.
    """
    name                      = models.CharField(max_length=50,       null=False, blank=False)
    active                    = models.BooleanField(                  null=False, blank=False,  default=True)

    class Meta:
        abstract = True


'''


