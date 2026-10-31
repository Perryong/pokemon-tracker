#!/bin/sh
# Direct container starts must not bypass the PowerShell launch gate.
echo 'Live coordinator startup disabled until the credential-isolated broker is integrated and verified. See SECURITY-BROKER.md.' >&2
exit 78
