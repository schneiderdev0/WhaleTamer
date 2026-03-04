import axios from "axios";
import { useCallback } from "react";
import { toast } from "react-toastify";

export function useAPI() {
  const getErrorMessage = useCallback((error: unknown, fallback: string) => {
    if (!error) {
      return fallback;
    }
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      if (typeof detail === "string" && detail.trim().length > 0) {
        return detail;
      }
    }
    if (error instanceof Error && typeof error.message === "string" && error.message.trim().length > 0) {
      return error.message;
    }
    return fallback;
  }, []);

  const notifyError = useCallback((error: unknown, fallback: string) => {
    toast.error(getErrorMessage(error, fallback));
  }, [getErrorMessage]);

  const notifySuccess = useCallback((message: string) => {
    toast.success(message);
  }, []);

  return { getErrorMessage, notifyError, notifySuccess };
}
