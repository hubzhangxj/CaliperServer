#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

from StringIO import StringIO

from django.core.serializers.base import Serializer as PythonSerializer
from django.db.models.fields import FieldDoesNotExist


class Serializer(PythonSerializer):
    """
       Abstract serializer base class.
       """

    # Indicates if the implemented serializer is only available for
    # internal Django use.

    def serialize(self, queryset, **options):
        """
        Serialize a queryset.
        """
        self.options = options

        self.stream = options.pop("stream", self.stream_class())
        self.selected_fields = options.pop("fields", None)
        self.excluded_fields = options.pop("excluded", None)
        self.use_recursion = options.pop("use_recursion", False)
        self.use_natural_foreign_keys = options.pop('use_natural_foreign_keys', False)
        self.use_natural_primary_keys = options.pop('use_natural_primary_keys', False)
        progress_bar = self.progress_class(
            options.pop('progress_output', None), options.pop('object_count', 0)
        )

        self.start_serialization()
        self.first = True
        for count, obj in enumerate(queryset, start=1):
            self.start_object(obj)
            # Use the concrete parent class' _meta instead of the object's _meta
            # This is to avoid local_fields problems for proxy models. Refs #17717.
            for field in obj._meta.fields:
                # if field.serialize:
                if field.remote_field is None:
                    if self.selected_fields is None or field.attname in self.selected_fields:
                        self.handle_field(obj, field)
                else:
                    if self.selected_fields is None or field.attname[:-3] in self.selected_fields:
                        self.handle_fk_field(obj, field)
            for field in obj._meta.many_to_many:
                # if field.serialize:
                if self.selected_fields is None or field.attname in self.selected_fields:
                    self.handle_m2m_field(obj, field)
            self.end_object(obj)
            progress_bar.update(count)
            if self.first:
                self.first = False
        self.end_serialization()
        return self.getvalue()
