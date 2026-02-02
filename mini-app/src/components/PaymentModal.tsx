import { useEffect, useRef } from 'react';
import '../styles/PaymentModal.css';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  widgetParams: any;
  onSuccess?: () => void;
  onFail?: (reason: string) => void;
}

// Extend Window interface for CloudPayments widget
declare global {
  interface Window {
    cp: any;
  }
}

export function PaymentModal({ isOpen, onClose, widgetParams, onSuccess, onFail }: PaymentModalProps) {
  const scriptLoaded = useRef(false);

  useEffect(() => {
    // Load CloudPayments widget script
    if (!scriptLoaded.current) {
      const script = document.createElement('script');
      script.src = 'https://widget.cloudpayments.ru/bundles/cloudpayments.js';
      script.async = true;
      document.body.appendChild(script);
      scriptLoaded.current = true;
    }
  }, []);

  useEffect(() => {
    if (isOpen && widgetParams && window.cp) {
      // Open CloudPayments widget
      const widget = new window.cp.CloudPayments();
      
      const options = {
        ...widgetParams,
        onSuccess: (options: any) => {
          console.log('Payment success:', options);
          onSuccess?.();
          onClose();
        },
        onFail: (reason: string, options: any) => {
          console.log('Payment failed:', reason, options);
          onFail?.(reason);
          onClose();
        },
        onComplete: (paymentResult: any, options: any) => {
          console.log('Payment complete:', paymentResult, options);
          onClose();
        }
      };

      widget.pay('charge', options);
    }
  }, [isOpen, widgetParams, onSuccess, onFail, onClose]);

  if (!isOpen) {
    return null;
  }

  return (
    <div className="payment-modal-overlay" onClick={onClose}>
      <div className="payment-modal" onClick={(e) => e.stopPropagation()}>
        <button className="payment-modal__close" onClick={onClose}>
          ×
        </button>
        <div className="payment-modal__content">
          <p>Загрузка платежной формы...</p>
        </div>
      </div>
    </div>
  );
}
