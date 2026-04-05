import { toast } from "sonner";
import { copyToClipboard } from "./clipboard";

export function notifySuccess(msg: string) {
  toast.success(msg, { duration: 4000 });
}

export function notifyError(msg: string) {
  toast.error(msg, {
    duration: 8000,
    action: {
      label: "复制",
      onClick: () => copyToClipboard(msg),
    },
  });
}

export function notifyLoading(msg: string): string | number {
  return toast.loading(msg);
}

export function dismissLoading(id: string | number) {
  toast.dismiss(id);
}
