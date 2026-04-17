import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#ef5b36", "#35a57e", "#3d6ae0", "#e0a53d", "#1f8a9c"];
const MAX_SERVER_SLICES = 6;

function formatCount(value) {
  return Number(value || 0).toLocaleString();
}

export default function MetricsCharts({ priorityData = [], serverLoadData = [] }) {
  const normalizedServerLoadData = [...serverLoadData]
    .map((item) => ({
      server: item?.server || "Unknown",
      count: Number(item?.count || 0),
    }))
    .filter((item) => item.count > 0)
    .sort((a, b) => b.count - a.count);

  const visibleServerSlices = normalizedServerLoadData.slice(0, MAX_SERVER_SLICES);
  const otherServerCount = normalizedServerLoadData
    .slice(MAX_SERVER_SLICES)
    .reduce((sum, item) => sum + item.count, 0);
  const chartServerLoadData =
    otherServerCount > 0
      ? [...visibleServerSlices, { server: "Other", count: otherServerCount }]
      : visibleServerSlices;
  const totalServerLoad = chartServerLoadData.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="glass-card p-4 md:p-5">
        <h3 className="mb-3 font-display text-lg font-semibold">Task Priority Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={priorityData}>
              <CartesianGrid strokeDasharray="4 4" stroke="#0000001f" />
              <XAxis dataKey="band" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                {priorityData.map((_, idx) => (
                  <Cell key={`p-${idx}`} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-card p-4 md:p-5">
        <h3 className="mb-3 font-display text-lg font-semibold">Server Load Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartServerLoadData}
                dataKey="count"
                nameKey="server"
                innerRadius={52}
                outerRadius={92}
                paddingAngle={2}
                labelLine={false}
                label={({ name, percent }) => (percent >= 0.06 ? `${name} ${(percent * 100).toFixed(0)}%` : "")}
              >
                {chartServerLoadData.map((_, idx) => (
                  <Cell key={`s-${idx}`} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(value, _, entry) => [formatCount(value), entry?.payload?.server || "Server"]}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value, entry) => {
                  const count = entry?.payload?.payload?.count || 0;
                  const percent = totalServerLoad > 0 ? Math.round((count / totalServerLoad) * 100) : 0;
                  return `${value} (${formatCount(count)}, ${percent}%)`;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
