// Header for dashboard routes that need a login
export const authHeaders = () => {
  const token = window.localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Forget the login in this browser (logout, or an expired or invalid token)
export const clearLogin = () => {
  window.localStorage.removeItem("email");
  window.localStorage.removeItem("token");
  window.localStorage.removeItem("admin");
};

// fetch with the login token; an expired or invalid login goes back to the login page
export const authFetch = async (url, options = {}) => {
  const response = await fetch(url, {
    ...options,
    headers: { ...(options.headers || {}), ...authHeaders() }
  });
  if (response.status === 401) {
    clearLogin();
    window.location.assign("/login");
  }
  return response;
};
