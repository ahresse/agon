import { useEffect, useState } from "react";
import { listTests, TestConfig, updateTestConfig } from "../services/apiClient";

/** Admin test-config page (US3, FR-008): enable/disable and set default weight. */
export function AdminConfig() {
  const [tests, setTests] = useState<TestConfig[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = () => listTests().then(setTests).catch((e) => setError((e as Error).message));
  useEffect(() => {
    load();
  }, []);

  const patch = async (id: string, p: { enabled?: boolean; default_weight?: number }) => {
    setError(null);
    try {
      await updateTestConfig(id, p);
      await load();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <section className="admin-config">
      <h2>Test configuration</h2>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Test</th>
            <th>Type</th>
            <th>Enabled</th>
            <th>Default weight</th>
          </tr>
        </thead>
        <tbody>
          {tests.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td>{t.type}</td>
              <td>
                <input
                  type="checkbox"
                  aria-label={`enabled-${t.name}`}
                  checked={t.enabled}
                  onChange={(e) => patch(t.id, { enabled: e.target.checked })}
                />
              </td>
              <td>
                <input
                  type="number"
                  min={0}
                  step={0.5}
                  aria-label={`weight-${t.name}`}
                  value={t.default_weight}
                  onChange={(e) => patch(t.id, { default_weight: Number(e.target.value) })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
