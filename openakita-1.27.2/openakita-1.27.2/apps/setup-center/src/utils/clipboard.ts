/**
 * 跨平台复制到剪贴板（兼容 Win / Mac / Web / Desktop / 移动端）。
 * 优先使用 navigator.clipboard，不可用时回退到 document.execCommand('copy')。
 */
export async function copyToClipboard(text: string | null | undefined): Promise<boolean> {
  const s = text == null ? "" : String(text);
  if (s.length === 0) return false;

  try {
    if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(s);
      return true;
    }
  } catch {
    // 非安全上下文（非 HTTPS、部分 WebView）或权限被拒时可能失败，使用回退
  }

  // 回退：execCommand('copy')，适用于旧版浏览器、部分移动端、非 HTTPS 页面
  try {
    const textarea = document.createElement("textarea");
    textarea.value = s;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    textarea.style.top = "0";
    document.body.appendChild(textarea);

    const selection = window.getSelection();
    const range = document.createRange();
    range.selectNodeContents(textarea);
    selection?.removeAllRanges();
    selection?.addRange(range);

    const ok = document.execCommand("copy");
    selection?.removeAllRanges();
    document.body.removeChild(textarea);
    return ok;
  } catch {
    return false;
  }
}
