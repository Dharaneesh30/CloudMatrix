import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 120000,
});

export const uploadDataset = async (file, scheduleType = "fast") => {
  const buildForm = (type) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("schedule_type", type);
    return formData;
  };

  try {
    const res = await api.post("/upload-dataset", buildForm(scheduleType));
    return res.data;
  } catch (err) {
    const detail = String(err?.response?.data?.detail || "");
    const unsupportedSchedule =
      scheduleType === "fast" &&
      detail.includes("Unsupported schedule_type");

    if (unsupportedSchedule) {
      const fallback = await api.post("/upload-dataset", buildForm("heap"));
      return {
        ...fallback.data,
        message: `${fallback.data?.message || "Dataset uploaded"} (fallback: heap)`,
      };
    }
    throw err;
  }
};

export const fetchStatus = async () => (await api.get("/status")).data;
export const fetchMetrics = async () =>
  (
    await api.get("/metrics", {
      timeout: 180000,
    })
  ).data;
export const fetchTasks = async (page = 1, limit = 50) =>
  (await api.get("/tasks", { params: { page, limit } })).data;
export const fetchTaskById = async (taskId) => (await api.get(`/task/${taskId}`)).data;
export const runSchedule = async (type, page = 1, limit = 50) =>
  (await api.post(`/schedule/${type}`, null, { params: { page, limit } })).data;
export const fetchServerBalance = async () => (await api.get("/server-balance")).data;
export const rebalanceUnassigned = async (
  autoScale = true,
  maxRows = 200000,
  batchSize = 25000
) =>
  (
    await api.post("/rebalance-unassigned", null, {
      params: {
        auto_scale: autoScale,
        max_rows: maxRows,
        batch_size: batchSize,
      },
      timeout: 180000,
    })
  ).data;
export const pingHealth = async () => (await api.get("/health")).data;

export default api;
