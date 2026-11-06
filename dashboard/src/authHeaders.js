// Header for dashboard routes that need a login (usage and limits)
export const authHeaders = () => {
  const token = window.localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};
