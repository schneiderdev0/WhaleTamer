import axios from "axios";
import { useAuthStore } from "../store/auth";

export const api = axios.create({
  baseURL: "",
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  const hasAuthorizationHeader =
    typeof config.headers?.Authorization === "string" ||
    typeof config.headers?.authorization === "string";

  if (token && !hasAuthorizationHeader) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
