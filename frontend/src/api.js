export const sortTasksAPI = async (tasks) => {
  const response = await fetch("http://localhost:5000/sort-tasks", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ tasks }),
  });

  return response.json();
};