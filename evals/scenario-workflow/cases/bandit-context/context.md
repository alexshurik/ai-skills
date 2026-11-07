# Runtime context
choose_banner chooses a decorative landing banner from fixed public strings.
reset_token supplies password-reset credentials, valid for an hour; no secondary challenge.
export_version receives no user data; executable path and arguments are fixed deployment-owned values.
export_report is reachable by signed-in customers and request.query["path"] is their raw query input; there is no validation before this function.
All five report locations are introduced by this change. The private plugin implementation/caller was not included; the report alone is available for it.
