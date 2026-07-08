import { useState } from 'react';
import { motion } from 'framer-motion';
import { FEATURE_CARDS } from '../../data';
import '../../styles/home/feature-cards.css';

const FALLBACK_GRADIENTS = [
  'linear-gradient(135deg, #dbeafe, #bfdbfe)',
  'linear-gradient(135deg, #ffedd5, #fecdd3)',
  'linear-gradient(135deg, #f3e8ff, #e9d5ff)',
  'linear-gradient(135deg, #f1f5f9, #cbd5e1)',
  'linear-gradient(135deg, #fef3c7, #fde68a)',
  'linear-gradient(135deg, #ccfbf1, #a5f3fc)',
];

type FeatureCardsProps = {
  onCardClick: (title: string, imageUrl: string) => void;
};

function CardImage({ src, index }: { src: string; index: number }) {
  const [hasError, setHasError] = useState(false);

  if (hasError || !src) {
    return (
      <div className="feature-card-image" style={{ background: FALLBACK_GRADIENTS[index] }} />
    );
  }

  return (
    <div className="feature-card-image">
      <img src={src} alt="" className="feature-card-img" onError={() => setHasError(true)} />
    </div>
  );
}

export function FeatureCards({ onCardClick }: FeatureCardsProps) {
  return (
    <div className="feature-cards-grid">
      {FEATURE_CARDS.map((card, i) => (
        <motion.button
          key={card.id}
          className="feature-card"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
          whileHover={{ y: -2, transition: { duration: 0.2 } }}
          onClick={() => onCardClick(card.title, card.imageUrl)}
          type="button"
        >
          <CardImage src={card.imageUrl} index={i} />
          <span className="feature-card-order">{card.order}</span>
          <div className="feature-card-overlay">
            <span>{card.title}</span>
          </div>
        </motion.button>
      ))}
    </div>
  );
}
