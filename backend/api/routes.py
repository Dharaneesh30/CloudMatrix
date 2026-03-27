from flask import request, jsonify
import pandas as pd
import os

from app import app
from core.allocation import greedy_allocate

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.normpath(os.path.join(BASE_DIR, "..", "data"))
DATA_PATH = os.path.join(DATA_FOLDER, "tasks.csv")

os.makedirs(DATA_FOLDER, exist_ok=True)


@app.route("/upload-dataset", methods=["POST"])
def upload_dataset():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        file.save(DATA_PATH)
        file_size = os.path.getsize(DATA_PATH)
        return jsonify({
            "message": "File saved successfully",
            "saved_to": DATA_PATH,
            "size_bytes": file_size
        })
    except PermissionError:
        return jsonify({"error": "Permission denied – check folder permissions"}), 500
    except Exception as e:
        return jsonify({"error": f"Save failed: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running"}), 200

@app.route("/tasks", methods=["GET"])
def get_tasks():
    if not os.path.exists(DATA_PATH):
        return jsonify({"error": "No dataset found. Please upload a CSV first."}), 404

    try:
        df = pd.read_csv(DATA_PATH)
        return jsonify(df.to_dict(orient="records"))
    except Exception as e:
        return jsonify({"error": f"Error reading CSV: {str(e)}"}), 500

@app.route("/add-task", methods=["POST"])
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


def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])

    return merge(left, right)


def merge(left, right):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i]["priority"] < right[j]["priority"]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])
    return result


@app.route("/sort-tasks", methods=["GET"])
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

        return jsonify({
            "total": total,
            "page": page,
            "page_size": page_size,
            "tasks": page_df.to_dict(orient="records"),
        })
    except Exception as e:
        return jsonify({"error": f"Error sorting tasks: {str(e)}"}), 500

@app.route("/allocate-servers", methods=["GET"])
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

        # Greedy scheduling by descending priority
        result = greedy_allocate(df.to_dict(orient="records"))
        allocations = result["allocations"]
        unassigned = result["unassigned"]

        # Pagination on allocations list
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paged_allocations = allocations[start_index:end_index]

        return jsonify({
            "total": total,
            "page": page,
            "page_size": page_size,
            "allocations": paged_allocations,
            "unassigned": unassigned,
        })
    except Exception as e:
        return jsonify({"error": f"Error during allocation: {str(e)}"}), 500