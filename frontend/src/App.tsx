import { useState } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes } from "react-router-dom";
import { Login } from "./pages/Login";
import { Upload } from "./pages/Upload";
import { ReviewDetail } from "./pages/ReviewDetail";
import { History } from "./pages/History";
import { AdminConfig } from "./pages/AdminConfig";
import { AdminUsers } from "./pages/AdminUsers";
import { Role } from "./services/apiClient";

export default function App() {
  const [role, setRole] = useState<Role | null>(null);

  if (!role) {
    return <Login onLoggedIn={(r) => setRole(r ?? "REVIEWER")} />;
  }

  const isAdmin = role === "ADMIN";
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Upload</Link>
        <Link to="/history">History</Link>
        {isAdmin && <Link to="/admin/tests">Test config</Link>}
        {isAdmin && <Link to="/admin/users">Users</Link>}
      </nav>
      <main>
        <Routes>
          <Route path="/" element={<Upload />} />
          <Route path="/history" element={<History />} />
          <Route path="/reviews/:reviewId" element={<ReviewDetail />} />
          {isAdmin && <Route path="/admin/tests" element={<AdminConfig />} />}
          {isAdmin && <Route path="/admin/users" element={<AdminUsers />} />}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
