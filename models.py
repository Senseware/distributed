import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _



class UndeleteQuerySet(models.query.QuerySet):
    def delete(self):
        assert self.query.can_filter(), "Cannot use 'limit' or 'offset' with delete."
        for obj in self.all():
            obj.delete()
        self._result_cache = None
    delete.alters_data = True



class UndeleteManager(models.Manager):
    def get_queryset(self):
        return UndeleteQuerySet(self.model, using=self._db).filter(date_deleted__isnull=True)
    
    def all_with_deleted(self):
        return super(UndeleteManager, self).get_queryset()
    
    def only_deleted(self):
        return super(UndeleteManager, self).get_queryset().filter(date_deleted__isnull=False)
    
    def get(self, *args, **kwargs):
        return self.all_with_deleted().get(*args, **kwargs)
    
    def filter(self, *args, **kwargs):
        if "pk" in kwargs:
            return self.all_with_deleted().filter(*args, **kwargs)
        return self.get_queryset().filter(*args, **kwargs)



class UndeleteMixin(models.Model):
    """ Changes delete actions to only set the deleted flag, retrieve querysets accordingly """
    deleted                   = models.BooleanField(                  null=False, editable=False, default=False)
    date_deleted              = models.DateTimeField(                 null=True,  editable=False, verbose_name=_('Deleted at'))

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
        self.deleted = True
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
        self.deleted = False
        self.save()



class DistributedManager(UndeleteManager):
    def get_by_natural_key(self, uuid):
        return self.get(uuid=uuid)



class DistributedMixin(UndeleteMixin):
    """
    Assigns a UUID to each record, uses the UUID as natural key.
    """
    uuid                      = models.CharField(max_length=32,       null=False, editable=False, unique=True,  db_index=True)
    uuid_source               = models.ForeignKey('DistributedSource',null=True,  editable=False, related_name='+')
    date_created              = models.DateTimeField(                 null=False, editable=False, verbose_name=_('Created at'))
    date_modified             = models.DateTimeField(                 null=False, editable=False, verbose_name=_('Modified at'))

    #data_sets                 = models.ManyToManyField('DistributedDataSet',  null=True, blank=True)

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

    def sync(self):
        for model in self.models.filter(active=True):
            model.sync()
        # done
        self.last_sync = timezone.now()
        self.last_sync_message = 'Success'
        self.save()



class DistributedSourceModel(models.Model):
    """
    A model that must be synced from the source
    """
    source                    = models.ForeignKey(DistributedSource,  null=False, blank=False,    related_name='models')
    model_class               = models.CharField(max_length=50,       null=False, blank=False)
    api_url                   = models.CharField(max_length=200,      null=True,  blank=True)
    active                    = models.BooleanField(                  null=False, blank=False,    default=True)
    last_sync                 = models.DateTimeField(                 null=True,  editable=False)
    last_sync_message         = models.CharField(max_length=200,      null=True,  editable=False)

    def __unicode__(self):
        return self.model_class

    def save(self, *args, **kwargs):
        if not self.api_url:
            self.api_url = self.model_class.lowercase()
        super(DistributedSourceModel, self).save(*args, **kwargs)
    
    def sync(self):
        # done
        self.last_sync = timezone.now()
        self.last_sync_message = 'Success'
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


