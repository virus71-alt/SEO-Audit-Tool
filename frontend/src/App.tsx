import { Link, Route, Routes, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import Overview from "./pages/Overview";
import Technical from "./pages/Technical";
import Content from "./pages/Content";
import Performance from "./pages/Performance";
import Links from "./pages/Links";
import Images from "./pages/Images";
import StructuredData from "./pages/StructuredData";
import Recommendations from "./pages/Recommendations";
import Login from "./pages/Login";

const NAV = [
  { to: "/", label: "Overview" },
  { to: "/technical", label: "Technical" },
  { to: "/content", label: "Content" },
  { to: "/performance", label: "Performance" },
  { to: "/links", label: "Links" },
  { to: "/images", label: "Images" },
  { to: "/schema", label: "Structured Data" },
  { to: "/recommendations", label: "Recommendations" },
];

export default function App() {
  const [dark, setDark] = useState(true);
  const navigate = useNavigate();
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);
  const token = localStorage.getItem("token");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <header className="border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex items-center gap-4 sticky top-0 z-10 bg-inherit">
        <Link to="/" className="font-bold text-lg">SEO Audit</Link>
        <nav className="flex gap-3 text-sm ml-4">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to} className="text-slate-500 hover:text-brand-500 transition">
              {n.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={() => setDark((d) => !d)}
            className="text-xs px-3 py-1 rounded-md border border-slate-300 dark:border-slate-700"
          >
            {dark ? "Light" : "Dark"}
          </button>
          {token ? (
            <button
              className="text-xs px-3 py-1 rounded-md bg-brand-600 text-white"
              onClick={() => {
                localStorage.removeItem("token");
                navigate("/login");
              }}
            >
              Logout
            </button>
          ) : (
            <Link to="/login" className="text-xs px-3 py-1 rounded-md bg-brand-600 text-white">
              Login
            </Link>
          )}
        </div>
      </header>
      <main className="p-6 max-w-7xl mx-auto">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/technical" element={<Technical />} />
          <Route path="/content" element={<Content />} />
          <Route path="/performance" element={<Performance />} />
          <Route path="/links" element={<Links />} />
          <Route path="/images" element={<Images />} />
          <Route path="/schema" element={<StructuredData />} />
          <Route path="/recommendations" element={<Recommendations />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </main>
    </div>
  );
}
