import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';
import '../../styles/feedback/confirm.css';

type ConfirmVariant = 'danger' | 'default';

type ConfirmOptions = {
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
};

type ConfirmState = Required<ConfirmOptions>;

type ConfirmContextValue = {
  requestConfirm: (options: ConfirmOptions) => Promise<boolean>;
};

const ConfirmContext = createContext<ConfirmContextValue | null>(null);

const defaultConfirmOptions = {
  confirmLabel: '确定',
  cancelLabel: '取消',
  variant: 'default',
} satisfies Pick<ConfirmOptions, 'confirmLabel' | 'cancelLabel' | 'variant'>;

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);
  const resolverRef = useRef<((confirmed: boolean) => void) | null>(null);

  const closeConfirm = useCallback((confirmed: boolean) => {
    resolverRef.current?.(confirmed);
    resolverRef.current = null;
    setConfirmState(null);
  }, []);

  const requestConfirm = useCallback((options: ConfirmOptions) => (
    new Promise<boolean>((resolve) => {
      resolverRef.current?.(false);
      resolverRef.current = resolve;
      setConfirmState({
        ...defaultConfirmOptions,
        ...options,
      });
    })
  ), []);

  useEffect(() => {
    if (!confirmState) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        closeConfirm(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeConfirm, confirmState]);

  return (
    <ConfirmContext.Provider value={{ requestConfirm }}>
      {children}
      {confirmState && (
        <div className="confirm-backdrop" onMouseDown={() => closeConfirm(false)}>
          <section
            className={`confirm-dialog confirm-${confirmState.variant}`}
            onMouseDown={(event) => event.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="confirm-title"
            aria-describedby="confirm-message"
          >
            <div className="confirm-icon">
              <AlertTriangle size={20} />
            </div>
            <div className="confirm-copy">
              <h2 id="confirm-title">{confirmState.title}</h2>
              <p id="confirm-message">{confirmState.message}</p>
            </div>
            <div className="confirm-actions">
              <button className="confirm-cancel" onClick={() => closeConfirm(false)} type="button">
                {confirmState.cancelLabel}
              </button>
              <button className="confirm-submit" onClick={() => closeConfirm(true)} type="button">
                {confirmState.confirmLabel}
              </button>
            </div>
          </section>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const context = useContext(ConfirmContext);
  if (!context) {
    throw new Error('useConfirm must be used inside ConfirmProvider');
  }
  return context;
}
