from flask import Blueprint, request, jsonify
import os
import sys
from pathlib import Path

import pandas as pd

try:
    from ..core.allocation import greedy_allocate
except ImportError:
    backend_root = Path(__file__).resolve().parents[1]
    backend_root_str = str(backend_root)
    if backend_root_str not in sys.path:
        sys.path.append(backend_root_str)
    from core.allocation import greedy_allocate


api_bp = Blueprint("api", __name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
DATA_PATH = os.path.join(DATA_FOLDER, "tasks.csv")

os.makedirs(DATA_FOLDER, exist_ok=True)


@api_bp.route("/upload-dataset", methods=["POST"])
def upload_dataset():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        file.save(DATA_PATH)
        file_size = os.path.getsize(DATA_PATH)
        return jsonify(
            {
                "message": "File saved successfully",
                "saved_to": DATA_PATH,
                "size_bytes": file_size,
            }
        )
    except PermissionError:
        return jsonify({"error": "Permission denied - check folder permissions"}), 500
    except Exception as e:
        return jsonify({"error": f"Save failed: {str(e)}"}), 500


@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200


@api_bp.route("/tasks", methods=["GET"])
def get_tasks():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No dataset found. Please upload a CSV first."}), 404

    try:
        df = pd.read_csv(DATA_PATH)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {str(e)}"}), 500


@api_bp.route("/add-task", methods=["POST"])
def add_task():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No dataset found. Upload CSV first."}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON"}), 400

    required = {"id", "priority"}
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields: id, priority"}), 400

    try:
        df = pd.read_csv(DATA_PATH)

        new_task = {
            "id": data["id"],
            "priority": data["priority"],
            "cpu_request": data.get("cpu_request", 1),
            "memory_request": data.get("memory_request", 1),
            "execution_time": data.get("execution_time", 1),
        }

        df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
        df.to_csv(DATA_PATH, index=False)

        return jsonify({"message": "Task added successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to add task: {str(e)}"}), 500


@api_bp.route("/sort-tasks", methods=["GET"])
def sort_tasks():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No dataset found"}), 404

    try:
        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=100, type=int)
        page = max(1, page)
        page_size = min(max(10, page_size), 500)

        df = pd.read_csv(DATA_PATH)
        total = len(df)

        df_sorted = df.sort_values(by="priority", ascending=True)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        page_df = df_sorted.iloc[start_index:end_index]

        return jsonify(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "tasks": page_df.to_dict(orient="records"),
            }
        )
    except Exception as e:
        return jsonify({"error": f"Error sorting tasks: {str(e)}"}), 500


@api_bp.route("/allocate-servers", methods=["GET"])
def allocate_servers():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No dataset found"}), 404

    try:
        page = request.args.get("page", default=1, type=int)
        page_size = request.args.get("page_size", default=100, type=int)
        page = max(1, page)
        page_size = min(max(10, page_size), 500)

        df = pd.read_csv(DATA_PATH)
        total = len(df)

        result = greedy_allocate(df.to_dict(orient="records"))
        allocations = result["allocations"]
        unassigned = result["unassigned"]

        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paged_allocations = allocations[start_index:end_index]

        return jsonify(
            {
                "total": total,
                "page": page,
                "page_size": page_size,
                "allocations": paged_allocations,
                "unassigned": unassigned,
            }
        )
    except Exception as e:
        return jsonify({"error": f"Error during allocation: {str(e)}"}), 500
