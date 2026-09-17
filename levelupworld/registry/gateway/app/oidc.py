"""OIDC / IdP configuration for production gateway auth.

Environment:
  AUTH_MODE=disabled|dev|oidc
  OIDC_ISSUER          — expected iss claim (required in oidc)
  OIDC_AUDIENCE        — expected aud claim (required in oidc)
  OIDC_JWKS_URL        — JWKS endpoint (required in oidc)
  OIDC_ORG_CLAIM       — claim path for org_id (default: org_id)
  OIDC_TENANT_CLAIM    — claim path for tenant (default: tenant_id)
  OIDC_ROLES_CLAIM     — claim path for roles (default: roles)
  OIDC_JWKS_CACHE_TTL  — seconds (default: 300)
"""

from __future__ import annotations

import os
import time
from typing import Any

import jwt
from fastapi import HTTPException, Request

from .auth import Principal


def _claim_path(claims: dict[str, Any], path: str) -> Any:
    cur: Any = claims
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class OidcValidator:
    """Production OIDC JWT validation with JWKS caching."""

    def __init__(self):
        self.issuer = os.environ.get("OIDC_ISSUER", "")
        self.audience = os.environ.get("OIDC_AUDIENCE", "mcp-gateway")
        self.jwks_url = os.environ.get("OIDC_JWKS_URL", "")
        self.org_claim = os.environ.get("OIDC_ORG_CLAIM", "org_id")
        self.tenant_claim = os.environ.get("OIDC_TENANT_CLAIM", "tenant_id")
        self.roles_claim = os.environ.get("OIDC_ROLES_CLAIM", "roles")
        self.cache_ttl = int(os.environ.get("OIDC_JWKS_CACHE_TTL", "300"))
        self._jwks_client: Any = None
        self._jwks_loaded_at = 0.0

    def validate_config(self) -> None:
        missing = []
        if not self.issuer:
            missing.append("OIDC_ISSUER")
        if not self.jwks_url:
            missing.append("OIDC_JWKS_URL")
        if not self.audience:
            missing.append("OIDC_AUDIENCE")
        if missing:
            raise RuntimeError(f"AUTH_MODE=oidc requires {', '.join(missing)}")

    def _client(self):
        now = time.time()
        if self._jwks_client is None or (now - self._jwks_loaded_at) > self.cache_ttl:
            self._jwks_client = jwt.PyJWKClient(self.jwks_url, cache_keys=True)
            self._jwks_loaded_at = now
        return self._jwks_client

    def authenticate(self, request: Request) -> Principal:
        self.validate_config()
        auth = request.headers.get("Authorization", "")
        if not auth.lower().startswith("bearer "):
            raise HTTPException(401, "missing bearer token")
        token = auth.split(" ", 1)[1].strip()
        try:
            key = self._client().get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256", "ES256", "PS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(401, f"invalid oidc token: {exc}") from exc

        roles_raw = _claim_path(claims, self.roles_claim)
        if roles_raw is None:
            roles_raw = claims.get("realm_access", {}).get("roles") or ["viewer"]
        if isinstance(roles_raw, str):
            roles = [roles_raw]
        else:
            roles = [str(r) for r in roles_raw]

        org_id = _claim_path(claims, self.org_claim) or claims.get("org") or request.headers.get("X-Org-ID")
        if not org_id:
            raise HTTPException(401, f"token missing org claim ({self.org_claim})")
        # Never trust client-supplied org override when claim present
        header_org = request.headers.get("X-Org-ID")
        if header_org and str(header_org) != str(org_id):
            raise HTTPException(401, "X-Org-ID does not match token org claim")

        tenant = _claim_path(claims, self.tenant_claim) or claims.get("tenant") or "tenant_default"
        return Principal(
            subject=str(claims.get("sub")),
            org_id=str(org_id),
            tenant_id=str(tenant),
            roles=roles,
            email=claims.get("email"),
            raw_claims=claims,
        )

    def public_config(self) -> dict[str, Any]:
        return {
            "mode": "oidc",
            "issuer": self.issuer or None,
            "audience": self.audience,
            "jwks_url_configured": bool(self.jwks_url),
            "org_claim": self.org_claim,
            "tenant_claim": self.tenant_claim,
            "roles_claim": self.roles_claim,
            "jwks_cache_ttl_seconds": self.cache_ttl,
        }
