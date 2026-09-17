"""Identity provider + request principal for the registry gateway.

Modes:
  AUTH_MODE=disabled  — tests / local demo (default principal)
  AUTH_MODE=dev       — accept HS256 bearer JWT or trusted X-* headers
  AUTH_MODE=oidc      — validate JWT against OIDC_JWKS_URL / OIDC_ISSUER (production)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request


@dataclass
class Principal:
    subject: str
    org_id: str
    tenant_id: str
    roles: list[str] = field(default_factory=list)
    email: str | None = None
    raw_claims: dict[str, Any] = field(default_factory=dict)

    def has_role(self, *needed: str) -> bool:
        return any(r in self.roles for r in needed) or "admin" in self.roles


class IdentityProvider:
    def __init__(self):
        self.mode = os.environ.get("AUTH_MODE", "disabled").lower()
        self.signing_secret = os.environ.get(
            "GATEWAY_SIGNING_SECRET", "dev-only-change-me-agent-ops-gateway"
        )
        self.issuer = os.environ.get("OIDC_ISSUER", "agent-ops-gateway")
        self.audience = os.environ.get("OIDC_AUDIENCE", "mcp-gateway")
        self.jwks_url = os.environ.get("OIDC_JWKS_URL")
        self._oidc = None
        if self.mode == "oidc":
            from .oidc import OidcValidator

            self._oidc = OidcValidator()
            # Fail fast on misconfiguration at startup when explicitly oidc
            try:
                self._oidc.validate_config()
            except RuntimeError:
                # Allow import in docs/tests that set mode later; authenticate() re-validates
                pass

    def issue_dev_token(
        self,
        *,
        subject: str,
        org_id: str,
        tenant_id: str,
        roles: list[str],
        email: str | None = None,
        ttl_seconds: int = 3600,
    ) -> str:
        import time

        now = int(time.time())
        claims = {
            "sub": subject,
            "org_id": org_id,
            "tenant_id": tenant_id,
            "roles": roles,
            "email": email,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": now + ttl_seconds,
        }
        return jwt.encode(claims, self.signing_secret, algorithm="HS256")

    def authenticate(self, request: Request) -> Principal:
        if self.mode == "disabled":
            return Principal(
                subject=request.headers.get("X-Actor", "user:local-dev"),
                org_id=request.headers.get("X-Org-ID", "org_local"),
                tenant_id=request.headers.get("X-Tenant-ID", "tenant_local"),
                roles=["admin", "approver", "operator", "viewer"],
                email="dev@localhost",
            )

        if self.mode == "oidc":
            if self._oidc is None:
                from .oidc import OidcValidator

                self._oidc = OidcValidator()
            return self._oidc.authenticate(request)

        auth = request.headers.get("Authorization", "")
        token = None
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()

        if not token and self.mode == "dev":
            if request.headers.get("X-Actor") and request.headers.get("X-Org-ID"):
                roles = [r.strip() for r in request.headers.get("X-Roles", "viewer").split(",") if r.strip()]
                return Principal(
                    subject=request.headers["X-Actor"],
                    org_id=request.headers["X-Org-ID"],
                    tenant_id=request.headers.get("X-Tenant-ID", "tenant_local"),
                    roles=roles or ["viewer"],
                    email=request.headers.get("X-Email"),
                )

        if not token:
            raise HTTPException(401, "missing bearer token")

        try:
            claims = jwt.decode(
                token,
                self.signing_secret,
                algorithms=["HS256"],
                audience=self.audience,
                issuer=self.issuer,
            )
        except jwt.PyJWTError as exc:
            raise HTTPException(401, f"invalid token: {exc}") from exc

        roles = claims.get("roles") or claims.get("realm_access", {}).get("roles") or ["viewer"]
        if isinstance(roles, str):
            roles = [roles]
        org_id = claims.get("org_id") or claims.get("org") or request.headers.get("X-Org-ID")
        if not org_id:
            raise HTTPException(401, "token missing org_id")
        return Principal(
            subject=str(claims.get("sub")),
            org_id=str(org_id),
            tenant_id=str(claims.get("tenant_id") or claims.get("tenant") or "tenant_default"),
            roles=[str(r) for r in roles],
            email=claims.get("email"),
            raw_claims=claims,
        )

    def public_config(self) -> dict[str, Any]:
        if self.mode == "oidc" and self._oidc is not None:
            return self._oidc.public_config()
        return {
            "mode": self.mode,
            "issuer": self.issuer,
            "audience": self.audience,
            "jwks_url_configured": bool(self.jwks_url),
            "dev_token_endpoint": "/api/v1/auth/dev-token" if self.mode in {"disabled", "dev"} else None,
        }


idp = IdentityProvider()


def get_principal(request: Request) -> Principal:
    return idp.authenticate(request)


def require_roles(*roles: str):
    def _dep(principal: Principal = Depends(get_principal)) -> Principal:
        if not principal.has_role(*roles):
            raise HTTPException(403, f"requires one of roles: {', '.join(roles)}")
        return principal

    return _dep
