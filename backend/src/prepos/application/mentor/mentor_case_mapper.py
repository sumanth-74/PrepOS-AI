from __future__ import annotations

from prepos.application.mentor.mentor_dto import MentorCaseNoteResponse, MentorCaseResponse
from prepos.domain.mentor.case_management_v1 import MentorCase, MentorCaseNote


def map_case_note(note: MentorCaseNote) -> MentorCaseNoteResponse:
    return MentorCaseNoteResponse(
        note_id=note.id,
        mentor_id=note.mentor_id,
        note=note.note,
        created_at=note.created_at,
    )


def map_case_response(
    case: MentorCase,
    *,
    notes: tuple[MentorCaseNote, ...] = (),
) -> MentorCaseResponse:
    return MentorCaseResponse(
        case_id=case.case_id,
        student_id=case.student_id,
        exam_id=case.exam_id,
        status=case.status.value,
        priority=case.priority.value,
        mentor_action_type=case.mentor_action_type.value,
        escalation_level=case.escalation_level.value,
        mentor_action_priority=case.mentor_action_priority,
        opened_at=case.opened_at,
        resolved_at=case.resolved_at,
        resolution_reason=(
            case.resolution_reason.value if case.resolution_reason is not None else None
        ),
        notes=[map_case_note(note) for note in notes],
    )
