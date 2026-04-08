import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 120000,
});

export const uploadDataset = async (file, unusedServers = 3) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("unused_servers", String(unusedServers || 3));
  const res = await api.post("/upload-dataset", formData);
  return res.data;
};

export const fetchStatus = async () => (await api.get("/status")).data;
export const fetchMetrics = async (mode = "auto") =>
  (
    await api.get("/metrics", {
      params: { mode },
      timeout: 30000,
    })
  ).data;
export const fetchTasks = async (page = 1, limit = 50) =>
  (await api.get("/tasks", { params: { page, limit } })).data;
export const fetchUnassignedTasks = async (page = 1, limit = 50, includeTotal = false) =>
  (await api.get("/unassigned-tasks", { params: { page, limit, include_total: includeTotal } })).data;
export const fetchTaskById = async (taskId) => (await api.get(`/task/${taskId}`)).data;
export const runSchedule = async (type, page = 1, limit = 50) =>
  (
    await api.post(`/schedule/${type}`, null, {
      params: { page, limit },
      timeout: 600000,
    })
  ).data;
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
