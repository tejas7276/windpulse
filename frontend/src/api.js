const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

export async function fetchDay(date, signal) {
  let response;
  try {
    response = await fetch(`${API_URL}/api/wind/day?date=${date}`, { signal });
  } catch (err) {
    if (err.name === "AbortError") throw err;
    throw new Error("Could not reach the WindPulse API. Check that the backend is running.");
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : null;
    throw new Error(detail || `The API returned an error (${response.status}).`);
  }
  return body;
}
