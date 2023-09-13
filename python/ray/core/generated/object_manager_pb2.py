# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: src/ray/protobuf/object_manager.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from . import common_pb2 as src_dot_ray_dot_protobuf_dot_common__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%src/ray/protobuf/object_manager.proto\x12\x07ray.rpc\x1a\x1dsrc/ray/protobuf/common.proto\"\xb8\x01\n\x0bPushRequest\x12\x0f\n\x07push_id\x18\x01 \x01(\x0c\x12\x11\n\tobject_id\x18\x02 \x01(\x0c\x12\x0f\n\x07node_id\x18\x03 \x01(\x0c\x12\'\n\rowner_address\x18\x04 \x01(\x0b\x32\x10.ray.rpc.Address\x12\x13\n\x0b\x63hunk_index\x18\x05 \x01(\r\x12\x11\n\tdata_size\x18\x06 \x01(\x04\x12\x15\n\rmetadata_size\x18\x07 \x01(\x04\x12\x0c\n\x04\x64\x61ta\x18\x08 \x01(\x0c\"1\n\x0bPullRequest\x12\x0f\n\x07node_id\x18\x01 \x01(\x0c\x12\x11\n\tobject_id\x18\x02 \x01(\x0c\"(\n\x12\x46reeObjectsRequest\x12\x12\n\nobject_ids\x18\x01 \x03(\x0c\"\x0b\n\tPushReply\"\x0b\n\tPullReply\"\x12\n\x10\x46reeObjectsReply2\xc1\x01\n\x14ObjectManagerService\x12\x30\n\x04Push\x12\x14.ray.rpc.PushRequest\x1a\x12.ray.rpc.PushReply\x12\x30\n\x04Pull\x12\x14.ray.rpc.PullRequest\x1a\x12.ray.rpc.PullReply\x12\x45\n\x0b\x46reeObjects\x12\x1b.ray.rpc.FreeObjectsRequest\x1a\x19.ray.rpc.FreeObjectsReplyB\x03\xf8\x01\x01\x62\x06proto3')



_PUSHREQUEST = DESCRIPTOR.message_types_by_name['PushRequest']
_PULLREQUEST = DESCRIPTOR.message_types_by_name['PullRequest']
_FREEOBJECTSREQUEST = DESCRIPTOR.message_types_by_name['FreeObjectsRequest']
_PUSHREPLY = DESCRIPTOR.message_types_by_name['PushReply']
_PULLREPLY = DESCRIPTOR.message_types_by_name['PullReply']
_FREEOBJECTSREPLY = DESCRIPTOR.message_types_by_name['FreeObjectsReply']
PushRequest = _reflection.GeneratedProtocolMessageType('PushRequest', (_message.Message,), {
  'DESCRIPTOR' : _PUSHREQUEST,
  '__module__' : 'src.ray.protobuf.object_manager_pb2'
  # @@protoc_insertion_point(class_scope:ray.rpc.PushRequest)
  })
_sym_db.RegisterMessage(PushRequest)

PullRequest = _reflection.GeneratedProtocolMessageType('PullRequest', (_message.Message,), {
  'DESCRIPTOR' : _PULLREQUEST,
  '__module__' : 'src.ray.protobuf.object_manager_pb2'
  # @@protoc_insertion_point(class_scope:ray.rpc.PullRequest)
  })
_sym_db.RegisterMessage(PullRequest)

FreeObjectsRequest = _reflection.GeneratedProtocolMessageType('FreeObjectsRequest', (_message.Message,), {
  'DESCRIPTOR' : _FREEOBJECTSREQUEST,
  '__module__' : 'src.ray.protobuf.object_manager_pb2'
  # @@protoc_insertion_point(class_scope:ray.rpc.FreeObjectsRequest)
  })
_sym_db.RegisterMessage(FreeObjectsRequest)

PushReply = _reflection.GeneratedProtocolMessageType('PushReply', (_message.Message,), {
  'DESCRIPTOR' : _PUSHREPLY,
  '__module__' : 'src.ray.protobuf.object_manager_pb2'
  # @@protoc_insertion_point(class_scope:ray.rpc.PushReply)
  })
_sym_db.RegisterMessage(PushReply)

PullReply = _reflection.GeneratedProtocolMessageType('PullReply', (_message.Message,), {
  'DESCRIPTOR' : _PULLREPLY,
  '__module__' : 'src.ray.protobuf.object_manager_pb2'
  # @@protoc_insertion_point(class_scope:ray.rpc.PullReply)
  })
_sym_db.RegisterMessage(PullReply)

FreeObjectsReply = _reflection.GeneratedProtocolMessageType('FreeObjectsReply', (_message.Message,), {
  'DESCRIPTOR' : _FREEOBJECTSREPLY,
  '__module__' : 'src.ray.protobuf.object_manager_pb2'
  # @@protoc_insertion_point(class_scope:ray.rpc.FreeObjectsReply)
  })
_sym_db.RegisterMessage(FreeObjectsReply)

_OBJECTMANAGERSERVICE = DESCRIPTOR.services_by_name['ObjectManagerService']
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  DESCRIPTOR._serialized_options = b'\370\001\001'
  _PUSHREQUEST._serialized_start=82
  _PUSHREQUEST._serialized_end=266
  _PULLREQUEST._serialized_start=268
  _PULLREQUEST._serialized_end=317
  _FREEOBJECTSREQUEST._serialized_start=319
  _FREEOBJECTSREQUEST._serialized_end=359
  _PUSHREPLY._serialized_start=361
  _PUSHREPLY._serialized_end=372
  _PULLREPLY._serialized_start=374
  _PULLREPLY._serialized_end=385
  _FREEOBJECTSREPLY._serialized_start=387
  _FREEOBJECTSREPLY._serialized_end=405
  _OBJECTMANAGERSERVICE._serialized_start=408
  _OBJECTMANAGERSERVICE._serialized_end=601
# @@protoc_insertion_point(module_scope)
