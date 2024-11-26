# coding: utf-8

# flake8: noqa
"""
    Skyflow Data API

    # Data API  This API inserts, retrieves, and otherwise manages data in a vault.  The Data API is available from two base URIs. *identifier* is the identifier in your vault's URL.<ul><li><b>Sandbox:</b> https://*identifier*.vault.skyflowapis-preview.com</li><li><b>Production:</b> https://*identifier*.vault.skyflowapis.com</li></ul>  When you make an API call, you need to add a header: <table><tr><th>Header</th><th>Value</th><th>Example</th></tr><tr><td>Authorization</td><td>A Bearer Token. See <a href='/api-authentication/'>API Authentication</a>.</td><td><code>Authorization: Bearer eyJhbGciOiJSUzI...1NiIsJdfPA</code></td></tr><table/>

    The version of the OpenAPI document: v1
    Contact: support@skyflow.com
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


# import models into model package
from skyflow.generated.rest.models.audit_event_audit_resource_type import AuditEventAuditResourceType
from skyflow.generated.rest.models.audit_event_context import AuditEventContext
from skyflow.generated.rest.models.audit_event_data import AuditEventData
from skyflow.generated.rest.models.audit_event_http_info import AuditEventHTTPInfo
from skyflow.generated.rest.models.batch_record_method import BatchRecordMethod
from skyflow.generated.rest.models.context_access_type import ContextAccessType
from skyflow.generated.rest.models.context_auth_mode import ContextAuthMode
from skyflow.generated.rest.models.detokenize_record_response_value_type import DetokenizeRecordResponseValueType
from skyflow.generated.rest.models.googlerpc_status import GooglerpcStatus
from skyflow.generated.rest.models.protobuf_any import ProtobufAny
from skyflow.generated.rest.models.query_service_execute_query_body import QueryServiceExecuteQueryBody
from skyflow.generated.rest.models.record_service_batch_operation_body import RecordServiceBatchOperationBody
from skyflow.generated.rest.models.record_service_bulk_delete_record_body import RecordServiceBulkDeleteRecordBody
from skyflow.generated.rest.models.record_service_insert_record_body import RecordServiceInsertRecordBody
from skyflow.generated.rest.models.record_service_update_record_body import RecordServiceUpdateRecordBody
from skyflow.generated.rest.models.redaction_enum_redaction import RedactionEnumREDACTION
from skyflow.generated.rest.models.request_action_type import RequestActionType
from skyflow.generated.rest.models.v1_audit_after_options import V1AuditAfterOptions
from skyflow.generated.rest.models.v1_audit_event_response import V1AuditEventResponse
from skyflow.generated.rest.models.v1_audit_response import V1AuditResponse
from skyflow.generated.rest.models.v1_audit_response_event import V1AuditResponseEvent
from skyflow.generated.rest.models.v1_audit_response_event_request import V1AuditResponseEventRequest
from skyflow.generated.rest.models.v1_bin_list_request import V1BINListRequest
from skyflow.generated.rest.models.v1_bin_list_response import V1BINListResponse
from skyflow.generated.rest.models.v1_byot import V1BYOT
from skyflow.generated.rest.models.v1_batch_operation_response import V1BatchOperationResponse
from skyflow.generated.rest.models.v1_batch_record import V1BatchRecord
from skyflow.generated.rest.models.v1_bulk_delete_record_response import V1BulkDeleteRecordResponse
from skyflow.generated.rest.models.v1_bulk_get_record_response import V1BulkGetRecordResponse
from skyflow.generated.rest.models.v1_card import V1Card
from skyflow.generated.rest.models.v1_delete_file_response import V1DeleteFileResponse
from skyflow.generated.rest.models.v1_delete_record_response import V1DeleteRecordResponse
from skyflow.generated.rest.models.v1_detokenize_payload import V1DetokenizePayload
from skyflow.generated.rest.models.v1_detokenize_record_request import V1DetokenizeRecordRequest
from skyflow.generated.rest.models.v1_detokenize_record_response import V1DetokenizeRecordResponse
from skyflow.generated.rest.models.v1_detokenize_response import V1DetokenizeResponse
from skyflow.generated.rest.models.v1_field_records import V1FieldRecords
from skyflow.generated.rest.models.v1_file_av_scan_status import V1FileAVScanStatus
from skyflow.generated.rest.models.v1_get_file_scan_status_response import V1GetFileScanStatusResponse
from skyflow.generated.rest.models.v1_get_query_response import V1GetQueryResponse
from skyflow.generated.rest.models.v1_insert_record_response import V1InsertRecordResponse
from skyflow.generated.rest.models.v1_member_type import V1MemberType
from skyflow.generated.rest.models.v1_record_meta_properties import V1RecordMetaProperties
from skyflow.generated.rest.models.v1_tokenize_payload import V1TokenizePayload
from skyflow.generated.rest.models.v1_tokenize_record_request import V1TokenizeRecordRequest
from skyflow.generated.rest.models.v1_tokenize_record_response import V1TokenizeRecordResponse
from skyflow.generated.rest.models.v1_tokenize_response import V1TokenizeResponse
from skyflow.generated.rest.models.v1_update_record_response import V1UpdateRecordResponse
from skyflow.generated.rest.models.v1_vault_field_mapping import V1VaultFieldMapping
from skyflow.generated.rest.models.v1_vault_schema_config import V1VaultSchemaConfig

from skyflow.generated.rest.models.v1_get_auth_token_request import V1GetAuthTokenRequest
from skyflow.generated.rest.models.v1_get_auth_token_response import V1GetAuthTokenResponse