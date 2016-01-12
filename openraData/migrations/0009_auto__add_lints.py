# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Lints'
        db.create_table(u'openraData_lints', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('map_id', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('version_tag', self.gf('django.db.models.fields.CharField')(default='release-20141029', max_length=100)),
            ('pass_status', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('lint_output', self.gf('django.db.models.fields.CharField')(default='', max_length=100000)),
            ('posted', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'openraData', ['Lints'])


    def backwards(self, orm):
        # Deleting model 'Lints'
        db.delete_table(u'openraData_lints')


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
        u'openraData.lints': {
            'Meta': {'object_name': 'Lints'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lint_output': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '100000'}),
            'map_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'pass_status': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'version_tag': ('django.db.models.fields.CharField', [], {'default': "'release-20141029'", 'max_length': '100'})
        },
        u'openraData.maps': {
            'Meta': {'object_name': 'Maps'},
            'advanced_map': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'amount_reports': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
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
            'mapformat': ('django.db.models.fields.IntegerField', [], {'default': '6'}),
            'next_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'parser': ('django.db.models.fields.CharField', [], {'default': "'release-20141029'", 'max_length': '100'}),
            'players': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'policy_adaptations': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'policy_cc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'policy_commercial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'pre_rev': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'rating': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'requires_upgrade': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'rsync_allow': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'shellmap': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'spawnpoints': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000'}),
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
            'rating': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
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
            'rating': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'used': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'openraData.rating': {
            'Meta': {'object_name': 'Rating'},
            'ex_id': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'ex_name': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'posted': ('django.db.models.fields.DateTimeField', [], {}),
            'rating': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
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
            'rating': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
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
            'rating': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
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