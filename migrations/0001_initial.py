# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DistributedSource'
        db.create_table(u'distributed_distributedsource', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('api_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('api_username', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('api_password', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_sync', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('last_sync_message', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
        ))
        db.send_create_signal(u'distributed', ['DistributedSource'])

        # Adding model 'DistributedSourceModel'
        db.create_table(u'distributed_distributedsourcemodel', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='models', to=orm['distributed.DistributedSource'])),
            ('resource_name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('api_url', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0)),
            ('last_sync', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('last_sync_message', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
        ))
        db.send_create_signal(u'distributed', ['DistributedSourceModel'])


    def backwards(self, orm):
        # Deleting model 'DistributedSource'
        db.delete_table(u'distributed_distributedsource')

        # Deleting model 'DistributedSourceModel'
        db.delete_table(u'distributed_distributedsourcemodel')


    models = {
        u'distributed.distributedsource': {
            'Meta': {'object_name': 'DistributedSource'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'api_password': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'api_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'api_username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_sync_message': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        u'distributed.distributedsourcemodel': {
            'Meta': {'ordering': "('order',)", 'object_name': 'DistributedSourceModel'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'api_url': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sync': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'last_sync_message': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'resource_name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'models'", 'to': u"orm['distributed.DistributedSource']"})
        }
    }

    complete_apps = ['distributed']