from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, timezone
from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.models.entities import TransferAuditLog

class PrivacyGateway:
    """
    Central Privacy Controller & Model Router.
    Enforces Strict Local, Private Hybrid, and Cloud Assisted governance.
    Every remote cloud transfer request must be vetted against active policy,
    global kill-switch, and logged to the transfer audit log.
    """
    def __init__(self):
        self.privacy_mode: str = settings.PRIVACY_MODE
        self.allow_cloud_transfers: bool = settings.ALLOW_CLOUD_TRANSFERS
        self.allowlist: List[str] = list(settings.CLOUD_PROVIDER_ALLOWLIST)

    def update_settings(
        self,
        privacy_mode: Optional[str] = None,
        allow_cloud_transfers: Optional[bool] = None,
        allowlist: Optional[List[str]] = None
    ):
        if privacy_mode in ("strict_local", "private_hybrid", "cloud_assisted"):
            self.privacy_mode = privacy_mode
        if allow_cloud_transfers is not None:
            self.allow_cloud_transfers = allow_cloud_transfers
        if allowlist is not None:
            self.allowlist = [item.lower().strip() for item in allowlist]
        logger.info(f"Privacy gateway updated: mode={self.privacy_mode}, cloud_allowed={self.allow_cloud_transfers}")

    def get_status(self) -> Dict[str, Any]:
        return {
            "privacy_mode": self.privacy_mode,
            "allow_cloud_transfers": self.allow_cloud_transfers,
            "allowlist": self.allowlist,
            "is_strict_local": self.privacy_mode == "strict_local",
            "offline_mode": not self.allow_cloud_transfers or self.privacy_mode == "strict_local"
        }

    def can_transfer_to_cloud(
        self,
        provider_name: str,
        task_type: str,
        payload_summary: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Evaluate whether an outbound request to a cloud AI provider is authorized.
        Logs every evaluation into the TransferAuditLog entity.
        """
        provider_key = provider_name.lower().strip()

        # Local providers always bypass cloud restrictions
        if provider_key in ("mock", "ollama", "edge_tts", "local_whisper", "local", "deterministic"):
            return True, "Local execution authorized (Zero cloud transfer)"

        status = "blocked"
        reason = ""

        if self.privacy_mode == "strict_local":
            reason = "Blocked: Strict Local privacy tier prohibits external cloud calls."
        elif not self.allow_cloud_transfers:
            reason = "Blocked: Global cloud transfer switch is disabled."
        elif provider_key not in [a.lower() for a in self.allowlist]:
            reason = f"Blocked: Provider '{provider_name}' is not in cloud allowlist."
        else:
            status = "allowed"
            reason = f"Authorized cloud transfer to {provider_name} under {self.privacy_mode} mode."

        is_allowed = (status == "allowed")

        # Audit log persistence
        try:
            with SessionLocal() as session:
                log_entry = TransferAuditLog(
                    provider=provider_name,
                    request_type=task_type,
                    payload_preview=payload_summary[:500] if payload_summary else None,
                    allowed=is_allowed,
                    is_cloud=(provider_key not in ("mock", "ollama", "edge_tts", "local_whisper")),
                    privacy_mode=self.privacy_mode
                )
                session.add(log_entry)
                session.commit()
        except Exception as e:
            logger.warning(f"Failed to record transfer audit log: {e}")

        if not is_allowed:
            logger.warning(f"[PRIVACY GATEWAY] Denied cloud transfer to {provider_name} ({task_type}): {reason}")
        else:
            logger.info(f"[PRIVACY GATEWAY] Permitted cloud transfer to {provider_name} ({task_type})")

        return is_allowed, reason

privacy_gateway = PrivacyGateway()
