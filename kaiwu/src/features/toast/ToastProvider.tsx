import { createContext, useCallback, useContext, useMemo, useState, type ComponentType, type ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

import type { ShowToast, ToastInput, ToastVariant } from '../../types';
import '../../styles/feedback/toast.css';

type ToastItem = Required<Pick<ToastInput, 'message' | 'variant' | 'duration'>> & {
  id: number;
  title?: string;
};

type ToastContextValue = {
  showToast: ShowToast;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const variantIcon: Record<ToastVariant, ComponentType<{ size?: number }>> = {
  success: CheckCircle2,
  error: AlertCircle,
  info: Info,
};

let nextToastId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback<ShowToast>((toastInput) => {
    const normalized = typeof toastInput === 'string'
      ? { message: toastInput }
      : toastInput;
    const id = nextToastId++;
    const toast: ToastItem = {
      id,
      message: normalized.message,
      title: normalized.title,
      variant: normalized.variant || 'success',
      duration: normalized.duration ?? 2600,
    };

    setToasts((current) => [toast, ...current].slice(0, 4));
    window.setTimeout(() => dismissToast(id), toast.duration);
  }, [dismissToast]);

  const value = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-viewport" aria-live="polite" aria-atomic="true">
        <AnimatePresence initial={false}>
          {toasts.map((toast) => {
            const Icon = variantIcon[toast.variant];
            return (
              <motion.div
                key={toast.id}
                className={`toast-item toast-${toast.variant}`}
                initial={{ opacity: 0, y: -16, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.98 }}
                transition={{ duration: 0.18, ease: 'easeOut' }}
                role={toast.variant === 'error' ? 'alert' : 'status'}
              >
                <span className="toast-icon">
                  <Icon size={17} />
                </span>
                <span className="toast-copy">
                  {toast.title && <strong>{toast.title}</strong>}
                  <span>{toast.message}</span>
                </span>
                <button
                  className="toast-close"
                  onClick={() => dismissToast(toast.id)}
                  type="button"
                  aria-label="关闭提示"
                  title="关闭提示"
                >
                  <X size={14} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used inside ToastProvider');
  }
  return context;
}
