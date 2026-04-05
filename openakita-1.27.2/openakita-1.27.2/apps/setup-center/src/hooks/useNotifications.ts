import { useCallback, useState } from "react";

export function useNotifications() {
  const [confirmDialog, setConfirmDialog] = useState<{ message: string; onConfirm: () => void } | null>(null);

  const askConfirm = useCallback((message: string, onConfirm: () => void) => {
    setConfirmDialog({ message, onConfirm });
  }, []);

  return {
    confirmDialog, setConfirmDialog,
    askConfirm,
  };
}
