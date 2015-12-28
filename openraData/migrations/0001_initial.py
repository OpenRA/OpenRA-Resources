# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UserOptions'
        db.create_table(u'openraData_useroptions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('notifications_email', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('notifications_site', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'openraData', ['UserOptions'])

        # Adding model 'NotifyOfComments'
        db.create_table(u'openraData_notifyofcomments', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('object_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('object_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'openraData', ['NotifyOfComments'])

        # Adding model 'ReadComments'
        db.create_table(u'openraData_readcomments', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('object_type', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('object_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('comment_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('ifread', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'openraData', ['ReadComments'])

        # Adding model 'Maps'
        db.create_table(u'openraData_maps', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=4000)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=4000)),
            ('author', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('map_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('players', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('game_mod', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('map_hash', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('width', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('height', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('bounds', self.gf('django.db.models.fields.CharField')(default='', max_length=50)),
            ('tileset', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('spawnpoints', self.gf('django.db.models.fields.CharField')(default='', max_length=200)),
            ('legacy_map', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('pre_rev', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('next_rev', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('downloading', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('requires_upgrade', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('advanced_map', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('lua', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
            ('viewed', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('downloaded', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('policy_cc', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('policy_adaptations', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('policy_commercial', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rating_votes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('rating_score', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal(u'openraData', ['Maps'])

        # Adding model 'Units'
        db.create_table(u'openraData_units', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('unit_type', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('category', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('palette', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('pre_rev', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('next_rev', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
            ('viewed', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('downloaded', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('policy_cc', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('policy_adaptations', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('policy_commercial', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rating_votes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('rating_score', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal(u'openraData', ['Units'])

        # Adding model 'Mods'
        db.create_table(u'openraData_mods', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('pre_rev', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('next_rev', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
            ('viewed', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('downloaded', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('policy_cc', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('policy_adaptations', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('policy_commercial', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('rating_votes', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('rating_score', self.gf('django.db.models.fields.IntegerField')(default=0, blank=True)),
        ))
        db.send_create_signal(u'openraData', ['Mods'])

        # Adding model 'Replays'
        db.create_table(u'openraData_replays', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=2000)),
            ('version', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
            ('viewed', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('downloaded', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'openraData', ['Replays'])

        # Adding model 'Palettes'
        db.create_table(u'openraData_palettes', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('info', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('used', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'openraData', ['Palettes'])

        # Adding model 'Reports'
        db.create_table(u'openraData_reports', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('reason', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('ex_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('ex_name', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('infringement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'openraData', ['Reports'])

        # Adding model 'Screenshots'
        db.create_table(u'openraData_screenshots', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('ex_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('ex_name', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
            ('map_preview', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'openraData', ['Screenshots'])

        # Adding model 'CrashReports'
        db.create_table(u'openraData_crashreports', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('gameID', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('isdesync', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('gistID', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal(u'openraData', ['CrashReports'])


    def backwards(self, orm):
        # Deleting model 'UserOptions'
        db.delete_table(u'openraData_useroptions')

        # Deleting model 'NotifyOfComments'
        db.delete_table(u'openraData_notifyofcomments')

        # Deleting model 'ReadComments'
        db.delete_table(u'openraData_readcomments')

        # Deleting model 'Maps'
        db.delete_table(u'openraData_maps')

        # Deleting model 'Units'
        db.delete_table(u'openraData_units')

        # Deleting model 'Mods'
        db.delete_table(u'openraData_mods')

        # Deleting model 'Replays'
        db.delete_table(u'openraData_replays')

        # Deleting model 'Palettes'
        db.delete_table(u'openraData_palettes')

        # Deleting model 'Reports'
        db.delete_table(u'openraData_reports')

        # Deleting model 'Screenshots'
        db.delete_table(u'openraData_screenshots')

        # Deleting model 'CrashReports'
        db.delete_table(u'openraData_crashreports')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'openraData.crashreports': {
            'Meta': {'object_name': 'CrashReports'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'gameID': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'gistID': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isdesync': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'openraData.maps': {
            'Meta': {'object_name': 'Maps'},
            'advanced_map': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'author': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'bounds': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '50'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'downloaded': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'downloading': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'game_mod': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'height': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '4000'}),
            'legacy_map': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'lua': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'map_hash': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'map_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'next_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'players': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'policy_adaptations': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'policy_cc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'policy_commercial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'pre_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'rating_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'rating_votes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'requires_upgrade': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'spawnpoints': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '200'}),
            'tileset': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'viewed': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'width': ('django.db.models.fields.CharField', [], {'max_length': '16'})
        },
        u'openraData.mods': {
            'Meta': {'object_name': 'Mods'},
            'downloaded': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'next_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'policy_adaptations': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'policy_cc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'policy_commercial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'pre_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'rating_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'rating_votes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'viewed': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'openraData.notifyofcomments': {
            'Meta': {'object_name': 'NotifyOfComments'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'object_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'openraData.palettes': {
            'Meta': {'object_name': 'Palettes'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'used': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'openraData.readcomments': {
            'Meta': {'object_name': 'ReadComments'},
            'comment_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ifread': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'object_type': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'openraData.replays': {
            'Meta': {'object_name': 'Replays'},
            'downloaded': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '2000'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'viewed': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'openraData.reports': {
            'Meta': {'object_name': 'Reports'},
            'ex_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ex_name': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'infringement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'reason': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'openraData.screenshots': {
            'Meta': {'object_name': 'Screenshots'},
            'ex_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ex_name': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'map_preview': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'openraData.units': {
            'Meta': {'object_name': 'Units'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'downloaded': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'next_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'palette': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'policy_adaptations': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'policy_cc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'policy_commercial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'pre_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'rating_score': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'rating_votes': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'unit_type': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'viewed': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        u'openraData.useroptions': {
            'Meta': {'object_name': 'UserOptions'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notifications_email': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'notifications_site': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['openraData']