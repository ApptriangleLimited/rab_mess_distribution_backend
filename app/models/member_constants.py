"""Member approval workflow constants — see docs/MEMBER_APPROVAL_PLAN.md."""

CREATED_VIA_PUBLIC = "public_register"
CREATED_VIA_CC = "cc_staff"
CREATED_VIA_DAILY = "daily_staff"

APPROVAL_PENDING_CC = "pending_cc"
APPROVAL_PENDING_DAILY = "pending_daily"
APPROVAL_APPROVED = "approved"
APPROVAL_REJECTED = "rejected"
APPROVAL_ENDED = "ended"

# Legacy DB/API value before two-stage workflow.
APPROVAL_LEGACY_PENDING = "pending"

PENDING_APPROVAL_STATUSES = (
    APPROVAL_PENDING_CC,
    APPROVAL_PENDING_DAILY,
    APPROVAL_LEGACY_PENDING,
)
