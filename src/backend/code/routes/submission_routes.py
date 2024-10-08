import logging

from flask import Blueprint, jsonify, url_for, request
from flask_hal import document, link

from code import User
from code.extensions import db
from code.models.submissions import Submission
from code.utils.auth import token_required

bp = Blueprint("submission_routes", __name__)
log = logging.getLogger("code")


@bp.route("/api/submissions", methods=["GET"])
def get_submissions():
    submissions = Submission.query.all()
    submission_collection = [
        document.Document(
            data={
                "id": submission.id,
                "program_lang": submission.program_lang,
                "linked_user": submission.linked_user,
                "problem_id": submission.problem_id,
                "status": submission.status,
                "result": submission.result,
                "result_time_ms": submission.result_time_ms,
                "result_memory_kb": submission.result_memory_kb,
            },
            links=link.Collection(
                link.Link("collection", href=url_for("submission_routes.get_submissions")),
            ),
        ).to_dict()
        for submission in submissions
    ]

    response = document.Document(
        data={"submissions": submission_collection},
        links=link.Collection(),
    )
    return jsonify(response.to_dict())


@bp.route("/api/submissions/<int:submission_id>", methods=["GET"])
def get_submission(submission_id):
    submission = db.session.get(Submission, submission_id)

    if not submission:
        return jsonify({"error": f"Submission {submission_id} not found"}), 404

    response = document.Document(
        data={
            "id": submission.id,
            "program_lang": submission.program_lang,
            "linked_user": submission.linked_user,
            "problem_id": submission.problem_id,
            "status": submission.status,
            "result": submission.result,
            "result_time_ms": submission.result_time_ms,
            "result_memory_kb": submission.result_memory_kb,
            "code": submission.code,
            "output_text": submission.output_text,
            "error_text": submission.error_text,
        },
        links=link.Collection(
            link.Link("collection", href=url_for("submission_routes.get_submissions")),
        ),
    )

    return jsonify(response.to_dict())


@bp.route("/api/users/<string:username>/problems/<int:problem_id>/submissions", methods=["GET"])
def get_user_submissions_for_problem(username, problem_id):
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": f"User {username} not found"}), 404

    submissions = Submission.query.filter_by(linked_user=user.id, problem_id=problem_id).all()
    submission_collection = [
        document.Document(
            data={
                "id": submission.id,
                "program_lang": submission.program_lang,
                "linked_user": submission.linked_user,
                "problem_id": submission.problem_id,
                "status": submission.status,
                "result": submission.result,
                "result_time_ms": submission.result_time_ms,
                "result_memory_kb": submission.result_memory_kb,
                "submission_time": submission.created,
            },
            links=link.Collection(
                link.Link("collection",
                          href=url_for("submission_routes.get_user_submissions_for_problem", username=username,
                                       problem_id=problem_id)),
            ),
        ).to_dict()
        for submission in submissions
    ]

    response = document.Document(
        data={"submissions": submission_collection},
        links=link.Collection(),
    )
    return jsonify(response.to_dict())


@bp.route("/api/create_submission", methods=["POST"])
@token_required
def create_submission(current_user):
    data = request.get_json()

    program_lang = data.get("program_lang")
    code = data.get("code")
    problem_id = data.get("problem_id")

    if not program_lang or not code or not problem_id:
        return jsonify({"message": "Missing required fields"}), 400

    new_submission = Submission(
        program_lang=program_lang,
        code=code,
        linked_user=current_user.id,
        problem_id=problem_id,
        status="PENDING",
        result="PENDING",
        result_time_ms=-1,
        result_memory_kb=-1,
        output_text="",
        error_text="",
    )

    db.session.add(new_submission)
    db.session.commit()

    return jsonify({"message": "Submission created successfully!"}), 201
