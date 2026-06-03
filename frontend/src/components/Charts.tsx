import {
  Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

const SEV_COLORS: Record<string, string> = {
  critical: "#dc2626", high: "#f43f5e", medium: "#f59e0b", low: "#0ea5e9", info: "#64748b",
};

export function SeverityPie({ data }: { data: { name: string; value: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" innerRadius={50} outerRadius={90}>
          {data.map((d) => (<Cell key={d.name} fill={SEV_COLORS[d.name] || "#94a3b8"} />))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
}

export function CategoryBars({ data }: { data: { category: string; score: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data}>
        <XAxis dataKey="category" />
        <YAxis domain={[0, 100]} />
        <Tooltip />
        <Bar dataKey="score" fill="#38bdf8" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
