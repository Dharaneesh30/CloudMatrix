import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#ef5b36", "#35a57e", "#3d6ae0", "#e0a53d", "#8f55da"];

export default function MetricsCharts({ priorityData = [], serverLoadData = [] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="glass-card p-4">
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

      <div className="glass-card p-4">
        <h3 className="mb-3 font-display text-lg font-semibold">Server Load Distribution</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={serverLoadData} dataKey="count" nameKey="server" outerRadius={95} label>
                {serverLoadData.map((_, idx) => (
                  <Cell key={`s-${idx}`} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
