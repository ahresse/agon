import { FormEvent, useState } from "react";
import { login, Role } from "../services/apiClient";

export function Login({ onLoggedIn }: { onLoggedIn: (role?: Role) => void }) {
  const [username, setUsername] = useState("reviewer");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const user = await login(username, password);
      onLoggedIn(user.role);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form onSubmit={submit} className="login">
      <h1>Agon — Sign in</h1>
      <label>
        Username
        <input value={username} onChange={(e) => setUsername(e.target.value)} />
      </label>
      <label>
        Password
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit">Sign in</button>
    </form>
  );
}
