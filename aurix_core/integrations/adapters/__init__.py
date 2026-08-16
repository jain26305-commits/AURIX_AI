"""Universal integration adapter registry exports for Phase 12."""

from aurix_core.integrations.adapters.erp_odoo import OdooErpConnector
from aurix_core.integrations.adapters.generic_rest import GenericRestConnector
from aurix_core.integrations.adapters.generic_sftp import GenericSftpConnector
from aurix_core.integrations.adapters.generic_webhook import GenericWebhookAdapter
from aurix_core.integrations.adapters.test_mock import MockIntegrationConnector
from aurix_core.integrations.adapters.wms_generic import GenericWmsConnector

__all__ = [
    "GenericRestConnector",
    "GenericWebhookAdapter",
    "GenericSftpConnector",
    "OdooErpConnector",
    "GenericWmsConnector",
    "MockIntegrationConnector",
]