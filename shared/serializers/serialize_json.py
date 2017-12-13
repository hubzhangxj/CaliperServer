# coding=utf-8
from itertools import chain
from django.db.models.fields import DateTimeField
import datetime


def value_from_object(obj,attname):
    """
    Returns the value of this field in the given model instance.
    """
    return getattr(obj, attname)

def model_to_dict(instance, fields=None, exclude=None):
    """
    Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        # if not getattr(f, 'editable', False):
        #     continue
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if isinstance(f,DateTimeField):
            value = f.value_from_object(instance)
            if value is None:
                data[f.name] = ""
            else:
                data[f.name] = value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            data[f.name] = f.value_from_object(instance)
    return data

# def model2dict(instance, fields=None, exclude=['password'],hasMany2Many = False):
#     data = {}
#     for f in instance._meta.fields:
#         if fields and f.name not in fields:
#             continue
#         if exclude and f.name in exclude:
#             continue
#         if f.remote_field is None:
#             if isinstance(f, DateTimeField):
#                 value = f.value_from_object(instance)
#                 if value is None:
#                     data[f.name] = ''
#                 else:
#                     data[f.name] = value.strftime('%Y-%m-%d %H:%M:%S')
#             else:
#                 data[f.name] = value_from_object(instance, f.name)
#         else:
#             related = getattr(instance, f.name)
#             if related is None:
#                 print "none11"
#                 data[f.name] = ''
#             else:
#                 data[f.name] = model_to_dict(related, fields, exclude)
#     if hasMany2Many:
#         for f in instance._meta.many_to_many:
#             values = []
#             for related in getattr(instance, f.name).iterator():
#                 if related is None:
#                     print "none"
#                     values.append({})
#                 else:
#                     values.append(model_to_dict(related, fields, exclude))
#
#             data[f.name] = values
#     else:
#         for f in instance._meta.many_to_many:
#             values = []
#             for related in getattr(instance, f.name).iterator():
#                 values.append(getattr(related, 'id'))
#             data[f.name] = values
#
#     return data

def model2dict(instance, fields=None, exclude=['password']):
    '''
    2层递归
    :param instance:
    :param fields:
    :param exclude:
    :param hasMany2Many:
    :return:
    '''
    data = {}
    for f in instance._meta.fields:
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if f.remote_field is None:
            if isinstance(f, DateTimeField):
                value = f.value_from_object(instance)
                if value is None:
                    data[f.name] = ''
                else:
                    data[f.name] = value.strftime('%Y-%m-%d %H:%M:%S')
            else:
                data[f.name] = value_from_object(instance, f.name)
        else:
            related = getattr(instance, f.name)
            if related is None:
                print "none11"
                data[f.name] = ''
            else:
                data[f.name] = model_to_dict(related, fields, exclude)

    for f in instance._meta.many_to_many:
        values = []
        for related in getattr(instance, f.name).iterator():
            if related is None:
                print "none"
                values.append({})
            else:
                values.append(model_to_dict(related, fields, exclude))

        data[f.name] = values


    return data

def format_datetime(data):
    return datetime.strptime(data,'%Y-%m-%d %H:%M:%S')