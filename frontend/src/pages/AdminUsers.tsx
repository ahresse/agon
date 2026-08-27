import { useEffect, useState } from "react";
import { createUser, listUsers, Role, updateUserRole, User } from "../services/apiClient";

/** Admin user-management page (US3, FR-014): create/list users and assign roles. */
export function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("REVIEWER");
  const [error, setError] = useState<string | null>(null);

  const load = () => listUsers().then(setUsers).catch((e) => setError((e as Error).message));
  useEffect(() => {
    load();
  }, []);

  const add = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await createUser(username, password, role);
      setUsername("");
      setPassword("");
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const changeRole = async (id: string, newRole: Role) => {
    setError(null);
    try {
      await updateUserRole(id, newRole);
      await load();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <section className="admin-users">
      <h2>User management</h2>
      {error && <p className="error">{error}</p>}
      <form onSubmit={add}>
        <input
          placeholder="username"
          aria-label="new-username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          type="password"
          placeholder="password"
          aria-label="new-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <select aria-label="new-role" value={role} onChange={(e) => setRole(e.target.value as Role)}>
          <option value="REVIEWER">REVIEWER</option>
          <option value="ADMIN">ADMIN</option>
        </select>
        <button type="submit">Create user</button>
      </form>
      <table>
        <thead>
          <tr>
            <th>Username</th>
            <th>Role</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.username}</td>
              <td>
                <select
                  aria-label={`role-${u.username}`}
                  value={u.role}
                  onChange={(e) => changeRole(u.id, e.target.value as Role)}
                >
                  <option value="REVIEWER">REVIEWER</option>
                  <option value="ADMIN">ADMIN</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
